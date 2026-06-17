"""
Generate a versioned evaluation report from graph_rag_eval.db.
Usage: python reports/generate_report.py [--version N]
If --version is omitted, reports on the latest version.
"""
from __future__ import annotations
import argparse, sqlite3, json
from datetime import datetime, timezone
from pathlib import Path

DB_PATH  = Path(__file__).parent.parent / "graph_rag_eval.db"
REPORTS  = Path(__file__).parent

STATUS_EMOJI = {"validated": "✅", "corrected": "⚠️", "rejected": "❌"}
RATING_BAR   = {1: "█░░░░", 2: "██░░░", 3: "███░░", 4: "████░", 5: "█████"}

# Add an entry here each time you run a new pipeline version
CHANGELOG: dict[int, dict] = {
    1: {
        "title": "Baseline pipeline (pre-improvements)",
        "pipeline_files": [],
        "changes": [],
        "known_issues": [
            "UNFCCC retrieval fails — SPARQL CONTAINS filter hits Ethiopia instead of UN FCCC",
            "Conceptual questions (land use/cover) return NOT_IN_CORPUS — no intent for category synthesis",
            "EUDR questions answered with EU 2010/2013 data — EUDR not in corpus but not flagged",
            "Reranking uses bag-of-words overlap — international org rows deprioritised vs country rows",
            "TYPOLOGICAL_KEYWORDS too narrow — misses FAO FRA entries for 'regenerated' and 'plantation'",
        ],
    },
    2: {
        "title": "Pipeline improvements — jurisdiction mapping, conceptual intent, reranking, typological keywords",
        "pipeline_files": ["workflow/planner.py", "workflow/retriever.py", "workflow/tools.py"],
        "changes": [
            "(a) planner.py — Added JURISDICTION_MAP with exact KG labels (UN FCCC, UN FAO, IPCC Kyoto Protocol, EU, UN EP…). "
            "SPARQL now uses IN() with exact labels instead of CONTAINS() for international orgs. "
            "Eliminated false positives (Ethiopia matching FCCC text).",

            "(b) planner.py + retriever.py — Added 'conceptual' intent for questions about the role/interest of "
            "a category (land use, land cover, ecological functions). Planner emits {intent: conceptual, keyword: LandUse/LandCover}. "
            "Retriever runs CONCEPTUAL_SPARQL filtering by :hasCategory label. "
            "Fixes NOT_IN_CORPUS on Q19/Q20.",

            "(c) retriever.py — Replaced bag-of-words _rerank_by_relevance() with jurisdiction-priority scoring. "
            "If the question mentions 'fao', 'unfccc', 'kyoto' etc., rows from matching KG labels score +100. "
            "Eliminates Ethiopia/random-country substitution on org-level questions.",

            "(d) retriever.py — Expanded TYPOLOGICAL_KEYWORDS for 'regenerated' (added: natural regrowth, "
            "naturally grown, spontaneous regenerat) and 'plantation' (added: reforestation, afforestation, "
            "monoculture, planted trees). Catches FAO FRA entries previously missed.",

            "(e) planner.py — Added 'not_in_corpus' intent for EUDR and other absent regulations. "
            "tools.py updated to return a clear disclaimer including an EUDR-specific note.",
        ],
        "known_issues": [
            "Comparative questions (primary vs regenerated, plantation vs regenerated) still rely on typological retrieval "
            "which may not return both types in one query.",
            "FAO 2005 canonical definition may still be diluted by peripheral FAO entries (FAO 2002 trees-outside-forest).",
        ],
    },
    5: {
        "title": "Pipeline improvements — FAO year ordering, tree concept, dual-typological, Kyoto injection, AFF systemic, prompt grounding",
        "pipeline_files": ["workflow/planner.py", "workflow/retriever.py", "workflow/tools.py", "workflow/steps.py", "workflow/prompts.py"],
        "changes": [
            "(a) retriever.py — FAO year-preference in reranking: preferred_years {2005,2006,2010,2013,2015} get +10 score. FAO 2005 now consistently first.",
            "(b) retriever.py + planner.py — Tree concept direct query: TREE_CONCEPT_SPARQL uses :defines :Tree. keyword='tree' routes to _run_tree_concept(). Q23 now returns FAO canonical tree definition.",
            "(c) retriever.py + planner.py — Dual-typological for comparatives: COMPARATIVE_PAIRS runs two typological queries and merges results. Few-shot examples added for primary_vs_regenerated and plantation_vs_regenerated.",
            "(d) retriever.py + tools.py + steps.py — Kyoto Forest injection: KYOTO_FOREST_SPARQL targets UN FCCC/FAO entries with planted stand/plantation/afforestation. Injected into boolean_reasoning when question contains plantation+unfccc. Question now propagated through steps→tools→retrieve.",
            "(e) retriever.py — AFF systemic lookup: AFF_SYSTEMIC_SPARQL targets AFF + functional unit/dynamic complex/ecosystem. systemic intent now tries this first. Q11 now cites AFF 2011.",
            "(f) prompts.py — Stronger corpus grounding: 'Use ONLY the provided context, never fill gaps from general knowledge' and 'Never synthesise a definition not explicitly stated in the context'.",
        ],
        "known_issues": [
            "Q1 regression: generic question 'Qu est ce qu une foret' now returns NOT_IN_CORPUS — planner emits wrong intent without explicit org keyword.",
            "FAO FRA not in KG: 'foret naturellement regeneree' (Q13), 'foret primaire' (Q12), comparatives (Q17) remain limited — data gap.",
            "Plantation vs regenerated (Q18) slight regression vs v2 — dual-typological context present but LLM synthesis weaker.",
            "UNFCCC plantation (Q4) Kyoto context now retrieved but LLM still not giving clear yes/no conclusion.",
        ],
    },
}


