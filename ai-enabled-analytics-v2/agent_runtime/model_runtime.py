"""Generic model execution for Markdown-defined agents."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

@lru_cache(maxsize=None)
def build_model_agent(system_prompt: str, output_type: type[Any]):
    from foundation.model_gateway import get_model
    from pydantic_ai import Agent

    return Agent(get_model(), output_type=output_type, system_prompt=system_prompt)


def run_structured(system_prompt: str, output_type: type[Any], input_text: str) -> Any:
    result = build_model_agent(system_prompt, output_type).run_sync(input_text)
    return getattr(result, "output", getattr(result, "data", result))
