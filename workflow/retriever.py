from graph.sparql_executor import execute_sparql
from workflow.context_formatter import format_results
from workflow.planner import fix_query

FALLBACK_DEFINITIONS = """
PREFIX : <http://example.org/forest#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dcterms: <http://purl.org/dc/terms/>
SELECT ?jurisdiction ?year ?canopy ?height ?area ?text ?category
WHERE {{
    ?d a :Definition ; :appliesIn ?jur ; :definitionText ?text .
    ?jur rdfs:label ?jurisdiction .
    {filter_clause}
    OPTIONAL {{ ?d dcterms:date ?year }}
    OPTIONAL {{ ?d :canopyThreshold ?canopy }}
    OPTIONAL {{ ?d :heightMin ?height }}
    OPTIONAL {{ ?d :areaMin ?area }}
    OPTIONAL {{ ?d :hasCategory ?cat . ?cat rdfs:label ?category }}
}}
ORDER BY ?jurisdiction
LIMIT 20
"""

SYNTH_BY_CATEGORY = """
PREFIX : <http://example.org/forest#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?category (COUNT(?d) AS ?count) WHERE {
    ?d a :Definition ; :defines :Forest .
    OPTIONAL { ?d :hasCategory ?cat . ?cat rdfs:label ?category }
} GROUP BY ?category ORDER BY DESC(?count)
"""

SYNTH_BY_CANOPY = """
PREFIX : <http://example.org/forest#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT ?canopy (COUNT(?d) AS ?count) WHERE {
    ?d a :Definition ; :defines :Forest ; :canopyThreshold ?canopy .
} GROUP BY ?canopy ORDER BY DESC(?count) LIMIT 10
"""

TYPOLOGICAL_KEYWORDS = {
    "systemic":    ["ecosystem", "functional unit", "ecological", "dynamic complex", "living organism", "biotic"],
    "structural":  ["crown cover", "canopy", "height", "area", "hectare", "crown closure", "basal area"],
    "ecological":  ["ecological", "ecosystem", "biodiversity", "habitat", "species", "fauna", "flora"],
    "primary":     ["primary forest", "old growth", "virgin", "undisturbed", "native species", "climax", "intact forest"],
    "regenerated": ["naturally regenerat", "natural regenerat", "secondary", "natural regrowth", "naturally grown", "spontaneous regenerat"],
    "plantation":  ["plantation", "planted stand", "planted forest", "kyoto forest", "reforestation", "afforestation", "monoculture", "planted trees"],
    "agroforest":  ["agroforest", "agroforestry", "small holder", "smallholder", "agro-forest", "trees outside"],
    "urban":       ["urban", "city", "park", "garden", "peri-urban", "street tree", "municipal"],
}

# Org keyword → exact KG jurisdiction labels (change c: jurisdiction-priority scoring)
JURISDICTION_PRIORITY = {
    "fao":    ["UN FAO", "UN FAO FRA", "UN FAO FRA draft Tree land", "UN FAO Kotka III", "UN FAO RAP", "UN ECEE/FAO"],
    "unfccc": ["UN FCCC", "UN FCCC IPCC GPG", "IPCC Kyoto Protocol", "UNFCCC", "IPCC", "IPCC?"],
    "fccc":   ["UN FCCC", "UN FCCC IPCC GPG", "IPCC Kyoto Protocol", "UNFCCC", "IPCC"],
    "kyoto":  ["IPCC Kyoto Protocol", "UN FCCC", "IPCC", "IPCC?"],
    "eu":     ["EU", "EU Copenicus", "EU JRC", "EUROSTAT", "European Community", "European Environment Agency"],
    "unep":   ["UN EP", "UN EP EAP AP", "UN EP GRID", "UN EP/CBD"],
    "ipcc":   ["IPCC Kyoto Protocol"],
    "cbd":    ["UN CBD", "UN EP/CBD"],
}

CONCEPTUAL_SPARQL = """
PREFIX : <http://example.org/forest#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dcterms: <http://purl.org/dc/terms/>
SELECT ?jurisdiction ?year ?canopy ?height ?area ?text ?category
WHERE {{
    ?d a :Definition ; :appliesIn ?jur ; :definitionText ?text .
    ?jur rdfs:label ?jurisdiction .
    ?d :hasCategory ?cat . ?cat rdfs:label ?category .
    FILTER(LCASE(?category) = "{category_lc}")
    OPTIONAL {{ ?d dcterms:date ?year }}
    OPTIONAL {{ ?d :canopyThreshold ?canopy }}
    OPTIONAL {{ ?d :heightMin ?height }}
    OPTIONAL {{ ?d :areaMin ?area }}
}}
ORDER BY ?jurisdiction
LIMIT 20
"""