def load_version(conn, version: int) -> list[dict]:
    rows = conn.execute("""
        SELECT question, generated_response, retrieved_triplets,
               sparql_query, expert_rating, expert_status,
               expert_correction, expert_issues, expert_note,
               timestamp
        FROM evaluations
        WHERE version = ?
        ORDER BY timestamp
    """, (version,)).fetchall()
    return [
        {
            "question":    r[0], "answer":      r[1], "context":  r[2],
            "sparql":      r[3], "rating":      r[4], "status":   r[5],
            "correction":  r[6], "issues":      r[7], "note":     r[8],
            "timestamp":   r[9],
        }
        for r in rows
    ]


def compute_stats(rows: list[dict]) -> dict:
    ratings = [r["rating"] for r in rows if r["rating"] is not None]
    statuses = [r["status"] for r in rows if r["status"]]
    issues_flat = []
    for r in rows:
        if r["issues"]:
            issues_flat.extend(r["issues"].split(","))

    by_rating = {i: sum(1 for x in ratings if x == i) for i in range(1, 6)}
    by_status = {s: statuses.count(s) for s in ["validated", "corrected", "rejected"]}
    issue_counts: dict[str, int] = {}
    for iss in issues_flat:
        iss = iss.strip()
        issue_counts[iss] = issue_counts.get(iss, 0) + 1

    return {
        "n":          len(rows),
        "avg":        round(sum(ratings) / len(ratings), 2) if ratings else 0,
        "by_rating":  by_rating,
        "by_status":  by_status,
        "top_issues": sorted(issue_counts.items(), key=lambda x: -x[1])[:10],
    }


def rating_dist_bar(by_rating: dict) -> str:
    lines = []
    for r in range(5, 0, -1):
        count = by_rating.get(r, 0)
        bar = "█" * count
        lines.append(f"  {r}/5 [{bar:<26}] {count}")
    return "\n".join(lines)


