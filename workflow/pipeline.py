from __future__ import annotations

import asyncio

from workflow.config import WorkflowConfig
from workflow.prompts import DEFAULT_MODE, get_prompt
from workflow.steps import ForestRAGWorkflow
from workflow.tools import WorkflowTools
from workflow.tracing import traceable


class ForestGraphRAGPipeline:
    def __init__(self, *, config: WorkflowConfig, tools: WorkflowTools | None = None):
        self.config = config
        self.tools = tools or WorkflowTools()
        self.labels = self.tools.load_labels(config.endpoint)

    @traceable(name="forest_graphrag", run_type="chain")
    async def aquery(self, question: str, *, mode: str = DEFAULT_MODE) -> dict:
        system_prompt, temperature = get_prompt(mode)
        workflow = ForestRAGWorkflow(config=self.config, labels=self.labels, tools=self.tools)
        return await workflow.run(
            question=question,
            system_prompt=system_prompt,
            temperature=temperature,
        )

    def query(self, question: str, *, mode: str = DEFAULT_MODE) -> dict:
        return asyncio.run(self.aquery(question, mode=mode))
