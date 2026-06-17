from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI

from app.db import EvaluationDB
from app.ragas_runner import RagasRunner
from app.routes import router
from app.service import EvaluationService
from config import load_settings
from workflow.config import WorkflowConfig
from workflow.pipeline import ForestGraphRAGPipeline


def create_app() -> FastAPI:
    settings = load_settings()
    app = FastAPI(title="Forest GraphRAG API")

    db = EvaluationDB(settings.db_path)
    ragas_runner = RagasRunner(metrics=settings.ragas_metrics, llm_model=settings.ragas_model)
    app.state.eval_service = EvaluationService(db=db, ragas_runner=ragas_runner, logger_enabled=settings.logger_enabled)
    app.state.pipeline = ForestGraphRAGPipeline(
        config=WorkflowConfig(
            endpoint=settings.sparql_endpoint,
            output_dir=settings.output_dir,
            timeout=settings.workflow_timeout,
        )
    )
    app.state.ragas_executor = ThreadPoolExecutor(max_workers=1)
    app.state.admin_password = settings.admin_password

    app.include_router(router)
    return app


app = create_app()
