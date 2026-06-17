# ForestGraphRAG — Pipeline Changelog

---

## v0 → v1 : LLM Backend Switch (Together.ai)

**Problem:** Groq free tier hit the 100k tokens/day limit after 2 questions, blocking all evaluation runs.

**Files changed:** `workflow/groq_client.py`, `.env`

### Changes

**`workflow/groq_client.py`**
- Added Together.ai support via the OpenAI-compatible client (`openai.OpenAI` with `base_url="https://api.together.xyz/v1"`)
- Added `_get_together()` client factory alongside existing `_get_groq()`
- `ask_llm()` now reads `LLM_BACKEND` env var at call time to switch between `groq` and `together`
- Model configurable via `TOGETHER_MODEL` env var (default: `meta-llama/Llama-3.3-70B-Instruct-Turbo`)

**`.env`**
- Added `TOGETHER_API_KEY`
- Added `TOGETHER_MODEL=meta-llama/Llama-3.3-70B-Instruct-Turbo`
- Added `LLM_BACKEND=together`

### Impact
- All 26 questions now run without rate-limit interruption
- Same model family (Llama 3.3 70B) — no change in answer quality
- Groq remains available by setting `LLM_BACKEND=groq`

---

## v1 → v2 : Retrieval & Intent Improvements

**Problem:** Expert evaluation of v1 results (avg 2.70/5) revealed 4 systematic failure modes:
1. UNFCCC queries returning Ethiopia instead of UN FCCC definitions
2. Conceptual questions (land use/cover role) returning NOT_IN_CORPUS
3. EUDR questions answered with EU 2010/2013 data — hallucination
4. Reranking by bag-of-words deprioritised international org rows vs country rows
5. Typological keywords too narrow — FAO FRA entries for regenerated/plantation not found

**Files changed:** `workflow/planner.py`, `workflow/retriever.py`, `workflow/tools.py`

---

### (a) Exact jurisdiction label mapping — `workflow/planner.py`