# Fetch :Tree concept definitions directly
TREE_CONCEPT_SPARQL = """
PREFIX : <http://example.org/forest#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dcterms: <http://purl.org/dc/terms/>
SELECT ?jurisdiction ?year ?canopy ?height ?area ?text ?category
WHERE {
    ?d a :Definition ; :defines :Tree ; :definitionText ?text ; :appliesIn ?jur .
    ?jur rdfs:label ?jurisdiction .
    OPTIONAL { ?d dcterms:date ?year }
    OPTIONAL { ?d :canopyThreshold ?canopy }
    OPTIONAL { ?d :heightMin ?height }
    OPTIONAL { ?d :areaMin ?area }
    OPTIONAL { ?d :hasCategory ?cat . ?cat rdfs:label ?category }
}
ORDER BY ?jurisdiction
LIMIT 15
"""

# Kyoto Forest / plantation-under-UNFCCC query
KYOTO_FOREST_SPARQL = """
PREFIX : <http://example.org/forest#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dcterms: <http://purl.org/dc/terms/>
SELECT ?jurisdiction ?year ?canopy ?height ?area ?text ?category
WHERE {
    ?d a :Definition ; :definitionText ?text ; :appliesIn ?jur .
    ?jur rdfs:label ?jurisdiction .
    FILTER(CONTAINS(LCASE(?text), "planted stand") || CONTAINS(LCASE(?text), "planted forest")
        || CONTAINS(LCASE(?text), "plantation") || CONTAINS(LCASE(?text), "afforestation")
        || CONTAINS(LCASE(?text), "reforestation"))
    FILTER(?jurisdiction IN ("UN FCCC", "UN FCCC IPCC GPG", "IPCC Kyoto Protocol",
                             "UN FAO", "UN FAO FRA", "UN FAO FRA draft Tree land"))
    OPTIONAL { ?d dcterms:date ?year }
    OPTIONAL { ?d :canopyThreshold ?canopy }
    OPTIONAL { ?d :heightMin ?height }
    OPTIONAL { ?d :areaMin ?area }
    OPTIONAL { ?d :hasCategory ?cat . ?cat rdfs:label ?category }
}
ORDER BY ?jurisdiction ?year
LIMIT 15
"""

# AFF + FAO 1958 systemic definitions
AFF_SYSTEMIC_SPARQL = """
PREFIX : <http://example.org/forest#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dcterms: <http://purl.org/dc/terms/>
SELECT ?jurisdiction ?year ?canopy ?height ?area ?text ?category
WHERE {
    ?d a :Definition ; :definitionText ?text ; :appliesIn ?jur .
    ?jur rdfs:label ?jurisdiction .
    FILTER(?jurisdiction IN ("AFF", "UN FAO FRA", "UN FAO")
        || CONTAINS(LCASE(?text), "functional unit")
        || CONTAINS(LCASE(?text), "dynamic complex")
        || CONTAINS(LCASE(?text), "ecosystem"))
    OPTIONAL { ?d dcterms:date ?year }
    OPTIONAL { ?d :canopyThreshold ?canopy }
    OPTIONAL { ?d :heightMin ?height }
    OPTIONAL { ?d :areaMin ?area }
    OPTIONAL { ?d :hasCategory ?cat . ?cat rdfs:label ?category }
}
ORDER BY ?jurisdiction ?year
LIMIT 15
"""

TYPOLOGICAL_SPARQL = """
PREFIX : <http://example.org/forest#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dcterms: <http://purl.org/dc/terms/>
SELECT ?jurisdiction ?year ?canopy ?height ?area ?text ?category
WHERE {{
    ?d a :Definition ; :appliesIn ?jur ; :definitionText ?text .
    ?jur rdfs:label ?jurisdiction .
    FILTER({filter_clause})
    OPTIONAL {{ ?d dcterms:date ?year }}
    OPTIONAL {{ ?d :canopyThreshold ?canopy }}
    OPTIONAL {{ ?d :heightMin ?height }}
    OPTIONAL {{ ?d :areaMin ?area }}
    OPTIONAL {{ ?d :hasCategory ?cat . ?cat rdfs:label ?category }}
}}
ORDER BY ?jurisdiction
LIMIT 15
"""