def build_report(version: int, rows: list[dict], stats: dict, prev_stats: dict | None) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = []

    lines += [
        f"# ForestGraphRAG — Evaluation Report v{version}",
        f"Generated: {ts}  |  Questions: {stats['n']}  |  DB: graph_rag_eval.db",
        "",
        "---",
        "",
        "## Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Average expert rating | **{stats['avg']}/5** |",
        f"| Validated (5 or 4) | {stats['by_status'].get('validated', 0)} |",
        f"| Corrected (3 or 2) | {stats['by_status'].get('corrected', 0)} |",
        f"| Rejected (1) | {stats['by_status'].get('rejected', 0)} |",
    ]

    if prev_stats:
        delta = round(stats["avg"] - prev_stats["avg"], 2)
        arrow = "▲" if delta > 0 else ("▼" if delta < 0 else "→")
        lines.append(f"| vs previous version | {arrow} {delta:+.2f} |")

    lines += [
        "",
        "### Rating Distribution",
        "",
        "```",
        rating_dist_bar(stats["by_rating"]),
        "```",
        "",
        "### Top Issues",
        "",
    ]
    for issue, count in stats["top_issues"]:
        lines.append(f"- `{issue}` — {count}×")

    # Changelog section
    changelog = CHANGELOG.get(version)
    if changelog:
        lines += ["", "---", "", f"## Pipeline — What Changed in v{version}", ""]
        lines.append(f"**{changelog['title']}**")
        lines.append("")

        if changelog["changes"]:
            lines.append("### Changes made")
            lines.append("")
            for c in changelog["changes"]:
                lines.append(f"- {c}")
            lines.append("")

        if changelog.get("pipeline_files"):
            lines.append(f"**Files modified:** `{'`, `'.join(changelog['pipeline_files'])}`")
            lines.append("")

        if changelog["known_issues"]:
            lines.append("### Known issues / remaining problems")
            lines.append("")
            for iss in changelog["known_issues"]:
                lines.append(f"- {iss}")
            lines.append("")

    lines += ["---", "", "## Per-Question Results", ""]

    for i, row in enumerate(rows, 1):
        rating  = row["rating"] or "?"
        status  = row["status"] or "?"
        emoji   = STATUS_EMOJI.get(status, "?")
        bar     = RATING_BAR.get(rating, "?????")
        answer  = (row["answer"] or "").replace("\n", " ")[:300]
        sparql  = (row["sparql"] or "").strip()[:200]

        lines += [
            f"### [{i}] {row['question']}",
            "",
            f"**Rating:** {rating}/5 {bar}  {emoji} `{status}`",
            "",
            f"**Answer preview:** {answer}...",
            "",
        ]
        if row["note"]:
            lines += [f"**Expert note:** {row['note']}", ""]
        if row["correction"]:
            lines += [f"**Correction needed:** {row['correction']}", ""]
        if row["issues"]:
            lines += [f"**Issues:** `{row['issues']}`", ""]
        if sparql:
            lines += [f"**SPARQL used:** `{sparql}`", ""]
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", type=int, default=None)
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)

    max_version = conn.execute("SELECT MAX(version) FROM evaluations").fetchone()[0] or 1
    version = args.version if args.version else max_version

    rows = load_version(conn, version)
    if not rows:
        print(f"No rows found for version {version}")
        return

    stats = compute_stats(rows)

    prev_stats = None
    if version > 1:
        prev_rows = load_version(conn, version - 1)
        if prev_rows:
            prev_stats = compute_stats(prev_rows)

    conn.close()

    report = build_report(version, rows, stats, prev_stats)

    out_path = REPORTS / f"report_v{version}.md"
    out_path.write_text(report, encoding="utf-8")
    print(f"Report written → {out_path}")
    print(f"Version {version} | avg={stats['avg']}/5 | n={stats['n']}")
    if prev_stats:
        delta = round(stats["avg"] - prev_stats["avg"], 2)
        print(f"vs v{version-1}: {delta:+.2f}")


if __name__ == "__main__":
    main()
