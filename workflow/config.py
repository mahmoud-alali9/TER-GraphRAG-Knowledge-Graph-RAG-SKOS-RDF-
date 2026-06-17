from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

try:
    from llama_index.core.workflow import Event
except ImportError as exc:
    raise ImportError(
        "llama-index-core is required. Install with `pip install -r requirements.txt`."
    ) from exc


@dataclass(frozen=True)
class WorkflowConfig:
    endpoint: str
    output_dir: Path
    timeout: int = 120


@dataclass(frozen=True)
class PipelineResult:
    question: str
    intent: str
    sparql_query: str
    context: str
    answer: str
    output_path: str

    def to_dict(self) -> dict:
        return {
            "question": self.question,
            "intent": self.intent,
            "sparql_query": self.sparql_query,
            "context": self.context,
            "answer": self.answer,
            "output_path": self.output_path,
        }


class PreparedInputEvent(Event):
    question: str


class LinkedJurisdictionEvent(Event):
    question: str
    resolved_jurisdictions: list[str]


class PlannedQueryEvent(Event):
    question: str
    plan: dict
    resolved_jurisdictions: list[str]


class RetrievedContextInputEvent(Event):
    question: str
    plan: dict
    resolved_jurisdictions: list[str]


class RetrievedContextEvent(Event):
    question: str
    intent: str
    sparql_query: str
    context: str


class GeneratedAnswerEvent(Event):
    question: str
    intent: str
    sparql_query: str
    context: str
    answer: str
