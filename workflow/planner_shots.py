"""Few-shot examples for the SPARQL planner. Each example teaches one query pattern."""

FAO_FILTER   = '"UN FAO", "UN FAO FRA", "UN FAO Kotka III", "UN FAO RAP", "UN ECEE/FAO"'
UNFCCC_FILTER= '"UN FCCC", "UN FCCC IPCC GPG", "IPCC Kyoto Protocol", "UNFCCC", "IPCC", "IPCC?"'
PREFIXES     = (
    "PREFIX : <http://example.org/forest#> "
    "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> "
    "PREFIX skos: <http://www.w3.org/2004/02/skos/core#> "
    "PREFIX dcterms: <http://purl.org/dc/terms/> "
    "PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>"
)

_DEF_BODY = (
    "SELECT ?jurisdiction ?year ?canopy ?height ?area ?text ?category WHERE {{ "
    "?d a :Definition{concept} ; :appliesIn ?jur ; :definitionText ?text . "
    "?jur rdfs:label ?jurisdiction .{filter} "
    "OPTIONAL {{ ?d <http://purl.org/dc/terms/date> ?year }} "
    "OPTIONAL {{ ?d :canopyThreshold ?canopy }} "
    "OPTIONAL {{ ?d :heightMin ?height }} "
    "OPTIONAL {{ ?d :areaMin ?area }} "
    "OPTIONAL {{ ?d :hasCategory ?cat . ?cat rdfs:label ?category }} "
    "}} ORDER BY ?jurisdiction LIMIT {limit}}}"
)


def _def(concept="", filter_clause="", limit=15):
    c = f" ; :defines :{concept}" if concept else ""
    f = f" {filter_clause}" if filter_clause else ""
    return f"{PREFIXES} {_DEF_BODY.format(concept=c, filter=f, limit=limit)}"


