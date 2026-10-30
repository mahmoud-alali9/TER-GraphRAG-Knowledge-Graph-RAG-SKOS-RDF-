"""Optional LangSmith tracing for the pipeline.

Tracing is OFF unless both variables are set (for example in .env):

    LANGSMITH_TRACING=true
    LANGSMITH_API_KEY=lsv2_...
    LANGSMITH_PROJECT=forest-graphrag      # optional

When it is on, every question becomes one trace in LangSmith with a child run per
step (jurisdiction linking, planning, retrieval, LLM calls), with inputs, outputs,
latency and errors. When it is off, ``traceable`` returns the function unchanged,
so the pipeline has no dependency on LangSmith.
"""
from __future__ import annotations

import os


def tracing_enabled() -> bool:
    flag = os.getenv("LANGSMITH_TRACING", os.getenv("LANGCHAIN_TRACING_V2", "")).lower()
    has_key = bool(os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY"))
    return flag == "true" and has_key


def traceable(name: str | None = None, run_type: str = "chain"):
    """Decorator: a LangSmith run when tracing is enabled, a no-op otherwise."""
    def decorator(func):
        if not tracing_enabled():
            return func
        try:
            from langsmith import traceable as ls_traceable
        except ImportError:
            return func
        return ls_traceable(name=name or func.__name__, run_type=run_type)(func)

    return decorator
