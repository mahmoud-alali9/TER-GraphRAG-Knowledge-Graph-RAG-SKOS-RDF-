"""
RAGAS evaluation for ForestGraphRAG pipeline.
Reads pipeline answers from graph_rag_eval.db (latest version by default).
Uses GPT-4o-mini as judge LLM and text-embedding-3-small for embeddings.
Results saved to ragas_results.db.

Usage:
    python run_ragas.py [--version N]

Input:  graph_rag_eval.db  — evaluations table (version N)
Output: ragas_results.db   — ragas_scores + ragas_summary tables
"""
from __future__ import annotations
import warnings; warnings.filterwarnings("ignore")
import os, sys, json, sqlite3, uuid, argparse
from datetime import datetime, timezone

sys.path.insert(0, '.')
sys.path.insert(0, '/home/salah/Desktop/Study/TER/terragv2-main/venv/lib/python3.12/site-packages')

from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.metrics import (
    faithfulness,
    context_recall,
    context_precision,
    answer_correctness,
)
from ragas import evaluate, EvaluationDataset, SingleTurnSample
from ragas.run_config import RunConfig

# ── Parse args ─────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--version", type=int, default=None,
                    help="DB version to evaluate (default: latest)")
args = parser.parse_args()

# ── Wire LLM / embeddings ──────────────────────────────────────────────────
llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4o-mini", temperature=0))
emb = LangchainEmbeddingsWrapper(OpenAIEmbeddings(model="text-embedding-3-small"))

for m in [faithfulness, context_recall, context_precision, answer_correctness]:
    m.llm = llm
answer_correctness.embeddings = emb

METRICS_WITH_REF    = [faithfulness, context_recall, context_precision, answer_correctness]
METRICS_WITHOUT_REF = [faithfulness, context_precision]

# ── Ground-truth references ────────────────────────────────────────────────
REFS = {
    "Qu'est ce qu'une forêt ?":
        "FAO 2005: land >0.5 ha, trees >5 m, canopy >10%. FAO 1958: vegetation dominated by trees influencing climate/water. Three axes: LandCover, LandUse, Ecological.",
    "Qu'est ce qu'une forêt au sens de la FAO ?":
        "FAO 2005: land >0.5 ha, trees >5 m, canopy >10%, excludes agricultural/urban land. Includes planted stands. Historical evolution from 1953 to 2005.",
    "Qu'est ce qu'une forêt au sens de l'UNFCCC ?":
        "UNFCCC Marrakech 2001: 0.05-1.0 ha, canopy 10-30%, tree height 2-5 m. Country chooses single value within these ranges. Includes temporarily unstocked areas.",
    "Est ce qu'une plantation forestière est une forêt au sens de l'UNFCCC ?":
        "Yes. UNFCCC/KP explicitly includes planted stands. Kyoto Forest = plantation established after January 1 1990 on previously non-forested land.",
    "Est ce qu'une plantation forestière est une forêt au sens de l'EUDR ?":
        "EUDR is not present in the corpus. No EUDR-specific definition is available in the knowledge base.",
    "Qu'est ce qu'une forêt au sens de l'EUDR ?":
        "EUDR is not present in the corpus. EU definitions available (JRC 2003, EEA, Copernicus) align with FAO but cannot be attributed to EUDR.",
    "Donne moi la définition de la forêt s'adossant à la définition de l'UNFCCC en Albanie":
        "Albania KP 2006/2007: canopy 30%, area 0.1 ha, height 3 m.",
    "Donne moi la définition de la forêt s'adossant à la définition de l'UNFCCC au Ghana":
        "Ghana KP 2006: canopy 15%, area 0.1 ha, height 2 m (LandUse).",
    "Donne moi la définition de la forêt s'adossant à la définition de l'UNFCCC au Brésil":
        "Brazil KP 2006/2009: canopy 30%, area 1 ha, height 5 m. Brazil chose maximum values within UNFCCC ranges.",
    "Donne moi une définition structurelle de la forêt":
        "No definition explicitly labelled structural in corpus. LandCover definitions (FAO 2005) provide measurable structural thresholds: >0.5 ha, >5 m, >10% canopy.",
    "Donne moi une définition systémique de la forêt":
        "AFF 2011: dynamic complex of plant, animal and microorganism communities and the non-living environment acting as a functional unit. FAO 1958: capable of influencing climate and water regimes.",
    "Donne moi une définition de la forêt primaire":
        "No explicit primary forest definition in corpus. FAO FRA: naturally regenerated forest of native species with no clearly visible human activity and undisturbed ecological processes.",
    "Donne moi une définition de la forêt naturellement régénérée":
        "FAO FRA 2005/2010: predominantly native species, regenerating naturally, no human planting. Includes secondary forest recovering from disturbance. Not explicitly in KG.",
    "Donne moi une définition de la plantation forestière":
        "FAO: forest established by planting or seeding, intensive management. Kyoto Forest: plantation established after 1 January 1990 on previously non-forested land.",
    "Donne moi une définition d'une agroforêt":
        "Agroforest (LandUse): forest managed more or less intensively by smallholders producing wood and non-wood forest products.",
    "Donne moi une définition de la forêt urbaine":
        "No formal urban forest definition in corpus. FAO excludes land under urban land use from forest statistics.",
    "Quelles sont les principales différences entre forêt primaire et forêt naturellement régénérée ?":
        "Primary forest: native species, no visible human activity, undisturbed ecological processes. Naturally regenerated: includes secondary forest recovering from disturbance. Key difference: degree of past human intervention.",
    "Quelles sont les principales différences entre plantation forestière et forêt naturellement régénérée ?":
        "Plantation: planted/seeded, intensive management, often monoculture. Naturally regenerated: native species, no planting, natural recovery. Two distinct FAO sub-categories.",
    "En quoi l'usage du sol (land use) peut être d'intérêt quand on cherche à caractériser la forêt ?":
        "LandUse captures management intent rather than physical state. Important for carbon accounting and policy. Germany NFI uses 50% canopy under LandUse definition.",
    "En quoi la couverture du sol (land cover) peut être d'intérêt quand on cherche à caractériser la forêt ?":
        "LandCover describes physical/biophysical state (canopy %, height, area). FAO 2005 is a LandCover definition. Remote-sensing compatible. Key for global monitoring.",
    "Est ce que la FAO considère la forêt urbaine comme étant une forêt ?":
        "No. FAO 2005 explicitly excludes land predominantly under agricultural or urban land use from forest statistics.",
    "Est ce que l'UNFCCC considère la forêt urbaine comme étant une forêt ?":
        "UNFCCC criteria do not explicitly mention urban exclusion. Urban trees can meet UNFCCC thresholds but national KP submissions typically exclude urban land. Corpus does not give explicit ruling.",
    "Qu'est ce qu'un arbre ?":
        "FAO 2000/2005: woody perennial plant typically >=5 m height at maturity in situ. This threshold is used in the FAO 2005 forest definition.",
    "Est ce que je peux définir une forêt à partir des services écosystémiques qu'elle est en capacité de fournir ?":
        "No formal definition based on ecosystem services in corpus. Services are consequences of forest existence, not definitional criteria. FAO 1958 and AFF 2011 approach functional framing.",
    "Est ce que je peux définir une forêt à partir de ses fonctions écologiques ?":
        "Yes. AFF 2011: dynamic complex of plant, animal and microorganism communities acting as a functional unit. FAO 1958: influencing climate and water regimes.",
    "L'EUDR reprend essentiellement les définitions (forêt en particulier) de la FAO":
        "Cannot be verified from corpus. EUDR is not present in the knowledge base. This claim cannot be confirmed or denied from corpus evidence.",
}

