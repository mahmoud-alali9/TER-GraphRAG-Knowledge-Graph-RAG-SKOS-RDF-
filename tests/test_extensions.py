"""Tests for the local SPARQL backend, the vector retrievers and the MCP tools.

Run: python -m pytest tests -q
They use the local Turtle file and a tiny fake embedding model, so they need
neither Fuseki, nor an LLM key, nor a model download.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from graph.label_loader import load_all_labels  # noqa: E402
from graph.sparql_executor import execute_sparql  # noqa: E402
from vector.corpus import load_definitions  # noqa: E402
from vector.index import BM25Index, DenseIndex, HybridRetriever, tokenize  # noqa: E402
from workflow.nerd_linking import find_jurisdiction  # noqa: E402


class FakeEncoder:
    """Hashing bag-of-words encoder standing in for sentence-transformers."""

    def encode(self, texts, batch_size=64, normalize_embeddings=True, show_progress_bar=False):
        vectors = np.zeros((len(texts), 256), dtype="float32")
        for row, text in enumerate(texts):
            for token in tokenize(text):
                vectors[row, hash(token) % 256] += 1.0
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        return vectors / np.maximum(norms, 1e-9)


@pytest.fixture(scope="module")
def docs():
    return load_definitions("local")


@pytest.fixture(scope="module")
def retrievers(docs, tmp_path_factory):
    dense = DenseIndex(docs, model_name="fake", store_dir=tmp_path_factory.mktemp("store"))
    dense._model = FakeEncoder()
    dense.build()
    bm25 = BM25Index(docs)
    return {"dense": dense, "bm25": bm25, "hybrid": HybridRetriever(dense, bm25)}


def test_local_backend_counts_definitions():
    rows, error = execute_sparql("local", """
        PREFIX : <http://example.org/forest#>
        SELECT (COUNT(?d) AS ?n) WHERE { ?d a :Definition }""")
    assert error is None
    assert int(rows[0]["n"]["value"]) == 2553


def test_local_backend_reports_errors():
    rows, error = execute_sparql("local", "SELECT WHERE broken")
    assert rows == [] and error


def test_labels_and_entity_linking():
    labels = load_all_labels("local")
    assert len(labels["jurisdictions"]) > 400
    linked = find_jurisdiction("Qu'est ce qu'une forêt au sens de l'UNFCCC ?", labels["jurisdictions"], "local")
    assert "UN FCCC" in linked


def test_corpus(docs):
    assert len(docs) == 2553
    assert len({d.id for d in docs}) == len(docs)
    assert all(d.text for d in docs)


@pytest.mark.parametrize("method", ["dense", "bm25", "hybrid"])
def test_retrievers_return_ranked_hits(retrievers, method):
    hits = retrievers[method].search("forest definition FAO canopy cover 10 percent", k=5)
    assert [h.rank for h in hits] == [1, 2, 3, 4, 5]
    scores = [h.score for h in hits]
    assert scores == sorted(scores, reverse=True)


def test_dense_index_is_reloaded_from_disk(docs, retrievers):
    store = retrievers["dense"].store_dir
    reloaded = DenseIndex(docs, model_name="fake", store_dir=store)
    reloaded._model = FakeEncoder()
    reloaded.load_or_build()
    assert reloaded._index.ntotal == len(docs)


def test_mcp_tools(monkeypatch, retrievers):
    import mcp_server

    monkeypatch.setattr(mcp_server, "_retrievers", lambda: retrievers)
    assert "UN FCCC" in mcp_server.list_jurisdictions("fccc")

    hits = mcp_server.search_definitions("Ghana forest", method="bm25", k=3)
    assert len(hits) == 3 and {"jurisdiction", "text", "score"} <= hits[0].keys()

    ok = mcp_server.run_sparql("PREFIX : <http://example.org/forest#>\nSELECT ?d WHERE { ?d a :Definition } LIMIT 3")
    assert ok["error"] is None and len(ok["rows"]) == 3

    refused = mcp_server.run_sparql("DELETE WHERE { ?s ?p ?o }")
    assert refused["error"] and refused["rows"] == []

    # a SELECT whose text merely contains an update keyword is still allowed
    allowed = mcp_server.run_sparql(
        'PREFIX : <http://example.org/forest#>\nSELECT ?t WHERE { ?d :definitionText ?t FILTER(CONTAINS(?t, "delete")) } LIMIT 1'
    )
    assert allowed["error"] is None


def test_mcp_server_lists_tools():
    import mcp_server

    tools = asyncio.run(mcp_server.mcp.list_tools())
    names = {t.name for t in tools}
    assert names == {"ask_forest_question", "search_definitions", "run_sparql", "list_jurisdictions"}
