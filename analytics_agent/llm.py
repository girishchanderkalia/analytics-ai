from functools import lru_cache

from langchain_openai import AzureChatOpenAI

from analytics_agent.config import get_api_key, get_settings


@lru_cache
def get_llm() -> AzureChatOpenAI:
    """The ASML gateway speaks the Azure OpenAI dialect, so the Azure client fits natively."""
    settings = get_settings()
    return AzureChatOpenAI(
        azure_endpoint=settings.base_url,
        azure_deployment=settings.deployment,
        api_version=settings.api_version,
        api_key=get_api_key(),
        temperature=settings.temperature,
    )
