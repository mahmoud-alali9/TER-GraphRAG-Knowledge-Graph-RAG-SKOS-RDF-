"""Execute SPARQL queries against Fuseki, or locally against the Turtle file.

Two backends:
- Fuseki (default): ``endpoint`` is an HTTP URL such as http://localhost:3030/forestKG/sparql
- Local: ``endpoint == "local"`` (or env ``SPARQL_BACKEND=local``). The graph is
  loaded once from ``data/schema.ttl`` with rdflib. Handy for demos, tests and the
  MCP server when Fuseki is not running. Fuseki stays the reference backend.

Both backends return results in the SPARQL JSON "bindings" format, so callers
do not need to know which backend answered.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

LOCAL_ENDPOINT = "local"
DEFAULT_TTL = Path(__file__).resolve().parent.parent / "data" / "schema.ttl"


def is_local(endpoint: str | None) -> bool:
    if os.getenv("SPARQL_BACKEND", "").lower() == LOCAL_ENDPOINT:
        return True
    return endpoint is None or endpoint == LOCAL_ENDPOINT


@lru_cache(maxsize=2)
def load_local_graph(ttl_path: str | None = None):
    """Parse the knowledge graph once and keep it in memory."""
    from rdflib import Graph

    graph = Graph()
    graph.parse(ttl_path or os.getenv("TTL_PATH", str(DEFAULT_TTL)), format="turtle")
    return graph


def _term_to_binding(term) -> dict:
    from rdflib import BNode, Literal, URIRef

    if isinstance(term, URIRef):
        return {"type": "uri", "value": str(term)}
    if isinstance(term, BNode):
        return {"type": "bnode", "value": str(term)}
    binding = {"type": "literal", "value": str(term)}
    if isinstance(term, Literal):
        if term.datatype is not None:
            binding["datatype"] = str(term.datatype)
        if term.language:
            binding["xml:lang"] = term.language
    return binding


def _execute_local(query: str):
    result = load_local_graph().query(query)
    if result.type == "ASK":
        return [{"ask": {"type": "literal", "value": str(bool(result.askAnswer)).lower()}}]
    bindings = []
    for row in result:
        values = row.asdict()
        bindings.append({var: _term_to_binding(val) for var, val in values.items() if val is not None})
    return bindings


def _execute_remote(endpoint: str, query: str):
    from SPARQLWrapper import JSON, SPARQLWrapper

    sparql = SPARQLWrapper(endpoint)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    return results["results"]["bindings"]


def execute_sparql(endpoint, query):
    """Run a SELECT/ASK query. Returns ``(bindings, error_message_or_None)``."""
    try:
        if is_local(endpoint):
            return _execute_local(query), None
        return _execute_remote(endpoint, query), None
    except Exception as e:
        return [], str(e)