FEW_SHOT_EXAMPLES = f"""
Q: "Qu'est ce qu'une forêt ?"
{{"intent": "definitional", "sparql": "PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> SELECT ?jurisdiction ?year ?canopy ?height ?area ?text ?category WHERE {{ ?d a :Definition ; :defines :Forest ; :appliesIn ?jur ; :definitionText ?text ; :hasJurisdictionLevel ?lvl . ?jur rdfs:label ?jurisdiction . ?lvl rdfs:label ?level . FILTER(?level IN (\\"General\\", \\"International\\")) OPTIONAL {{ ?d <http://purl.org/dc/terms/date> ?year }} OPTIONAL {{ ?d :canopyThreshold ?canopy }} OPTIONAL {{ ?d :heightMin ?height }} OPTIONAL {{ ?d :areaMin ?area }} OPTIONAL {{ ?d :hasCategory ?cat . ?cat rdfs:label ?category }} }} ORDER BY ?jurisdiction LIMIT 20"}}

Q: "What is the FAO definition of forest?"
{{"intent": "definitional", "sparql": "PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> SELECT ?jurisdiction ?year ?canopy ?height ?area ?text ?category WHERE {{ ?d a :Definition ; :appliesIn ?jur ; :definitionText ?text . ?jur rdfs:label ?jurisdiction . FILTER(?jurisdiction IN ({FAO_FILTER})) OPTIONAL {{ ?d <http://purl.org/dc/terms/date> ?year }} OPTIONAL {{ ?d :canopyThreshold ?canopy }} OPTIONAL {{ ?d :heightMin ?height }} OPTIONAL {{ ?d :areaMin ?area }} OPTIONAL {{ ?d :hasCategory ?cat . ?cat rdfs:label ?category }} }} ORDER BY ?jurisdiction LIMIT 15"}}

Q: "How does UNFCCC define forest?"
{{"intent": "definitional", "sparql": "PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> SELECT ?jurisdiction ?year ?canopy ?height ?area ?text ?category WHERE {{ ?d a :Definition ; :appliesIn ?jur ; :definitionText ?text . ?jur rdfs:label ?jurisdiction . FILTER(?jurisdiction IN ({UNFCCC_FILTER})) OPTIONAL {{ ?d <http://purl.org/dc/terms/date> ?year }} OPTIONAL {{ ?d :canopyThreshold ?canopy }} OPTIONAL {{ ?d :heightMin ?height }} OPTIONAL {{ ?d :areaMin ?area }} OPTIONAL {{ ?d :hasCategory ?cat . ?cat rdfs:label ?category }} }} ORDER BY ?jurisdiction LIMIT 15"}}

Q: "What is the forest definition in Albania?"
{{"intent": "definitional", "sparql": "PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> SELECT ?jurisdiction ?year ?canopy ?height ?area ?text ?category WHERE {{ ?d a :Definition ; :appliesIn ?jur ; :definitionText ?text . ?jur rdfs:label ?jurisdiction . FILTER(LCASE(?jurisdiction) = \\"albania\\") OPTIONAL {{ ?d <http://purl.org/dc/terms/date> ?year }} OPTIONAL {{ ?d :canopyThreshold ?canopy }} OPTIONAL {{ ?d :heightMin ?height }} OPTIONAL {{ ?d :areaMin ?area }} OPTIONAL {{ ?d :hasCategory ?cat . ?cat rdfs:label ?category }} }} ORDER BY ?jurisdiction LIMIT 15"}}

Q: "Qu'est-ce que l'afforestation au sens de l'UNFCCC ?"
{{"intent": "definitional", "sparql": "PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> SELECT ?jurisdiction ?year ?canopy ?height ?area ?text ?category WHERE {{ ?d a :Definition ; :defines :Afforestation ; :appliesIn ?jur ; :definitionText ?text . ?jur rdfs:label ?jurisdiction . FILTER(?jurisdiction IN ({UNFCCC_FILTER})) OPTIONAL {{ ?d <http://purl.org/dc/terms/date> ?year }} OPTIONAL {{ ?d :canopyThreshold ?canopy }} OPTIONAL {{ ?d :heightMin ?height }} OPTIONAL {{ ?d :areaMin ?area }} OPTIONAL {{ ?d :hasCategory ?cat . ?cat rdfs:label ?category }} }} ORDER BY ?jurisdiction LIMIT 15"}}

Q: "Qu'est-ce que l'afforestation au sens de la FAO ?"
{{"intent": "definitional", "sparql": "PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> SELECT ?jurisdiction ?year ?canopy ?height ?area ?text ?category WHERE {{ ?d a :Definition ; :defines :Afforestation ; :appliesIn ?jur ; :definitionText ?text . ?jur rdfs:label ?jurisdiction . FILTER(?jurisdiction IN ({FAO_FILTER})) OPTIONAL {{ ?d <http://purl.org/dc/terms/date> ?year }} OPTIONAL {{ ?d :canopyThreshold ?canopy }} OPTIONAL {{ ?d :heightMin ?height }} OPTIONAL {{ ?d :areaMin ?area }} OPTIONAL {{ ?d :hasCategory ?cat . ?cat rdfs:label ?category }} }} ORDER BY ?jurisdiction LIMIT 15"}}

Q: "How do countries define deforestation?"
{{"intent": "definitional", "sparql": "PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> SELECT ?jurisdiction ?year ?canopy ?height ?area ?text ?category WHERE {{ ?d a :Definition ; :defines :Deforestation ; :appliesIn ?jur ; :definitionText ?text . ?jur rdfs:label ?jurisdiction . OPTIONAL {{ ?d <http://purl.org/dc/terms/date> ?year }} OPTIONAL {{ ?d :canopyThreshold ?canopy }} OPTIONAL {{ ?d :heightMin ?height }} OPTIONAL {{ ?d :areaMin ?area }} OPTIONAL {{ ?d :hasCategory ?cat . ?cat rdfs:label ?category }} }} ORDER BY ?jurisdiction LIMIT 15"}}

Q: "Est ce qu'une plantation forestière est une forêt au sens de l'UNFCCC ?"
{{"intent": "boolean_reasoning", "sparql": "PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> SELECT ?jurisdiction ?year ?canopy ?height ?area ?text ?category WHERE {{ ?d a :Definition ; :appliesIn ?jur ; :definitionText ?text . ?jur rdfs:label ?jurisdiction . FILTER(?jurisdiction IN ({UNFCCC_FILTER}) || CONTAINS(LCASE(?text), \\"plantation\\") || CONTAINS(LCASE(?text), \\"planted stand\\")) OPTIONAL {{ ?d <http://purl.org/dc/terms/date> ?year }} OPTIONAL {{ ?d :canopyThreshold ?canopy }} OPTIONAL {{ ?d :heightMin ?height }} OPTIONAL {{ ?d :areaMin ?area }} OPTIONAL {{ ?d :hasCategory ?cat . ?cat rdfs:label ?category }} }} ORDER BY ?jurisdiction LIMIT 15"}}

Q: "Quelle est la différence entre forestation, reforestation et afforestation ?"
{{"intent": "comparative", "sparql": "PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> SELECT ?concept ?jurisdiction ?year ?text ?category WHERE {{ ?d a :Definition ; :defines ?concept ; :appliesIn ?jur ; :definitionText ?text . ?jur rdfs:label ?jurisdiction . FILTER(?concept IN (:Afforestation, :Reforestation, :Deforestation)) OPTIONAL {{ ?d <http://purl.org/dc/terms/date> ?year }} OPTIONAL {{ ?d :hasCategory ?cat . ?cat rdfs:label ?category }} }} ORDER BY ?concept ?jurisdiction LIMIT 20"}}

Q: "Qu'est-ce que la forestation ?"
{{"intent": "comparative", "sparql": "PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> SELECT ?concept ?jurisdiction ?year ?text ?category WHERE {{ ?d a :Definition ; :defines ?concept ; :appliesIn ?jur ; :definitionText ?text . ?jur rdfs:label ?jurisdiction . FILTER(?concept IN (:Afforestation, :Reforestation)) OPTIONAL {{ ?d <http://purl.org/dc/terms/date> ?year }} OPTIONAL {{ ?d :hasCategory ?cat . ?cat rdfs:label ?category }} }} ORDER BY ?concept ?jurisdiction LIMIT 20"}}

Q: "What are the global trends in how countries define forests?"
{{"intent": "synthesis", "sparql": "PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> SELECT ?category (COUNT(?d) AS ?count) WHERE {{ ?d a :Definition ; :defines :Forest . OPTIONAL {{ ?d :hasCategory ?cat . ?cat rdfs:label ?category }} }} GROUP BY ?category ORDER BY DESC(?count)"}}

Q: "What is a structural definition of forest?"
{{"intent": "typological", "keyword": "structural", "sparql": "PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> SELECT ?jurisdiction ?year ?canopy ?height ?area ?text ?category WHERE {{ ?d a :Definition ; :appliesIn ?jur ; :definitionText ?text . ?jur rdfs:label ?jurisdiction . FILTER(CONTAINS(LCASE(?text), \\"crown cover\\") || CONTAINS(LCASE(?text), \\"canopy\\") || CONTAINS(LCASE(?text), \\"height\\") || CONTAINS(LCASE(?text), \\"hectare\\")) OPTIONAL {{ ?d <http://purl.org/dc/terms/date> ?year }} OPTIONAL {{ ?d :canopyThreshold ?canopy }} OPTIONAL {{ ?d :heightMin ?height }} OPTIONAL {{ ?d :areaMin ?area }} OPTIONAL {{ ?d :hasCategory ?cat . ?cat rdfs:label ?category }} }} ORDER BY ?jurisdiction LIMIT 15"}}

Q: "What is a systemic definition of forest?"
{{"intent": "typological", "keyword": "systemic", "sparql": "PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> SELECT ?jurisdiction ?year ?canopy ?height ?area ?text ?category WHERE {{ ?d a :Definition ; :appliesIn ?jur ; :definitionText ?text . ?jur rdfs:label ?jurisdiction . FILTER(CONTAINS(LCASE(?text), \\"ecosystem\\") || CONTAINS(LCASE(?text), \\"functional unit\\") || CONTAINS(LCASE(?text), \\"ecological\\") || CONTAINS(LCASE(?text), \\"dynamic complex\\")) OPTIONAL {{ ?d <http://purl.org/dc/terms/date> ?year }} OPTIONAL {{ ?d :canopyThreshold ?canopy }} OPTIONAL {{ ?d :heightMin ?height }} OPTIONAL {{ ?d :areaMin ?area }} OPTIONAL {{ ?d :hasCategory ?cat . ?cat rdfs:label ?category }} }} ORDER BY ?jurisdiction LIMIT 15"}}

Q: "Qu'est ce qu'un arbre ?"
{{"intent": "typological", "keyword": "tree"}}

Q: "Quelles sont les principales différences entre forêt primaire et forêt naturellement régénérée ?"
{{"intent": "typological", "keyword": "primary_vs_regenerated"}}

Q: "Quelles sont les principales différences entre plantation forestière et forêt naturellement régénérée ?"
{{"intent": "typological", "keyword": "plantation_vs_regenerated"}}

Q: "Est ce qu'une forêt urbaine est une forêt ?"
{{"intent": "typological", "keyword": "urban"}}

Q: "Est ce qu'une agroforêt est une forêt ?"
{{"intent": "typological", "keyword": "agroforest"}}

Q: "Est ce qu'une plantation monospécifique est une forêt ?"
{{"intent": "typological", "keyword": "plantation"}}

Q: "En quoi l'usage du sol (land use) peut être d'intérêt quand on cherche à caractériser la forêt ?"
{{"intent": "conceptual", "keyword": "LandUse"}}

Q: "En quoi la couverture du sol (land cover) peut être d'intérêt quand on cherche à caractériser la forêt ?"
{{"intent": "conceptual", "keyword": "LandCover"}}

Q: "Est ce que je peux définir une forêt à partir des services écosystémiques ?"
{{"intent": "conceptual", "keyword": "ecosystem_services"}}

Q: "Quel est le rôle de la forestation dans les stratégies Net Zéro des États ?"
{{"intent": "not_in_corpus"}}

Q: "Qu'est-ce que le mécanisme REDD+ et quel est son lien avec la forestation ?"
{{"intent": "not_in_corpus"}}

Q: "Comment les NDC intègrent-ils des objectifs de forestation ?"
{{"intent": "not_in_corpus"}}

Q: "Quelle est la différence entre déforestation et dégradation des forêts ?"
{{"intent": "definitional", "sparql": "PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> SELECT ?jurisdiction ?year ?canopy ?height ?area ?text ?category WHERE {{ ?d a :Definition ; :defines :Deforestation ; :appliesIn ?jur ; :definitionText ?text . ?jur rdfs:label ?jurisdiction . OPTIONAL {{ ?d <http://purl.org/dc/terms/date> ?year }} OPTIONAL {{ ?d :canopyThreshold ?canopy }} OPTIONAL {{ ?d :heightMin ?height }} OPTIONAL {{ ?d :areaMin ?area }} OPTIONAL {{ ?d :hasCategory ?cat . ?cat rdfs:label ?category }} }} ORDER BY ?jurisdiction LIMIT 15"}}
"""
