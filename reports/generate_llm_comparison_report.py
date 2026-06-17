"""
Generate a side-by-side LLM comparison report from llm_comparison.db.
Usage: python reports/generate_llm_comparison_report.py [--run-ts TIMESTAMP]
If --run-ts omitted, uses the most recent run.
"""
from __future__ import annotations
import argparse, sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH  = Path(__file__).parent.parent / "llm_comparison.db"
REPORTS  = Path(__file__).parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-ts", type=str, default=None)
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)

    run_ts = args.run_ts or conn.execute(
        "SELECT MAX(run_ts) FROM llm_summary"
    ).fetchone()[0]

    if not run_ts:
        print("No runs found in llm_comparison.db")
        return

    summary_rows = conn.execute("""
        SELECT model_name, backend, n_total, n_answered, n_not_in_corpus, n_errors,
               avg_answer_len, avg_latency_s
        FROM llm_summary WHERE run_ts=? ORDER BY n_answered DESC
    """, (run_ts,)).fetchall()

    models = [r[0] for r in summary_rows]
    pipeline_version = conn.execute(
        "SELECT pipeline_version FROM llm_summary WHERE run_ts=? LIMIT 1", (run_ts,)
    ).fetchone()[0]

    questions = conn.execute("""
        SELECT DISTINCT question FROM llm_answers WHERE run_ts=? ORDER BY rowid
    """, (run_ts,)).fetchall()
    questions = [q[0] for q in questions]

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = []

    lines += [
        f"# ForestGraphRAG — LLM Comparison Report",
        f"Generated: {ts}  |  Pipeline v{pipeline_version}  |  Run: `{run_ts[:19]}`",
        "",
        "---",
        "",
        "## Model Summary",
        "",
        f"| Model | Backend | Answered | NOT_IN_CORPUS | Errors | Avg Len | Avg Latency |",
        f"|-------|---------|----------|---------------|--------|---------|-------------|",
    ]
    for r in summary_rows:
        model, backend, n_total, n_ans, n_nic, n_err, avg_len, avg_lat = r
        lines.append(
            f"| {model} | {backend} | {n_ans}/{n_total} | {n_nic} | {n_err} "
            f"| {avg_len:.0f} chars | {avg_lat:.1f}s |"
        )

    lines += ["", "---", "", "## Per-Question Comparison", ""]

    for i, question in enumerate(questions, 1):
        lines += [f"### [{i}] {question}", ""]

        for model in models:
            row = conn.execute("""
                SELECT intent, answer, latency_s, is_not_in_corpus, is_error, error_msg
                FROM llm_answers
                WHERE run_ts=? AND model_name=? AND question=?
            """, (run_ts, model, question)).fetchone()

            if not row:
                lines += [f"**{model}:** *(no result)*", ""]
                continue

            intent, answer, latency, is_nic, is_err, error_msg = row

            if is_err:
                lines += [f"**{model}** `ERROR` ({latency}s): `{(error_msg or '')[:120]}`", ""]
            elif is_nic:
                lines += [f"**{model}** `not_in_corpus` ({latency}s): NOT_IN_CORPUS ✓", ""]
            else:
                preview = (answer or "").replace("\n", " ")[:400]
                lines += [
                    f"**{model}** `{intent}` ({latency}s)",
                    f"> {preview}{'...' if len(answer or '') > 400 else ''}",
                    "",
                ]

        lines += ["---", ""]

    report = "\n".join(lines)
    out_path = REPORTS / f"llm_comparison_v{pipeline_version}.md"
    out_path.write_text(report, encoding="utf-8")
    print(f"Report written → {out_path}")
    conn.close()


if __name__ == "__main__":
    main()
