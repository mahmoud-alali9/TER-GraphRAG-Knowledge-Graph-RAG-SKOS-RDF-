from SPARQLWrapper import SPARQLWrapper, JSON


def fetch_all_labels(endpoint, rdf_type):
    sparql = SPARQLWrapper(endpoint)

    if rdf_type == "skos:Concept":
        sparql.setQuery("""
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            SELECT ?label WHERE { ?s a skos:Concept ; skos:prefLabel ?label . }
        """)
    else:
        sparql.setQuery(f"""
            PREFIX : <http://example.org/forest#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT ?label WHERE {{ ?s a :{rdf_type} ; rdfs:label ?label . }}
        """)

    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    return [r["label"]["value"] for r in results["results"]["bindings"]]


def load_all_labels(endpoint):
    return {
        "jurisdictions": fetch_all_labels(endpoint, "Jurisdiction"),
        "categories": fetch_all_labels(endpoint, "InterpretationCategory"),
        "levels": fetch_all_labels(endpoint, "JurisdictionLevel"),
        "concepts": fetch_all_labels(endpoint, "skos:Concept"),
    }
