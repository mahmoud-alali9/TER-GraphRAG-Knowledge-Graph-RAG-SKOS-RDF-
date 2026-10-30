"""Load the definitions of the knowledge graph as flat documents for vector search."""
from __future__ import annotations

from dataclasses import asdict, dataclass

from graph.sparql_executor import execute_sparql

DEFINITIONS_QUERY = """
PREFIX :     <http://example.org/forest#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?def ?text ?concept ?jurisdiction ?source WHERE {
    ?def a :Definition ;
         :definitionText ?text ;
         :defines ?conceptNode .
    BIND(STRAFTER(STR(?conceptNode), "#") AS ?concept)
    OPTIONAL { ?def :appliesIn ?j . ?j rdfs:label ?jurisdiction . }
    OPTIONAL { ?def :sourceRef ?source . }
}
"""


@dataclass(frozen=True)
class DefinitionDoc:
    id: str
    text: str
    concept: str
    jurisdiction: str
    source: str

    @property
    def indexed_text(self) -> str:
        """Text given to the retrievers: the jurisdiction is part of the chunk,
        as it would be in a standard RAG over the original documents."""
        return f"{self.jurisdiction} ({self.concept}): {self.text}"

    def to_dict(self) -> dict:
        return asdict(self)


def load_definitions(endpoint: str = "local") -> list[DefinitionDoc]:
    """Return every definition of the graph, sorted by id (stable order for the index)."""
    bindings, error = execute_sparql(endpoint, DEFINITIONS_QUERY)
    if error:
        raise RuntimeError(f"Could not load definitions: {error}")

    docs: dict[str, DefinitionDoc] = {}
    for b in bindings:
        def_id = b["def"]["value"].split("#")[-1]
        if def_id in docs:  # a definition may have several jurisdictions: keep the first
            continue
        docs[def_id] = DefinitionDoc(
            id=def_id,
            text=b["text"]["value"],
            concept=b.get("concept", {}).get("value", ""),
            jurisdiction=b.get("jurisdiction", {}).get("value", "Unknown"),
            source=b.get("source", {}).get("value", ""),
        )
    return [docs[k] for k in sorted(docs)]