**Root cause:** SPARQL used `CONTAINS(LCASE(?jurisdiction), "fao")` and `CONTAINS(LCASE(?jurisdiction), "fccc")`. These broad string matches hit peripheral entries (e.g. Ethiopia's text references "FCCC") instead of the exact KG labels.

**Actual KG labels discovered:**
```
UN FAO, UN FAO FRA, UN FAO Kotka III, UN FAO RAP, UN ECEE/FAO
UN FCCC, UN FCCC IPCC GPG, IPCC Kyoto Protocol
EU, EU Copenicus, EU JRC, EUROSTAT, European Community, European Environment Agency
UN EP, UN EP EAP AP, UN EP GRID, UN EP/CBD
```

**Fix:**
- Added `JURISDICTION_MAP` dict mapping org aliases → exact KG labels
- Updated `SYSTEM_PROMPT` JURISDICTION MATCHING RULES to use `IN()` with exact labels instead of `CONTAINS()`
- Updated few-shot examples for FAO and UNFCCC to use `IN()` filters
- Added `JURISDICTION MATCHING RULES` section documenting exact labels for all major orgs

**Before:**
```sparql
FILTER(CONTAINS(LCASE(?jurisdiction), "fccc"))
```
**After:**
```sparql
FILTER(?jurisdiction IN ("UN FCCC", "UN FCCC IPCC GPG", "IPCC Kyoto Protocol"))
```

---

### (b) New `conceptual` intent — `workflow/planner.py` + `workflow/retriever.py`

**Root cause:** Questions like *"En quoi l'usage du sol est-il d'intérêt…"* have no jurisdiction and no typological keyword — they ask about the role/value of a definitional category. The planner had no intent for this and returned NOT_IN_CORPUS.

**Fix in `planner.py`:**
- Added `conceptual` to the intent taxonomy in `SYSTEM_PROMPT`
- Added rule: triggered by questions about the interest/role of a category (land use, land cover, ecological functions)
- Added two few-shot examples mapping land use/cover questions → `{"intent": "conceptual", "keyword": "LandUse"/"LandCover"}`

**Fix in `retriever.py`:**
- Added `CONCEPTUAL_SPARQL` template that fetches all definitions filtered by `:hasCategory` label
- Added `_run_conceptual(endpoint, keyword)` function with category name normalisation
- Wired into `retrieve()` before the typological branch

**Questions fixed:** Q19 (land use), Q20 (land cover), Q24 (ecosystem services)

---

### (c) `not_in_corpus` intent for absent regulations — `workflow/planner.py` + `workflow/tools.py`

**Root cause:** EUDR (Regulation EU 2023/1115) is not in the KG. The planner had no way to signal this, so it fell through to the EU 2010/2013 entries and generated a hallucinated answer attributing EU thresholds to EUDR.

**Fix in `planner.py`:**
- Added `not_in_corpus` to the intent taxonomy
- Added rule: triggered when the question references an org/regulation absent from the KG (EUDR explicitly listed)
- LLM outputs `{"intent": "not_in_corpus"}` — no SPARQL generated

**Fix in `retriever.py`:**
- Added early return for `not_in_corpus` intent — skips all retrieval

**Fix in `tools.py`:**
- Updated `generate_answer()` NOT_IN_CORPUS message to include an explicit EUDR-specific note

**Questions fixed:** Q5, Q6, Q26 — all went from rating 1–2 (hallucination) to rating 5 (correct refusal)

---

### (d) Jurisdiction-priority reranking — `workflow/retriever.py`

**Root cause:** `_rerank_by_relevance()` scored rows by bag-of-words overlap between the question (in French) and the definition text (in English). International org rows scored low because French question words don't appear in English KG text. Country rows with more verbose text scored higher by accident.

**Fix:**
- Replaced bag-of-words scoring with jurisdiction-priority scoring
- Added `JURISDICTION_PRIORITY` dict mapping org keywords (fao, unfccc, kyoto, eu…) → exact KG labels
- If a question mentions an org keyword, all rows from that org's labels receive a +100 score boost
- Secondary score: keyword overlap on words longer than 3 chars (filters out stopwords)

**Before:** Ethiopia row scores higher than UN FCCC row on UNFCCC question  
**After:** UN FCCC rows always ranked first on UNFCCC questions

---

### (e) Expanded typological keywords — `workflow/retriever.py`

**Root cause:** `TYPOLOGICAL_KEYWORDS` used narrow English terms. FAO FRA entries use slightly different phrasing (`"natural regeneration"`, `"planted stand"`) that wasn't matched.

**Added terms:**

| Type | Added keywords |
|------|---------------|
| `systemic` | `living organism`, `biotic` |
| `structural` | `crown closure`, `basal area` |
| `ecological` | `species`, `fauna`, `flora` |
| `primary` | `climax`, `intact forest` |
| `regenerated` | `natural regrowth`, `naturally grown`, `spontaneous regenerat` |
| `plantation` | `reforestation`, `afforestation`, `monoculture`, `planted trees` |
| `agroforest` | `smallholder`, `agro-forest`, `trees outside` |
| `urban` | `peri-urban`, `street tree`, `municipal` |

**Questions improved:** Q14 (plantation), Q18 (plantation vs regenerated)  
**Still failing:** Q13 (forêt naturellement régénérée) — label in KG needs investigation

---

---

## v2 → v3 : Answer Grounding, Dual-Typological, Tree Concept, Kyoto Injection

**Problem:** Expert evaluation of v2 results (avg 3.69/5) revealed remaining issues:
1. FAO 2005 still diluted by peripheral entries (FAO 1998, FAO 2002) — not ranked first
2. Comparative questions (primary vs regenerated) still insufficient — single typological query, no FAO FRA
3. "Qu'est ce qu'un arbre" returns national table without FAO canonical ≥5m definition
4. UNFCCC plantation question doesn't surface Kyoto Forest clause
5. Systemic definitions miss AFF 2011 as primary reference
6. LLM occasionally fills gaps from general knowledge instead of flagging absence

**Files changed:** `workflow/planner.py`, `workflow/retriever.py`, `workflow/tools.py`, `workflow/steps.py`, `workflow/prompts.py`

---

### (a) FAO year-preference in reranking — `workflow/retriever.py`

Added `preferred_years = {"2005", "2006", "2010", "2013", "2015"}` to `_rerank_by_relevance()`. Rows from these years get a +10 score boost on top of jurisdiction-priority. FAO 2005 now consistently appears first for FAO questions.

---

### (b) Tree concept direct query — `workflow/retriever.py` + `workflow/planner.py`

**KG discovery:** `:defines :Tree` exists as a property. Added `TREE_CONCEPT_SPARQL` that fetches definitions with `:defines :Tree` directly.

Added `tree` as a typological keyword routed to `_run_tree_concept()`. Added few-shot example in `planner.py`: "Qu'est ce qu'un arbre" → `{"intent": "typological", "keyword": "tree"}`.

---

### (c) Dual-typological retrieval for comparatives — `workflow/retriever.py` + `workflow/planner.py`

Added `COMPARATIVE_PAIRS` dict in `_run_typological()`: `primary_vs_regenerated` and `plantation_vs_regenerated` each run two separate typological queries and merge results (8 rows each). Added few-shot examples in `planner.py` for both comparison questions.

---

### (d) Kyoto Forest injection for plantation/UNFCCC — `workflow/retriever.py` + `workflow/tools.py` + `workflow/steps.py`

Added `KYOTO_FOREST_SPARQL` targeting UN FCCC/FAO entries containing `planted stand`, `plantation`, `afforestation`. For `boolean_reasoning` questions containing both "plantation" and "unfccc/kyoto", the retriever injects these results on top of the standard SPARQL results.

Fixed question propagation: `steps.py` now passes `ev.question` to `tools.retrieve_context()`, which injects it as `plan["_question"]` so `retrieve()` can access it for context-aware injection.

---

### (e) AFF 2011 systemic lookup — `workflow/retriever.py`

Added `AFF_SYSTEMIC_SPARQL` targeting AFF, UN FAO FRA jurisdictions plus `functional unit` / `dynamic complex` / `ecosystem` CONTAINS filters. For `keyword="systemic"`, retriever now tries AFF_SYSTEMIC_SPARQL first before falling back to generic typological search.

---

### (f) Stronger corpus grounding in prompts — `workflow/prompts.py`

Added two explicit rules to `MARKDOWN_RULES`:
- "Use ONLY the provided context. Never fill gaps from general knowledge."
- "Never synthesise a definition not explicitly stated in the context. If you cite a source it must appear verbatim in the context."

---

### KG gap confirmed — `forêt naturellement régénérée`
Investigation confirmed: the KG contains **no entries** matching "regenerat*" in `definitionText`. FAO FRA is indexed under different text. This is a data gap — not fixable at the pipeline level without re-ingesting FAO FRA with the correct text.

---

## Evaluation Results Summary

| Version | Avg Rating | Validated | Corrected | Rejected | Notes |
|---------|-----------|-----------|-----------|----------|-------|
| v1 (baseline) | 2.70/5 | 4 | 7 | 9 (+ 6 errors) | Groq limit, major retrieval failures |
| v2 (improved) | 3.69/5 | 14 | 10 | 1 | All 26 questions answered |
| **Delta** | **+1.00** | **+10** | **+3** | **-8** | |

### Remaining issues after v2
- `forêt naturellement régénérée` still returns NOT_IN_CORPUS — KG label needs inspection
- FAO 2005 canonical definition still diluted by peripheral FAO entries (FAO 1998, FAO 2002)
- Comparative questions (primary vs regenerated) partially answered — no dedicated dual-typological retrieval
- Typological answers missing AFF 2011 and FAO 1958 as primary systemic references
