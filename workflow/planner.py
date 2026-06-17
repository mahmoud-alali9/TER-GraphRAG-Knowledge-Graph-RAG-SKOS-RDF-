import re
import json
from workflow.groq_client import ask_llm
from workflow.planner_shots import FEW_SHOT_EXAMPLES

JURISDICTION_MAP = {
    "FAO":    ["UN FAO", "UN FAO FRA", "UN FAO FRA draft Tree land", "UN FAO Kotka III", "UN FAO RAP", "UN ECEE/FAO"],
    "UNFCCC": ["UN FCCC", "UN FCCC IPCC GPG", "IPCC Kyoto Protocol", "UNFCCC", "IPCC", "IPCC?"],
    "KP":     ["UN FCCC", "IPCC Kyoto Protocol", "UNFCCC", "IPCC"],
    "EU":     ["EU", "EU Copenicus", "EU JRC", "EUROSTAT", "European Community", "European Community DGXIII", "European Environment Agency"],
    "UNEP":   ["UN EP", "UN EP EAP AP", "UN EP GRID", "UN EP/CBD", "UN EP/EAP.AP"],
    "CBD":    ["UN CBD", "UN EP/CBD"],
    "IPCC":   ["IPCC Kyoto Protocol"],
    "EUDR":   [],
}

GRAPH_SCHEMA = """
Classes: Definition, Jurisdiction, JurisdictionLevel, InterpretationCategory, skos:Concept
Concepts: :Forest, :Tree, :Afforestation, :Deforestation, :Reforestation
JurisdictionLevels: :General, :International, :National, :Local
Categories: :Administrative, :LandCover, :LandUse, :Ecological

Properties on :Definition:
  :defines → skos:Concept
  :appliesIn → :Jurisdiction (rdfs:label = country name)
  :hasJurisdictionLevel → :JurisdictionLevel
  :hasCategory → :InterpretationCategory (rdfs:label = category name)
  :canopyThreshold → xsd:decimal  :heightMin → xsd:decimal  :areaMin → xsd:decimal
  :definitionText → string  :sourceRef → string  dcterms:date → xsd:gYear

Numeric values stored as "10.0"^^xsd:decimal — cast with xsd:float(?var) for filtering.
Prefixes (include ALL):
  PREFIX : <http://example.org/forest#>
  PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
  PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
  PREFIX dcterms: <http://purl.org/dc/terms/>
  PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
"""

SYSTEM_PROMPT = f"""You are a SPARQL query planner for a forest definitions knowledge graph.

GRAPH SCHEMA:
{GRAPH_SCHEMA}

EXAMPLES:
{FEW_SHOT_EXAMPLES}

RULES:
- Output ONLY valid JSON: {{"intent":"...","sparql":"..."}}
- intent options: definitional, comparative, synthesis, filtering, alignment, boolean_reasoning, typological, conceptual, not_in_corpus
- Typological intent: also include "keyword" field (systemic, structural, ecological, primary, regenerated, plantation, agroforest, urban, tree, primary_vs_regenerated, plantation_vs_regenerated)
- Conceptual intent: also include "keyword" field (LandUse, LandCover, Ecological, ecosystem_services). No sparql needed.
- Generic forest with NO org/country: use :hasJurisdictionLevel FILTER(?level IN ("General","International")) LIMIT 20
- "forestation" alone (no re/af prefix) = comparative with FILTER(?concept IN (:Afforestation,:Reforestation))
- afforestation/deforestation/reforestation: always include :defines :Concept in WHERE clause
- When jurisdiction IS resolved AND question is about afforestation/deforestation/reforestation: include BOTH :defines AND jurisdiction FILTER
- Boolean question with NO jurisdiction: use typological intent, keyword = subject type (urban, agroforest, plantation, primary…)
- Write SPARQL on a SINGLE LINE — no newlines inside the query string
- Translate country/concept names to English before writing SPARQL FILTER
- LIMIT 15 for definitional/comparative. No LIMIT for filtering intent.
- No markdown, no explanation — ONLY the JSON

JURISDICTION MATCHING RULES:
- Countries: FILTER(LCASE(?jurisdiction) = "english_name_lowercase")
- FAO: FILTER(?jurisdiction IN ("UN FAO","UN FAO FRA","UN FAO Kotka III","UN FAO RAP","UN ECEE/FAO"))
- UNFCCC/KP: FILTER(?jurisdiction IN ("UN FCCC","UN FCCC IPCC GPG","IPCC Kyoto Protocol","UNFCCC","IPCC","IPCC?"))
- EU: FILTER(?jurisdiction IN ("EU","EU Copenicus","EU JRC","EUROSTAT","European Community","European Environment Agency"))
- UNEP: FILTER(?jurisdiction IN ("UN EP","UN EP EAP AP","UN EP GRID","UN EP/CBD"))
- EUDR: NOT IN CORPUS → output {{"intent":"not_in_corpus"}}
- not_in_corpus triggers: EUDR, AFR100, Bonn Challenge, REDD+, NDC, COP21, Accord de Paris, Net Zéro, engagements internationaux forestation
"""


def _normalize_json(raw: str) -> str:
    """Collapse literal newlines/tabs inside JSON string values so json.loads works."""
    def _collapse(m):
        return '"' + ' '.join(m.group(1).split()) + '"'
    return re.sub(r'"((?:[^"\\]|\\.)*)"', _collapse, raw, flags=re.DOTALL)


def plan_query(question, labels=None, resolved_jurisdictions=None):
    prompt = f'Generate the SPARQL plan for:\n"{question}"'
    if resolved_jurisdictions:
        prompt += f"\n\nResolved jurisdictions (use EXACT labels): {', '.join(resolved_jurisdictions)}"
    if labels:
        jur_sample = ", ".join(labels.get("jurisdictions", [])[:30])
        prompt += f"\n\nAvailable jurisdictions (sample): {jur_sample}"

    raw = ask_llm(prompt, system=SYSTEM_PROMPT, temperature=0.0).strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]

    raw = _normalize_json(raw)
    try:
        plan = json.loads(raw)
        if isinstance(plan.get("sparql"), str):
            plan["sparql"] = " ".join(plan["sparql"].split())
        return plan
    except json.JSONDecodeError:
        return {"intent": "definitional", "sparql": None}


def fix_query(failed_query, error_message, intent):
    prompt = (
        f"The following SPARQL query failed or returned 0 results.\n"
        f"Intent: {intent}\nQuery: {failed_query}\nError: {error_message}\n\n"
        f"Provide a FIXED query. Output ONLY: {{\"intent\":\"{intent}\",\"sparql\":\"...\"}}"
    )
    raw = ask_llm(prompt, system=SYSTEM_PROMPT, temperature=0.0).strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
    try:
        return json.loads(raw).get("sparql")
    except Exception:
        return None