def _run_synthesis(endpoint):
    sections = []

    cat_b, _ = execute_sparql(endpoint, SYNTH_BY_CATEGORY)
    if cat_b:
        lines = [f"  {r.get('category', {}).get('value', 'Unknown')}: {r['count']['value']}" for r in cat_b]
        sections.append("Definitions by Category:\n" + "\n".join(lines))

    can_b, _ = execute_sparql(endpoint, SYNTH_BY_CANOPY)
    if can_b:
        low, mid, high = 0, 0, 0
        for r in can_b:
            try:
                val = float(r['canopy']['value'])
                cnt = int(r['count']['value'])
                if val <= 10.0: low += cnt
                elif val <= 30.0: mid += cnt
                else: high += cnt
            except Exception:
                pass
        sections.append(
            f"Canopy Threshold Distribution:\n"
            f"  <=10%: {low} countries\n"
            f"  11-30%: {mid} countries\n"
            f"  >30%: {high} countries"
        )

    return "\n\n".join(sections) if sections else None


def _rerank_by_relevance(bindings, question, top_k=5):
    """Rank rows by jurisdiction priority, recency, then keyword overlap."""
    question_lc = question.lower()

    priority_labels = set()
    for keyword, labels in JURISDICTION_PRIORITY.items():
        if keyword in question_lc:
            priority_labels.update(labels)

    # Prefer recent FAO definitions (2005 is the canonical one)
    preferred_years = {"2005", "2006", "2010", "2013", "2015"}

    def score(row):
        jur  = row.get("jurisdiction", {}).get("value", "")
        year = str(row.get("year", {}).get("value", ""))
        text = row.get("text", {}).get("value", "").lower()
        priority = 100 if jur in priority_labels else 0
        recency  = 10  if year in preferred_years else 0
        words    = set(question_lc.split())
        overlap  = sum(1 for w in words if len(w) > 3 and w in text)
        return priority + recency + overlap

    ranked = sorted(bindings, key=score, reverse=True)
    return ranked[:top_k]


def _run_conceptual(endpoint, keyword):
    """Fetch all definitions for a given category (LandUse, LandCover, Ecological)."""
    # Map keyword → exact KG rdfs:label (case-sensitive in the graph)
    category_map = {
        "landuse":            "LandUse",
        "land_use":           "LandUse",
        "LandUse":            "LandUse",
        "landcover":          "LandCover",
        "land_cover":         "LandCover",
        "LandCover":          "LandCover",
        "ecological":         "Ecological",
        "Ecological":         "Ecological",
        "ecosystem_services": "Ecological",
    }
    category_exact = category_map.get(keyword, category_map.get(keyword.lower(), "LandCover"))
    # Use exact match (not LCASE) because KG labels are TitleCase
    query = """
PREFIX : <http://example.org/forest#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dcterms: <http://purl.org/dc/terms/>
SELECT ?jurisdiction ?year ?canopy ?height ?area ?text ?category
WHERE {{
    ?d a :Definition ; :appliesIn ?jur ; :definitionText ?text .
    ?jur rdfs:label ?jurisdiction .
    ?d :hasCategory ?cat . ?cat rdfs:label ?category .
    FILTER(?category = "{category}")
    OPTIONAL {{ ?d dcterms:date ?year }}
    OPTIONAL {{ ?d :canopyThreshold ?canopy }}
    OPTIONAL {{ ?d :heightMin ?height }}
    OPTIONAL {{ ?d :areaMin ?area }}
}}
ORDER BY ?jurisdiction
LIMIT 20
""".format(category=category_exact)
    bindings, error = execute_sparql(endpoint, query)
    if bindings:
        return format_results(bindings, "definitional")
    return None


def _run_tree_concept(endpoint):
    """Fetch definitions for the :Tree concept directly."""
    bindings, _ = execute_sparql(endpoint, TREE_CONCEPT_SPARQL)
    if bindings:
        return format_results(bindings, "definitional")
    return None


def _run_kyoto_plantation(endpoint):
    """Fetch plantation/Kyoto Forest definitions from UNFCCC/FAO sources."""
    bindings, _ = execute_sparql(endpoint, KYOTO_FOREST_SPARQL)
    if bindings:
        return format_results(bindings, "definitional")
    return None


