"""
LLM Comparison Runner for ForestGraphRAG.
Runs all 26 evaluation questions through multiple LLM backends/models,
saves results to llm_comparison.db for side-by-side quality analysis.

Usage:
    python run_llm_comparison.py [--models MODEL1,MODEL2,...] [--pipeline-version N]

Output: llm_comparison.db
  - llm_answers    : one row per (question, model)
  - llm_summary    : aggregate stats per model
"""
from __future__ import annotations
import sys, os, sqlite3, uuid, json, time, argparse
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, '.')
sys.path.insert(0, '/home/salah/Desktop/Study/TER/terragv2-main/venv/lib/python3.12/site-packages')

from dotenv import load_dotenv; load_dotenv()
from workflow.pipeline import ForestGraphRAGPipeline
from workflow.config import WorkflowConfig

# ── Models to compare ─────────────────────────────────────────────────────────
# Format: (backend, model_id, short_name)
MODELS = [
    ("together", "Qwen/Qwen3-235B-A22B-Instruct-2507-tput",  "qwen3-235b"),
    ("together", "google/gemma-4-31B-it",                     "gemma-4-31b"),
]

QUESTIONS = [
    "Qu'est ce qu'une forêt ?",
    "Qu'est ce qu'une forêt au sens de la FAO ?",
    "Qu'est ce qu'une forêt au sens de l'UNFCCC ?",
    "Est ce qu'une plantation forestière est une forêt au sens de l'UNFCCC ?",
    "Est ce qu'une plantation forestière est une forêt au sens de l'EUDR ?",
    "Qu'est ce qu'une forêt au sens de l'EUDR ?",
    "Donne moi la définition de la forêt s'adossant à la définition de l'UNFCCC en Albanie",
    "Donne moi la définition de la forêt s'adossant à la définition de l'UNFCCC au Ghana",
    "Donne moi la définition de la forêt s'adossant à la définition de l'UNFCCC au Brésil",
    "Donne moi une définition structurelle de la forêt",
    "Donne moi une définition systémique de la forêt",
    "Donne moi une définition de la forêt primaire",
    "Donne moi une définition de la forêt naturellement régénérée",
    "Donne moi une définition de la plantation forestière",
    "Donne moi une définition d'une agroforêt",
    "Donne moi une définition de la forêt urbaine",
    "Quelles sont les principales différences entre forêt primaire et forêt naturellement régénérée ?",
    "Quelles sont les principales différences entre plantation forestière et forêt naturellement régénérée ?",
    "En quoi l'usage du sol (land use) peut être d'intérêt quand on cherche à caractériser la forêt ?",
    "En quoi la couverture du sol (land cover) peut être d'intérêt quand on cherche à caractériser la forêt ?",
    "Est ce que la FAO considère la forêt urbaine comme étant une forêt ?",
    "Est ce que l'UNFCCC considère la forêt urbaine comme étant une forêt ?",
    "Qu'est ce qu'un arbre ?",
    "Est ce que je peux définir une forêt à partir des services écosystémiques qu'elle est en capacité de fournir ?",
    "Est ce que je peux définir une forêt à partir de ses fonctions écologiques ?",
    "L'EUDR reprend essentiellement les définitions (forêt en particulier) de la FAO",
]

# ── Args ──────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--models", type=str, default=None,
                    help="Comma-separated short names to run (default: all)")
parser.add_argument("--pipeline-version", type=int, default=None,
                    help="Tag results with this pipeline version (default: auto from graph_rag_eval.db)")
args = parser.parse_args()

filter_models = set(args.models.split(",")) if args.models else None
active_models = [(b, m, n) for b, m, n in MODELS if filter_models is None or n in filter_models]

# Auto-detect pipeline version
pipeline_version = args.pipeline_version
if pipeline_version is None:
    try:
        _c = sqlite3.connect("graph_rag_eval.db")
        pipeline_version = _c.execute("SELECT MAX(version) FROM evaluations").fetchone()[0] or 1
        _c.close()
    except Exception:
        pipeline_version = 0

# ── DB setup ──────────────────────────────────────────────────────────────────
conn = sqlite3.connect("llm_comparison.db")
conn.execute("""CREATE TABLE IF NOT EXISTS llm_answers (
    id               TEXT PRIMARY KEY,
    run_ts           TEXT,
    pipeline_version INTEGER,
    model_name       TEXT,
    backend          TEXT,
    question         TEXT,
    intent           TEXT,
    sparql_query     TEXT,
    context_preview  TEXT,
    answer           TEXT,
    answer_len       INTEGER,
    latency_s        REAL,
    is_not_in_corpus INTEGER,
    is_error         INTEGER,
    error_msg        TEXT
)""")
conn.execute("""CREATE TABLE IF NOT EXISTS llm_summary (
    run_ts           TEXT,
    pipeline_version INTEGER,
    model_name       TEXT,
    backend          TEXT,
    n_total          INTEGER,
    n_not_in_corpus  INTEGER,
    n_errors         INTEGER,
    n_answered       INTEGER,
    avg_answer_len   REAL,
    avg_latency_s    REAL,
    PRIMARY KEY (run_ts, model_name)
)""")
conn.commit()

run_ts = datetime.now(timezone.utc).isoformat()

