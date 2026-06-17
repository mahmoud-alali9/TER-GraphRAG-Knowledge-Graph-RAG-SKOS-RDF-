"""
Run 26 evaluation questions through the ForestGraphRAG pipeline
and save raw results to graph_rag_eval.db.
Expert evaluation is done separately after reviewing the actual answers.
"""
from __future__ import annotations
import sys, sqlite3, uuid, json
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, '.')
sys.path.insert(0, '/home/salah/Desktop/Study/TER/terragv2-main/venv/lib/python3.12/site-packages')

from dotenv import load_dotenv; load_dotenv()
from workflow.pipeline import ForestGraphRAGPipeline
from workflow.config import WorkflowConfig

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

cfg = WorkflowConfig(
    endpoint="http://localhost:3030/forestKG/sparql",
    output_dir=Path("outputs"),
    timeout=120,
)
pipeline = ForestGraphRAGPipeline(config=cfg)
conn = sqlite3.connect("graph_rag_eval.db")

# Ensure version column exists
cols = [r[1] for r in conn.execute("PRAGMA table_info(evaluations)").fetchall()]
if "version" not in cols:
    conn.execute("ALTER TABLE evaluations ADD COLUMN version INTEGER DEFAULT 1")
    conn.commit()

# Auto-increment version for this run
current_version = (conn.execute("SELECT MAX(version) FROM evaluations").fetchone()[0] or 0) + 1
run_ts = datetime.now(timezone.utc).isoformat()

# Skip questions already done in THIS version
already_done = set(
    row[0] for row in conn.execute(
        "SELECT question FROM evaluations "
        "WHERE version=? AND generated_response IS NOT NULL "
        "AND generated_response NOT LIKE 'PIPELINE ERROR%'",
        (current_version,)
    ).fetchall()
)

print("=" * 70)
print(f"Batch run — version {current_version} — {len(QUESTIONS)} questions  (skipping {len(already_done)} already done)")
print("=" * 70)

for i, question in enumerate(QUESTIONS, 1):
    if question in already_done:
        print(f"\n[{i:2}/{len(QUESTIONS)}] SKIP: {question[:65]}")
        continue

    print(f"\n[{i:2}/{len(QUESTIONS)}] {question[:70]}")
    try:
        result  = pipeline.query(question)
        answer  = result["answer"]
        sparql  = result.get("sparql_query", "")
        context = result.get("context", "")
        intent  = result.get("intent", "")

        conn.execute("""
            INSERT INTO evaluations (
                id, timestamp, question, sparql_query, retrieved_triplets,
                generated_response, username, prompt_mode, version
            ) VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            str(uuid.uuid4()), run_ts, question, sparql,
            json.dumps(context) if context else None,
            answer, "batch_run", "default", current_version,
        ))
        conn.commit()
        print(f"  intent={intent} | ans_len={len(answer)}")
        print(f"  {answer[:120].replace(chr(10), ' ')}")

    except Exception as e:
        print(f"  ERROR: {e}")
        conn.execute("""
            INSERT INTO evaluations (
                id, timestamp, question, generated_response, username, prompt_mode, version
            ) VALUES (?,?,?,?,?,?,?)
        """, (
            str(uuid.uuid4()), run_ts, question,
            f"PIPELINE ERROR: {e}", "batch_run", "default", current_version,
        ))
        conn.commit()

conn.close()
print("\n" + "=" * 70)
print(f"Done. Results saved to graph_rag_eval.db")
print("=" * 70)
