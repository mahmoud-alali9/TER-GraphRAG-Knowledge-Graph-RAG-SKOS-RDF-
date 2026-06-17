"""CLI: ask questions interactively against the Forest GraphRAG pipeline."""
import os
from pathlib import Path

from dotenv import load_dotenv

from workflow.config import WorkflowConfig
from workflow.pipeline import ForestGraphRAGPipeline

load_dotenv()

if __name__ == "__main__":
    pipeline = ForestGraphRAGPipeline(
        config=WorkflowConfig(
            endpoint=os.getenv("SPARQL_ENDPOINT", "http://localhost:3030/forestKG/sparql"),
            output_dir=Path(os.getenv("OUTPUT_DIR", "outputs")),
            timeout=int(os.getenv("WORKFLOW_TIMEOUT", "120")),
        )
    )
    while True:
        question = input("Question: ").strip()
        if question.lower() in {"exit", "quit", "q"}:
            break
        if question:
            result = pipeline.query(question)
            print(result.get("answer", result))