print("=" * 70)
print(f"LLM Comparison — ForestGraphRAG  (pipeline v{pipeline_version})")
print(f"Models: {[n for _,_,n in active_models]}")
print(f"Questions: {len(QUESTIONS)}")
print("=" * 70)

cfg = WorkflowConfig(
    endpoint="http://localhost:3030/forestKG/sparql",
    output_dir=Path("outputs"),
    timeout=120,
)

# ── Run each model ─────────────────────────────────────────────────────────────
for backend, model_id, model_name in active_models:
    print(f"\n{'━'*70}")
    print(f"MODEL: {model_name}  ({backend} / {model_id})")
    print(f"{'━'*70}")

    # Set env vars so groq_client picks up the right backend/model
    os.environ["LLM_BACKEND"]    = backend
    os.environ["TOGETHER_MODEL"] = model_id

    pipeline = ForestGraphRAGPipeline(config=cfg)

    model_stats = {"n_not_in_corpus": 0, "n_errors": 0, "latencies": [], "answer_lens": []}

    for i, question in enumerate(QUESTIONS, 1):
        print(f"\n  [{i:2}/{len(QUESTIONS)}] {question[:65]}")

        # Skip if already done for this (run_ts, model_name, question)
        existing = conn.execute(
            "SELECT 1 FROM llm_answers WHERE run_ts=? AND model_name=? AND question=?",
            (run_ts, model_name, question)
        ).fetchone()
        if existing:
            print("    → already done, skipping")
            continue

        t0 = time.time()
        intent = sparql = context_preview = answer = error_msg = None
        is_not_in_corpus = is_error = 0

        try:
            result = pipeline.query(question)
            latency = round(time.time() - t0, 2)

            intent         = result.get("intent", "")
            sparql         = (result.get("sparql_query") or "")[:400]
            answer         = result.get("answer") or ""
            ctx            = result.get("context") or ""
            context_preview = ctx[:300]

            is_not_in_corpus = 1 if ("Cette information n'est pas présente" in answer or
                                      intent == "not_in_corpus") else 0
            is_error = 0

            print(f"    intent={intent} | len={len(answer)} | {latency}s")
            if is_not_in_corpus:
                print(f"    → NOT_IN_CORPUS")
                model_stats["n_not_in_corpus"] += 1
            else:
                model_stats["answer_lens"].append(len(answer))

        except Exception as e:
            latency = round(time.time() - t0, 2)
            error_msg = str(e)[:400]
            answer = ""
            intent = "ERROR"
            is_error = 1
            model_stats["n_errors"] += 1
            print(f"    ERROR: {error_msg[:80]}")

        model_stats["latencies"].append(latency)

        conn.execute(
            "INSERT OR REPLACE INTO llm_answers VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (str(uuid.uuid4()), run_ts, pipeline_version, model_name, backend,
             question, intent, sparql, context_preview, answer, len(answer),
             latency, is_not_in_corpus, is_error, error_msg)
        )
        conn.commit()

    # Per-model summary
    n_total   = len(QUESTIONS)
    n_nic     = model_stats["n_not_in_corpus"]
    n_err     = model_stats["n_errors"]
    n_ans     = n_total - n_nic - n_err
    avg_len   = round(sum(model_stats["answer_lens"]) / len(model_stats["answer_lens"]), 1) if model_stats["answer_lens"] else 0
    avg_lat   = round(sum(model_stats["latencies"]) / len(model_stats["latencies"]), 2) if model_stats["latencies"] else 0

    conn.execute(
        "INSERT OR REPLACE INTO llm_summary VALUES (?,?,?,?,?,?,?,?,?,?)",
        (run_ts, pipeline_version, model_name, backend,
         n_total, n_nic, n_err, n_ans, avg_len, avg_lat)
    )
    conn.commit()

    print(f"\n  ── {model_name} summary ──")
    print(f"     Answered        : {n_ans}/{n_total}")
    print(f"     NOT_IN_CORPUS   : {n_nic}")
    print(f"     Errors          : {n_err}")
    print(f"     Avg answer len  : {avg_len} chars")
    print(f"     Avg latency     : {avg_lat}s")

# ── Final comparison table ─────────────────────────────────────────────────────
print("\n" + "=" * 70)
print(f"FINAL COMPARISON  (pipeline v{pipeline_version})")
print("=" * 70)
print(f"  {'Model':<22} {'Answered':>8} {'NIC':>5} {'Errors':>7} {'AvgLen':>8} {'AvgLat':>8}")
print(f"  {'-'*22} {'-'*8} {'-'*5} {'-'*7} {'-'*8} {'-'*8}")

rows = conn.execute("""
    SELECT model_name, n_answered, n_not_in_corpus, n_errors, avg_answer_len, avg_latency_s
    FROM llm_summary
    WHERE run_ts = ?
    ORDER BY n_answered DESC, avg_answer_len DESC
""", (run_ts,)).fetchall()

for r in rows:
    print(f"  {r[0]:<22} {r[1]:>8} {r[2]:>5} {r[3]:>7} {r[4]:>8.0f} {r[5]:>7.1f}s")

print(f"\nResults saved to: llm_comparison.db")
print("=" * 70)
conn.close()
print("\nDone.")
