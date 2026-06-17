from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    # Pipeline
    sparql_endpoint : str       = "http://localhost:3030/forestKG/sparql"
    output_dir      : Path      = Path("outputs")
    workflow_timeout: int       = 120

    # Evaluation
    db_path         : str       = "graph_rag_eval.db"
    logger_enabled  : bool      = True
    ragas_model     : str       = "gpt-4o-mini"
    ragas_metrics   : list[str] = field(default_factory=lambda: [
        "faithfulness",
        "context_recall",
        "context_precision",
        "factual_correctness",
        "semantic_similarity",
    ])

    # Security
    admin_password  : str       = ""


def load_settings() -> Settings:
    return Settings(
        sparql_endpoint  = os.getenv("SPARQL_ENDPOINT",   Settings.sparql_endpoint),
        output_dir       = Path(os.getenv("OUTPUT_DIR",   str(Settings.output_dir))),
        workflow_timeout = int(os.getenv("WORKFLOW_TIMEOUT", str(Settings.workflow_timeout))),
        db_path          = os.getenv("DB_PATH",           Settings.db_path),
        logger_enabled   = os.getenv("LOGGER_ENABLED", "true").lower() not in {"0", "false", "no"},
        ragas_model      = os.getenv("RAGAS_MODEL",       Settings.ragas_model),
        admin_password   = os.getenv("ADMIN_PASSWORD",    ""),
    )
