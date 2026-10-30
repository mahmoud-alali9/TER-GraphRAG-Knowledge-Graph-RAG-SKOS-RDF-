"""Dense (FAISS), sparse (BM25) and hybrid (RRF) retrieval over the definitions.

These retrievers are the classic RAG baselines we compare GraphRAG against.

    retrievers = build_retrievers()           # builds or loads the FAISS index
    hits = retrievers["hybrid"].search("forêt selon l'UNFCCC", k=5)
"""
from __future__ import annotations

import json
import os
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from vector.corpus import DefinitionDoc, load_definitions

# Multilingual model: questions are in French, definitions mostly in English.
DEFAULT_MODEL = os.getenv(
    "EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
DEFAULT_STORE = Path(os.getenv("VECTOR_STORE_DIR", "vector_store"))
RRF_K = 60  # standard constant of Reciprocal Rank Fusion


@dataclass(frozen=True)
class SearchHit:
    doc: DefinitionDoc
    score: float
    rank: int
    method: str

    def to_dict(self) -> dict:
        return {
            "rank": self.rank,
            "score": round(float(self.score), 4),
            "method": self.method,
            **self.doc.to_dict(),
        }


# ── Sparse: BM25 ────────────────────────────────────────────────────────────

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    """Lowercase, strip accents, keep alphanumeric tokens."""
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return _TOKEN_RE.findall(text)


class BM25Index:
    name = "bm25"

    def __init__(self, docs: list[DefinitionDoc]):
        from rank_bm25 import BM25Okapi

        self.docs = docs
        self._bm25 = BM25Okapi([tokenize(d.indexed_text) for d in docs])

    def scores(self, query: str) -> np.ndarray:
        return np.asarray(self._bm25.get_scores(tokenize(query)), dtype="float32")

    def search(self, query: str, k: int = 5) -> list[SearchHit]:
        scores = self.scores(query)
        top = np.argsort(-scores)[:k]
        return [SearchHit(self.docs[i], float(scores[i]), r + 1, self.name) for r, i in enumerate(top)]


# ── Dense: sentence embeddings + FAISS ──────────────────────────────────────

class DenseIndex:
    name = "dense"

    def __init__(self, docs: list[DefinitionDoc], model_name: str = DEFAULT_MODEL,
                 store_dir: Path = DEFAULT_STORE):
        self.docs = docs
        self.model_name = model_name
        self.store_dir = Path(store_dir)
        self._model = None
        self._index = None

    @property
    def model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        return self._model

    def _embed(self, texts: list[str]) -> np.ndarray:
        vectors = self.model.encode(
            texts, batch_size=64, normalize_embeddings=True, show_progress_bar=False
        )
        return np.asarray(vectors, dtype="float32")

    def _meta(self) -> dict:
        return {"model": self.model_name, "ids": [d.id for d in self.docs]}

    def build(self) -> "DenseIndex":
        import faiss

        vectors = self._embed([d.indexed_text for d in self.docs])
        index = faiss.IndexFlatIP(vectors.shape[1])  # inner product = cosine (normalized)
        index.add(vectors)
        self._index = index
        self.store_dir.mkdir(parents=True, exist_ok=True)
        faiss.write_index(index, str(self.store_dir / "definitions.faiss"))
        (self.store_dir / "meta.json").write_text(json.dumps(self._meta()), encoding="utf-8")
        return self

    def load_or_build(self) -> "DenseIndex":
        import faiss

        index_path = self.store_dir / "definitions.faiss"
        meta_path = self.store_dir / "meta.json"
        if index_path.exists() and meta_path.exists():
            if json.loads(meta_path.read_text(encoding="utf-8")) == self._meta():
                self._index = faiss.read_index(str(index_path))
                return self
        return self.build()  # missing or stale (other model / corpus changed)

    def search(self, query: str, k: int = 5) -> list[SearchHit]:
        if self._index is None:
            self.load_or_build()
        scores, ids = self._index.search(self._embed([query]), k)
        return [
            SearchHit(self.docs[i], float(s), r + 1, self.name)
            for r, (i, s) in enumerate(zip(ids[0], scores[0]))
            if i >= 0
        ]


# ── Hybrid: Reciprocal Rank Fusion of dense + BM25 ──────────────────────────

class HybridRetriever:
    """score(d) = sum over retrievers of 1 / (RRF_K + rank(d)).

    RRF only uses ranks, so the very different score scales of BM25 and
    cosine similarity do not need to be calibrated.
    """
    name = "hybrid"

    def __init__(self, dense: DenseIndex, bm25: BM25Index, depth: int = 50):
        self.dense = dense
        self.bm25 = bm25
        self.depth = depth

    def search(self, query: str, k: int = 5) -> list[SearchHit]:
        fused: dict[str, float] = {}
        docs: dict[str, DefinitionDoc] = {}
        for retriever in (self.dense, self.bm25):
            for hit in retriever.search(query, k=self.depth):
                fused[hit.doc.id] = fused.get(hit.doc.id, 0.0) + 1.0 / (RRF_K + hit.rank)
                docs[hit.doc.id] = hit.doc
        ranked = sorted(fused.items(), key=lambda item: item[1], reverse=True)[:k]
        return [SearchHit(docs[doc_id], score, r + 1, self.name) for r, (doc_id, score) in enumerate(ranked)]


def build_retrievers(endpoint: str = "local", model_name: str = DEFAULT_MODEL,
                     store_dir: Path = DEFAULT_STORE) -> dict:
    """Load the corpus once and return {"dense", "bm25", "hybrid"} retrievers."""
    docs = load_definitions(endpoint)
    dense = DenseIndex(docs, model_name=model_name, store_dir=store_dir).load_or_build()
    bm25 = BM25Index(docs)
    return {"dense": dense, "bm25": bm25, "hybrid": HybridRetriever(dense, bm25)}