# ── Load samples from DB ───────────────────────────────────────────────────
conn_e = sqlite3.connect("graph_rag_eval.db")

# Determine version
if args.version:
    version = args.version
else:
    version = conn_e.execute("SELECT MAX(version) FROM evaluations").fetchone()[0]

print("=" * 70)
print(f"RAGAS Evaluation — ForestGraphRAG  (DB version {version})")
print("=" * 70)

rows = conn_e.execute("""
    SELECT question, generated_response, retrieved_triplets,
           sparql_query, expert_rating, expert_status
    FROM evaluations
    WHERE version = ?
    ORDER BY timestamp
""", (version,)).fetchall()
conn_e.close()

samples_meta = []
for question, answer, ctx_json, sparql, expert_rating, expert_status in rows:
    # Skip NOT_IN_CORPUS and pipeline errors — no meaningful context to evaluate
    if not answer or "Cette information n'est pas présente" in answer or "PIPELINE ERROR" in answer:
        continue
    if len(answer) < 50:
        continue

    # Build retrieved context list
    contexts = []
    if ctx_json:
        try:
            parsed = json.loads(ctx_json)
            if isinstance(parsed, str):
                contexts = [parsed[:1200]]
            elif isinstance(parsed, list):
                contexts = [str(x) for x in parsed[:5]]
            else:
                contexts = [str(parsed)[:1200]]
        except Exception:
            contexts = [str(ctx_json)[:1200]]
    if not contexts:
        contexts = ["No context retrieved."]

    ref = REFS.get(question)
    samples_meta.append({
        "question":       question,
        "response":       answer,
        "reference":      ref,
        "contexts":       contexts,
        "expert_rating":  expert_rating,
        "expert_status":  expert_status,
    })

print(f"Samples loaded   : {len(samples_meta)}")
print(f"With reference   : {sum(1 for m in samples_meta if m['reference'])}")
print(f"Without reference: {sum(1 for m in samples_meta if not m['reference'])}")
print("=" * 70)

