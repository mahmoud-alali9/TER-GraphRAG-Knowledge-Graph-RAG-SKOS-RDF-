"""Compare graph retrieval against classic RAG retrievers (dense FAISS, BM25, hybrid).

Question: when the user asks about a specific country or organization, do the
top-k retrieved definitions really come from that jurisdiction?

Metric: jurisdiction precision@k = share of the k retrieved definitions whose
jurisdiction is one of the expected ones. We also report "wrong jurisdictions"
(e.g. Ethiopia for a UNFCCC question, the failure we found in v1) and latency.

The "graph" line filters on the exact jurisdiction labels with SPARQL IN(),
like the v2 pipeline. It is precise by construction: the point of the table is
to measure how much the vector baselines lose without that structure.

Usage:
    python scripts/compare_retrievers.py                 # local graph (data/schema.ttl)
    python scripts/compare_retrievers.py --endpoint http://localhost:3030/forestKG/sparql
"""
from __future__ import annotations

import argparse
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from graph.sparql_executor import execute_sparql  # noqa: E402
from vector.corpus import DefinitionDoc  # noqa: E402
from vector.index import SearchHit, build_retrievers  # noqa: E402

FAO = ["UN FAO", "UN FAO FRA", "UN FAO Kotka III", "UN FAO RAP", "UN ECEE/FAO"]
UNFCCC = ["UN FCCC", "UN FCCC IPCC GPG", "IPCC Kyoto Protocol"]

# Questions of the evaluation set that name a jurisdiction, with the expected labels.
GOLD = [
    ("Qu'est ce qu'une forêt au sens de la FAO ?", FAO),
    ("Qu'est ce qu'une forêt au sens de l'UNFCCC ?", UNFCCC),
    ("Est ce qu'une plantation forestière est une forêt au sens de l'UNFCCC ?", UNFCCC),
    ("Donne moi la définition de la forêt s'adossant à la définition de l'UNFCCC en Albanie", ["Albania"]),
    ("Donne moi la définition de la forêt s'adossant à la définition de l'UNFCCC au Ghana", ["Ghana"]),
    ("Donne moi la définition de la forêt s'adossant à la définition de l'UNFCCC au Brésil", ["Brazil"]),
    ("Est ce que la FAO considère la forêt urbaine comme étant une forêt ?", FAO),
    ("Est ce que l'UNFCCC considère la forêt urbaine comme étant une forêt ?", UNFCCC),
]

GRAPH_QUERY = """
PREFIX :     <http://example.org/forest#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?def ?text ?jurisdiction WHERE {{
    ?def a :Definition ; :defines :Forest ; :definitionText ?text ; :appliesIn ?j .
    ?j rdfs:label ?jurisdiction .
    FILTER(?jurisdiction IN ({labels}))
}} ORDER BY ?def LIMIT {k}
"""


class GraphFilterRetriever:
    """Exact jurisdiction filter in SPARQL (what the knowledge graph makes possible)."""
    name = "graph"

    def __init__(self, endpoint: str):
        self.endpoint = endpoint

    def search(self, query: str, k: int, expected: list[str]) -> list[SearchHit]:
        labels = ", ".join(f'"{label}"' for label in expected)
        bindings, error = execute_sparql(self.endpoint, GRAPH_QUERY.format(labels=labels, k=k))
        if error:
            raise RuntimeError(error)
        return [
            SearchHit(
                DefinitionDoc(b["def"]["value"].split("#")[-1], b["text"]["value"], "Forest",
                              b["jurisdiction"]["value"], ""),
                1.0, r + 1, self.name,
            )
            for r, b in enumerate(bindings)
        ]


def evaluate(retrievers: dict, k: int) -> tuple[dict, list[str]]:
    summary = {name: {"precision": [], "latency_ms": [], "wrong": {}} for name in retrievers}
    details = []
    for question, expected in GOLD:
        details.append(f"\n### {question}\nAttendu : {', '.join(expected)}\n")
        for name, retriever in retrievers.items():
            start = time.perf_counter()
            if name == "graph":
                hits = retriever.search(question, k, expected)
            else:
                hits = retriever.search(question, k)
            latency = (time.perf_counter() - start) * 1000

            good = [h for h in hits if h.doc.jurisdiction in expected]
            precision = len(good) / len(hits) if hits else 0.0  # some countries have < k definitions
            summary[name]["precision"].append(precision)
            summary[name]["latency_ms"].append(latency)
            for h in hits:
                if h.doc.jurisdiction not in expected:
                    summary[name]["wrong"][h.doc.jurisdiction] = summary[name]["wrong"].get(h.doc.jurisdiction, 0) + 1
            got = ", ".join(h.doc.jurisdiction for h in hits) or "(aucun résultat)"
            details.append(f"- **{name}** : {precision:.0%} — {got}")
    return summary, details


def render(summary: dict, details: list[str], k: int) -> str:
    lines = [
        "# Comparaison des retrievers : graphe vs RAG vectoriel",
        "",
        f"Jeu : {len(GOLD)} questions de l'évaluation qui citent un pays ou un organisme. "
        f"Métrique : part des définitions retournées (k = {k} au maximum) qui viennent de la bonne juridiction.",
        "",
        f"| Retriever | Précision juridiction@{k} | Latence médiane (ms) | Juridictions hors sujet les plus fréquentes |",
        "| --- | --- | --- | --- |",
    ]
    for name, s in summary.items():
        wrong = sorted(s["wrong"].items(), key=lambda kv: kv[1], reverse=True)[:3]
        wrong_txt = ", ".join(f"{j} ({n})" for j, n in wrong) or "aucune"
        lines.append(
            f"| {name} | {statistics.mean(s['precision']):.0%} | "
            f"{statistics.median(s['latency_ms']):.1f} | {wrong_txt} |"
        )
    lines += ["", "## Détail par question", *details, ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--endpoint", default="local", help='"local" (Turtle file) or a Fuseki SPARQL URL')
    parser.add_argument("-k", type=int, default=5)
    parser.add_argument("--out", default="reports/retrieval_comparison.md")
    parser.add_argument("--no-dense", action="store_true",
                        help="only graph + BM25 (no embedding model download)")
    args = parser.parse_args()

    retrievers = {"graph": GraphFilterRetriever(args.endpoint)}
    if args.no_dense:
        from vector.corpus import load_definitions
        from vector.index import BM25Index

        retrievers["bm25"] = BM25Index(load_definitions(args.endpoint))
    else:
        retrievers.update(build_retrievers(args.endpoint))
    summary, details = evaluate(retrievers, args.k)
    report = render(summary, details, args.k)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(report, encoding="utf-8")
    print(report.split("## Détail")[0])
    print(f"Rapport complet : {args.out}")


if __name__ == "__main__":
    main()
