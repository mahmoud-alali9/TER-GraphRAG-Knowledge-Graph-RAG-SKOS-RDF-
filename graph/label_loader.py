from graph.sparql_executor import execute_sparql

CONCEPT_QUERY = """
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    SELECT ?label WHERE { ?s a skos:Concept ; skos:prefLabel ?label . }
"""

TYPED_LABEL_QUERY = """
    PREFIX : <http://example.org/forest#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?label WHERE {{ ?s a :{rdf_type} ; rdfs:label ?label . }}
"""


def fetch_all_labels(endpoint, rdf_type):
    if rdf_type == "skos:Concept":
        query = CONCEPT_QUERY
    else:
        query = TYPED_LABEL_QUERY.format(rdf_type=rdf_type)

    bindings, error = execute_sparql(endpoint, query)
    if error:
        raise RuntimeError(f"Could not load {rdf_type} labels: {error}")
    return [r["label"]["value"] for r in bindings]


def load_all_labels(endpoint):
    return {
        "jurisdictions": fetch_all_labels(endpoint, "Jurisdiction"),
        "categories": fetch_all_labels(endpoint, "InterpretationCategory"),
        "levels": fetch_all_labels(endpoint, "JurisdictionLevel"),
        "concepts": fetch_all_labels(endpoint, "skos:Concept"),
    }
