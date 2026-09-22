from functools import lru_cache

from langchain_openai import AzureChatOpenAI

from AnalyticsFoundation.config import get_api_key, get_settings


@lru_cache
def get_llm() -> AzureChatOpenAI:
    """Platform capability: connects any application agent to the hosted model.

    The ASML gateway speaks the Azure OpenAI dialect, so the Azure client fits natively.
    """
    settings = get_settings()
    return AzureChatOpenAI(
        azure_endpoint=settings.base_url,
        azure_deployment=settings.deployment,
        api_version=settings.api_version,
        api_key=get_api_key(),
        temperature=settings.temperature,
        timeout=settings.request_timeout_s,
        max_retries=0,
    )
