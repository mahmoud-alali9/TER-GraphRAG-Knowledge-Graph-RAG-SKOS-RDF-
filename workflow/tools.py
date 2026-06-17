from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from graph.label_loader import load_all_labels
from workflow.groq_client import ask_llm
from workflow.nerd_linking import find_jurisdiction
from workflow.planner import plan_query
from workflow.prompts import answer_prompt
from workflow.retriever import retrieve


class WorkflowTools:
    def load_labels(self, endpoint: str) -> dict:
        return load_all_labels(endpoint)

    def create_query_plan(self, question: str, labels: dict, resolved_jurisdictions: list[str] = None) -> dict:
        return plan_query(question, labels, resolved_jurisdictions)

    def link_jurisdictions(self, question: str, labels: list[str], endpoint: str) -> list[str]:
        return find_jurisdiction(question, labels, endpoint)

    def retrieve_context(self, endpoint: str, plan: dict, fallback_jurisdictions: list[str], question: str = "") -> tuple[str, str, str]:
        plan = {**plan, "_question": question}
        context, intent, sparql_query = retrieve(endpoint, plan, fallback_jurisdictions)
        return (
            context if context is not None else "NOT_IN_CORPUS",
            intent,
            sparql_query,
        )

    def generate_answer(self, *, question: str, context: str, system_prompt: str, temperature: float) -> str:
        if context == "NOT_IN_CORPUS":
            return (
                "Cette information n'est pas présente dans le corpus de définitions forestières.\n\n"
                "Le corpus contient des définitions nationales et internationales de la forêt "
                "(FAO, UNFCCC/KP, définitions nationales de plus de 150 pays). "
                "Si votre question porte sur une organisation ou un pays spécifique, "
                "veuillez vérifier l'orthographe ou reformuler la question.\n\n"
                "Note : si votre question porte sur l'EUDR (Règlement UE 2023/1115), "
                "ce règlement n'est pas présent dans le corpus actuel."
            )
        return ask_llm(
            answer_prompt(context, question),
            system=system_prompt,
            temperature=temperature,
        )

    def save_output(self, output_dir: Path, question: str, answer: str, intent: str, context: str) -> str:
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", question).strip("_")[:50] or "question"
        path = output_dir / f"{slug}_{timestamp}.txt"
        path.write_text(
            f"QUESTION: {question}\n"
            f"INTENT: {intent}\n"
            f"{'=' * 40}\nCONTEXT:\n{context}\n"
            f"{'=' * 40}\nANSWER:\n{answer}\n",
            encoding="utf-8",
        )
        return str(path)
