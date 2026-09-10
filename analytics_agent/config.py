from functools import lru_cache

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ASML_AI_")

    base_url: str = "https://platform.ai.asml.com"
    deployment: str = "mistral-large-3-ssa"
    api_version: str = "2024-10-21"
    temperature: float = 0.2

    key_vault_url: str = "https://ssa-prd-proj-15528-01-kv.vault.azure.net/"
    secret_name: str = "ssa-ai-key"

    checkpoint_db: str = "checkpoints.sqlite"


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_api_key() -> str:
    """Read the gateway key from the Key Vault behind Databricks scope lis-analytics-15528."""
    settings = get_settings()
    client = SecretClient(
        vault_url=settings.key_vault_url,
        # Picks up the local `az login` session, or a managed identity when deployed
        credential=DefaultAzureCredential(),
    )
    return client.get_secret(settings.secret_name).value
