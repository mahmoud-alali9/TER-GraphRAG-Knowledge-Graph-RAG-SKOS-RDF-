from __future__ import annotations

import asyncio

try:
    from llama_index.core.workflow import StartEvent, StopEvent, Workflow, step
except ImportError as exc:
    raise ImportError(
        "llama-index-core is required. Install with `pip install -r requirements.txt`."
    ) from exc

from workflow.config import (
    GeneratedAnswerEvent,
    LinkedJurisdictionEvent,
    PipelineResult,
    PlannedQueryEvent,
    PreparedInputEvent,
    RetrievedContextEvent,
    RetrievedContextInputEvent,
    WorkflowConfig,
)
from workflow.tools import WorkflowTools


class ForestRAGWorkflow(Workflow):
    def __init__(self, *, config: WorkflowConfig, labels: dict, tools: WorkflowTools | None = None, **kwargs):
        super().__init__(timeout=config.timeout, verbose=False, **kwargs)
        self.config = config
        self.labels = labels
        self.tools = tools or WorkflowTools()
        self._system_prompt: str = ""
        self._temperature: float = 0.1

    @step
    async def prepare_input(self, ev: StartEvent) -> PreparedInputEvent:
        question = ev.question.strip()
        if not question:
            raise ValueError("Question must not be empty.")
        self._system_prompt = ev.system_prompt
        self._temperature = ev.temperature
        return PreparedInputEvent(question=question)

    @step
    async def link_jurisdiction(self, ev: PreparedInputEvent) -> LinkedJurisdictionEvent:
        resolved = await asyncio.to_thread(
            self.tools.link_jurisdictions,
            ev.question,
            self.labels["jurisdictions"],
            self.config.endpoint,
        )
        return LinkedJurisdictionEvent(
            question=ev.question,
            resolved_jurisdictions=resolved,
        )

    @step
    async def plan_query(self, ev: LinkedJurisdictionEvent) -> PlannedQueryEvent:
        plan = await asyncio.to_thread(
            self.tools.create_query_plan,
            ev.question,
            self.labels,
            ev.resolved_jurisdictions,
        )
        return PlannedQueryEvent(
            question=ev.question,
            plan=plan,
            resolved_jurisdictions=ev.resolved_jurisdictions,
        )

    @step
    async def retrieve_context(self, ev: PlannedQueryEvent) -> RetrievedContextEvent:
        context, intent, sparql_query = await asyncio.to_thread(
            self.tools.retrieve_context,
            self.config.endpoint,
            ev.plan,
            ev.resolved_jurisdictions,
            ev.question,
        )
        return RetrievedContextEvent(
            question=ev.question,
            intent=intent,
            sparql_query=sparql_query,
            context=context,
        )

    @step
    async def generate_answer(self, ev: RetrievedContextEvent) -> GeneratedAnswerEvent:
        answer = await asyncio.to_thread(
            self.tools.generate_answer,
            question=ev.question,
            context=ev.context,
            system_prompt=self._system_prompt,
            temperature=self._temperature,
        )
        return GeneratedAnswerEvent(
            question=ev.question,
            intent=ev.intent,
            sparql_query=ev.sparql_query,
            context=ev.context,
            answer=answer,
        )

    @step
    async def finish(self, ev: GeneratedAnswerEvent) -> StopEvent:
        output_path = await asyncio.to_thread(
            self.tools.save_output,
            self.config.output_dir,
            ev.question,
            ev.answer,
            ev.intent,
            ev.context,
        )
        result = PipelineResult(
            question=ev.question,
            intent=ev.intent,
            sparql_query=ev.sparql_query,
            context=ev.context,
            answer=ev.answer,
            output_path=output_path,
        )
        return StopEvent(result=result.to_dict())
