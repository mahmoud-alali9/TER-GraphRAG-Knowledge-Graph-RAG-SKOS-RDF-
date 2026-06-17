from SPARQLWrapper import SPARQLWrapper, JSON, SPARQLExceptions


def execute_sparql(endpoint, query):
    sparql = SPARQLWrapper(endpoint)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    try:
        results = sparql.query().convert()
        return results["results"]["bindings"], None
    except Exception as e:
        return [], str(e)