# ── SQLite output ──────────────────────────────────────────────────────────
conn_r = sqlite3.connect("ragas_results.db")
conn_r.execute("""CREATE TABLE IF NOT EXISTS ragas_scores (
    id TEXT PRIMARY KEY,
    run_ts TEXT,
    db_version INTEGER,
    question TEXT,
    response_preview TEXT,
    reference_preview TEXT,
    expert_rating INTEGER,
    expert_status TEXT,
    faithfulness REAL,
    context_recall REAL,
    context_precision REAL,
    answer_correctness REAL,
    ragas_error TEXT
)""")
conn_r.commit()

run_ts   = datetime.now(timezone.utc).isoformat()
all_scores = []

for i, meta in enumerate(samples_meta, 1):
    q      = meta["question"]
    ans    = meta["response"]
    ref    = meta["reference"]
    ctx    = meta["contexts"]
    has_ref = bool(ref and len(ref) > 10)
    active  = METRICS_WITH_REF if has_ref else METRICS_WITHOUT_REF

    print(f"\n[{i:2}/{len(samples_meta)}] {q[:65]}")
    print(f"  ref={'yes' if has_ref else 'no ':3} | ctx_len={sum(len(c) for c in ctx)} | ans_len={len(ans)}")

    scores  = {}
    err_msg = None
    try:
        sample = SingleTurnSample(
            user_input=q,
            retrieved_contexts=ctx,
            response=ans,
            reference=ref if has_ref else None,
        )
        run_cfg = RunConfig(timeout=180, max_retries=2, max_wait=60)
        result  = evaluate(
            EvaluationDataset(samples=[sample]),
            metrics=active,
            llm=llm,
            embeddings=emb,
            run_config=run_cfg,
        )
        row_df = result.to_pandas().iloc[0].to_dict()

        def _g(k): return float(row_df[k]) if row_df.get(k) is not None else None
        scores = {
            "faithfulness":       _g("faithfulness"),
            "context_recall":     _g("context_recall"),
            "context_precision":  _g("context_precision"),
            "answer_correctness": _g("answer_correctness"),
        }
        def _fmt(v): return f"{v:.2f}" if v is not None else "  - "
        print(f"  faith={_fmt(scores['faithfulness'])}  "
              f"recall={_fmt(scores['context_recall'])}  "
              f"prec={_fmt(scores['context_precision'])}  "
              f"ans_corr={_fmt(scores['answer_correctness'])}")

    except Exception as e:
        err_msg = str(e)[:300]
        print(f"  ERROR: {err_msg[:120]}")

    conn_r.execute(
        "INSERT OR REPLACE INTO ragas_scores VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (str(uuid.uuid4()), run_ts, version, q,
         ans[:300], str(ref)[:200] if ref else None,
         meta["expert_rating"], meta["expert_status"],
         scores.get("faithfulness"), scores.get("context_recall"),
         scores.get("context_precision"), scores.get("answer_correctness"),
         err_msg)
    )
    conn_r.commit()
    all_scores.append(scores)

# ── Aggregate ──────────────────────────────────────────────────────────────
def avg(key):
    vals = [s[key] for s in all_scores if s.get(key) is not None]
    return round(sum(vals) / len(vals), 3) if vals else None

print("\n" + "=" * 70)
print(f"FINAL RAGAS RESULTS  (DB version {version})")
print("=" * 70)
print(f"  {'Faithfulness':<28} {str(avg('faithfulness')):>8}")
print(f"  {'Context Recall':<28} {str(avg('context_recall')):>8}")
print(f"  {'Context Precision':<28} {str(avg('context_precision')):>8}")
print(f"  {'Answer Correctness':<28} {str(avg('answer_correctness')):>8}")
overall_vals = [v for v in [avg('faithfulness'), avg('context_recall'),
                             avg('context_precision'), avg('answer_correctness')] if v]
overall = round(sum(overall_vals) / len(overall_vals), 3) if overall_vals else None
print(f"  {'OVERALL (mean of above)':<28} {str(overall):>8}")
print(f"\nSamples evaluated : {len(all_scores)}")
print(f"Results saved to  : ragas_results.db")
print("=" * 70)

# ── Summary table ──────────────────────────────────────────────────────────
conn_r.execute("""CREATE TABLE IF NOT EXISTS ragas_summary (
    run_ts TEXT PRIMARY KEY,
    db_version INTEGER,
    n_samples INTEGER,
    faithfulness REAL,
    context_recall REAL,
    context_precision REAL,
    answer_correctness REAL,
    overall REAL
)""")
conn_r.execute(
    "INSERT OR REPLACE INTO ragas_summary VALUES (?,?,?,?,?,?,?,?)",
    (run_ts, version, len(all_scores),
     avg('faithfulness'), avg('context_recall'),
     avg('context_precision'), avg('answer_correctness'), overall)
)
conn_r.commit()
conn_r.close()
print("\nDone.")
