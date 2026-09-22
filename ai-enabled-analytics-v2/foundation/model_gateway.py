"""Platform capability: a PydanticAI-compatible model factory, no OPO semantics.

Phase 1 of PLAN.md replaces raw ``AzureChatOpenAI.with_structured_output(...)``
calls with typed ``pydantic_ai.Agent`` definitions (see
``agent_runtime/application_agent/agents.py``). This module only builds the
underlying model object; prompts, output schemas, and business logic live in the
application agent layer.
"""

from functools import lru_cache

from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.azure import AzureProvider

from foundation.config import get_api_key, get_settings


#@lru_cache
def get_model() -> OpenAIChatModel:
    """Platform capability: connects any application agent to the hosted model.

    The ASML gateway speaks the Azure OpenAI dialect, so the Azure provider fits
    natively. Returned model is framework-neutral: any ``pydantic_ai.Agent`` can
    use it regardless of its output type.
    """
    settings = get_settings()
    provider = AzureProvider(
        azure_endpoint=settings.base_url,
        api_version=settings.api_version,
        api_key=get_api_key(),
    )
    return OpenAIChatModel(settings.deployment, provider=provider)
