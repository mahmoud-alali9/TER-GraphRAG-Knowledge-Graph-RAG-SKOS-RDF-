"""MCP server for Forest GraphRAG.

Exposes the knowledge graph and the pipeline as tools that any MCP client
(Claude Desktop, Claude Code, Cursor, an agent...) can call:

- ask_forest_question : full GraphRAG pipeline (LLM + SPARQL), sourced answer
- search_definitions  : dense / BM25 / hybrid search over the 2 553 definitions
- run_sparql          : read-only SPARQL on the graph
- list_jurisdictions  : find the exact labels of countries and organizations

Run:
    python mcp_server.py                      # stdio transport (for Claude Desktop / Claude Code)
    mcp dev mcp_server.py                     # MCP Inspector, to test the tools in a browser

The graph backend comes from SPARQL_ENDPOINT (Fuseki URL) or "local" (default:
reads data/schema.ttl, no Fuseki needed). ask_forest_question also needs an LLM
key (GROQ_API_KEY, or TOGETHER_API_KEY with LLM_BACKEND=together).
"""
from __future__ import annotations

import os
import re
import sys
from functools import lru_cache
from pathlib import Path
from typing import Literal

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)  # MCP clients start the server from any folder

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

try:  # MCP Python SDK v2
    from mcp.server.mcpserver import MCPServer as FastMCP  # noqa: E402
except ImportError:  # MCP Python SDK v1
    from mcp.server.fastmcp import FastMCP  # noqa: E402

from graph.sparql_executor import execute_sparql  # noqa: E402

ENDPOINT = os.getenv("SPARQL_ENDPOINT", "local")
MAX_ROWS = 50
_PROLOGUE = re.compile(r"^\s*(?:#[^\n]*\n|PREFIX\s+\S*\s*<[^>]*>|BASE\s*<[^>]*>)", re.IGNORECASE)


def _is_read_only(query: str) -> bool:
    """True if the query, after its PREFIX/BASE prologue, is a SELECT or ASK."""
    body = query
    while (match := _PROLOGUE.match(body)):
        body = body[match.end():]
    return re.match(r"\s*(SELECT|ASK)\b", body, re.IGNORECASE) is not None

mcp = FastMCP(
    name="forest-graphrag",
    instructions=(
        "Tools over a knowledge graph of 2 553 legal definitions of forest, tree, "
        "afforestation... from 497 countries and organizations (Lund 2018 corpus). "
        "Prefer ask_forest_question for user questions. Use list_jurisdictions to get "
        "exact labels before writing SPARQL filters."
    ),
)


@lru_cache(maxsize=1)
def _pipeline():
    from workflow.config import WorkflowConfig
    from workflow.pipeline import ForestGraphRAGPipeline

    return ForestGraphRAGPipeline(
        config=WorkflowConfig(endpoint=ENDPOINT, output_dir=Path("outputs"), timeout=120)
    )


@lru_cache(maxsize=1)
def _retrievers():
    from vector.index import build_retrievers

    return build_retrievers(ENDPOINT)


@mcp.tool()
async def ask_forest_question(question: str, mode: Literal["technical", "friendly"] = "technical") -> dict:
    """Answer a question about forest definitions with the GraphRAG pipeline.

    The answer only uses definitions retrieved from the knowledge graph. Returns the
    answer, the detected intent, the SPARQL query used and the retrieved context
    (the sources). If the information is not in the corpus, the answer says so.
    """
    result = await _pipeline().aquery(question, mode=mode)
    return {k: result[k] for k in ("answer", "intent", "sparql_query", "context")}


@mcp.tool()
def search_definitions(
    query: str,
    method: Literal["hybrid", "dense", "bm25"] = "hybrid",
    k: int = 5,
) -> list[dict]:
    """Semantic / keyword search over the definitions (no LLM call).

    method: "dense" (FAISS embeddings), "bm25" (keywords) or "hybrid" (both, fused
    with Reciprocal Rank Fusion). Each result has the definition text, its
    jurisdiction, concept, source URL and score.
    """
    k = max(1, min(k, 20))
    return [hit.to_dict() for hit in _retrievers()[method].search(query, k=k)]


@mcp.tool()
def run_sparql(query: str) -> dict:
    """Run a read-only SPARQL SELECT or ASK query on the knowledge graph.

    Prefixes: ":" = <http://example.org/forest#>, rdfs, skos. Main classes:
    :Definition (:definitionText, :defines, :appliesIn, :hasCategory,
    :canopyThreshold, :heightMin, :areaMin, :sourceRef), :Jurisdiction (rdfs:label).
    Results are capped at 50 rows. Update queries are refused.
    """
    if not _is_read_only(query):
        return {"error": "Only read-only SELECT / ASK queries are allowed.", "rows": []}
    bindings, error = execute_sparql(ENDPOINT, query)
    if error:
        return {"error": error, "rows": []}
    rows = [{var: cell["value"] for var, cell in b.items()} for b in bindings[:MAX_ROWS]]
    return {"error": None, "row_count": len(bindings), "rows": rows, "truncated": len(bindings) > MAX_ROWS}


@mcp.tool()
def list_jurisdictions(contains: str = "") -> list[str]:
    """List the exact jurisdiction labels of the graph (countries, organizations).

    contains: optional case-insensitive filter, e.g. "fao", "fccc", "brazil".
    """
    from graph.label_loader import fetch_all_labels

    labels = sorted(fetch_all_labels(ENDPOINT, "Jurisdiction"))
    if contains:
        labels = [label for label in labels if contains.lower() in label.lower()]
    return labels[:200]


if __name__ == "__main__":
    mcp.run()