def _run_typological(endpoint, keyword):
    """Build and execute a CONTAINS-based SPARQL query for typological intents."""
    # Special case: tree concept — use :defines :Tree directly
    if keyword == "tree":
        return _run_tree_concept(endpoint)

    # Special case: systemic — augment with AFF/FAO 1958 jurisdiction lookup
    if keyword == "systemic":
        bindings, _ = execute_sparql(endpoint, AFF_SYSTEMIC_SPARQL)
        if bindings:
            return format_results(bindings, "definitional")

    # Special case: plantation — also search Kyoto/UNFCCC sources
    if keyword == "plantation":
        ctx = _run_kyoto_plantation(endpoint)
        if ctx:
            return ctx

    # Special case: comparative keywords — run both types and merge
    COMPARATIVE_PAIRS = {
        "primary_vs_regenerated": ("primary", "regenerated"),
        "plantation_vs_regenerated": ("plantation", "regenerated"),
    }
    if keyword in COMPARATIVE_PAIRS:
        t1, t2 = COMPARATIVE_PAIRS[keyword]
        results = []
        for t in (t1, t2):
            terms = TYPOLOGICAL_KEYWORDS.get(t, [])
            if terms:
                clauses = " || ".join(f'CONTAINS(LCASE(?text), "{t}")' for t in terms)
                b, _ = execute_sparql(endpoint, TYPOLOGICAL_SPARQL.format(filter_clause=clauses))
                if b:
                    results.extend(b[:8])
        if results:
            return format_results(results, "definitional")
        return None

    terms = TYPOLOGICAL_KEYWORDS.get(keyword, [])
    if not terms:
        return None

    clauses = " || ".join(
        f'CONTAINS(LCASE(?text), "{t}")'
        for t in terms
    )
    query = TYPOLOGICAL_SPARQL.format(filter_clause=clauses)
    bindings, error = execute_sparql(endpoint, query)
    if bindings:
        return format_results(bindings, "definitional")
    return None


def retrieve(endpoint, plan, fallback_jurisdictions=None):
    """Returns (context_or_None, intent, executed_sparql)."""
    intent = plan.get("intent", "definitional")
    sparql = plan.get("sparql")

    # Not in corpus — short-circuit immediately
    if intent == "not_in_corpus":
        return None, intent, ""

    # Conceptual questions (land use/cover role, ecosystem services)
    if intent == "conceptual":
        keyword = plan.get("keyword", "")
        context = _run_conceptual(endpoint, keyword)
        if context:
            return context, intent, ""
        return None, intent, ""

    # Handle typological intents directly via keyword search
    if intent == "typological":
        keyword = plan.get("keyword", "")
        context = _run_typological(endpoint, keyword)
        if context:
            return context, intent, sparql or ""
        return None, intent, sparql or ""

    if sparql:
        executed = sparql
        bindings, error = execute_sparql(endpoint, sparql)

        if error or (not bindings and intent != "synthesis"):
            reason = error if error else "Query returned 0 results. Might be too restrictive or have wrong casing."
            fixed_sparql = fix_query(sparql, reason, intent)
            if fixed_sparql:
                executed = fixed_sparql
                bindings, error = execute_sparql(endpoint, fixed_sparql)

        if bindings:
            if intent in ("definitional", "boolean_reasoning"):
                question = plan.get("_question", "")
                bindings = _rerank_by_relevance(bindings, question)
                # For plantation+UNFCCC boolean questions, also inject Kyoto context
                q_lc = question.lower()
                if intent == "boolean_reasoning" and "plantation" in q_lc and any(k in q_lc for k in ("unfccc", "fccc", "kyoto")):
                    kyoto_b, _ = execute_sparql(endpoint, KYOTO_FOREST_SPARQL)
                    if kyoto_b:
                        bindings = kyoto_b[:5] + bindings
            return format_results(bindings, intent), intent, executed

    if intent == "synthesis":
        context = _run_synthesis(endpoint)
        if context:
            return context, intent, sparql or ""

    if fallback_jurisdictions:
        jur_filter = " || ".join(
            [f'LCASE(?jurisdiction) = "{j.lower()}"' for j in fallback_jurisdictions]
        )
        query = FALLBACK_DEFINITIONS.format(filter_clause=f"FILTER({jur_filter})")
        bindings, error = execute_sparql(endpoint, query)
        if bindings:
            bindings = _rerank_by_relevance(bindings, "")
            return format_results(bindings, "definitional"), "definitional", query

    # No broad no-filter fallback — return None to trigger not-in-corpus gate
    return None, intent, sparql or ""
