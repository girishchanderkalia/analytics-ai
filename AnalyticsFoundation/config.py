from concurrent.futures import ThreadPoolExecutor, TimeoutError
from functools import lru_cache

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from pydantic_settings import BaseSettings, SettingsConfigDict


class ModelSettings(BaseSettings):
    """Connection settings for the platform-hosted model gateway."""

    model_config = SettingsConfigDict(env_prefix="ASML_AI_")

    base_url: str = "https://platform.ai.asml.com"
    deployment: str = "mistral-large-3-ssa"
    api_version: str = "2024-10-21"
    temperature: float = 0.2
    request_timeout_s: float = 15.0
    api_key: str | None = None

    key_vault_url: str = "https://ssa-prd-proj-15528-01-kv.vault.azure.net/"
    secret_name: str = "ssa-ai-key"
    session_db: str = "agent_sessions.sqlite"


_KEY_VAULT_EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="key-vault")


@lru_cache
def get_settings() -> ModelSettings:
    return ModelSettings()


@lru_cache
def get_api_key() -> str:
    """Read the gateway key from the Key Vault behind Databricks scope lis-analytics-15528."""
    settings = get_settings()
    if settings.api_key:
        return settings.api_key.strip()

    client = SecretClient(
        vault_url=settings.key_vault_url,
        # Picks up the local `az login` session, or a managed identity when deployed
        credential=DefaultAzureCredential(),
    )
    future = _KEY_VAULT_EXECUTOR.submit(client.get_secret, settings.secret_name)
    try:
        return future.result(timeout=settings.request_timeout_s).value
    except TimeoutError as exc:
        raise RuntimeError("Timed out retrieving the model API key from Key Vault") from exc
