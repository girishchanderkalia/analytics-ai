"""Foundation-wide settings: model gateway, PostgreSQL runtime state, MCP transport."""

import concurrent.futures
from functools import lru_cache

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from pydantic_settings import BaseSettings, SettingsConfigDict

KEY_VAULT_FETCH_TIMEOUT_SECONDS = 10


class FoundationSettings(BaseSettings):
    """Connection settings for the platform-hosted model gateway and runtime state."""

    model_config = SettingsConfigDict(env_prefix="ASML_AI_")

    base_url: str = "https://platform.ai.asml.com"
    deployment: str = "mistral-large-3-ssa"
    api_version: str = "2024-10-21"
    temperature: float = 0.2

    key_vault_url: str = "https://ssa-prd-proj-15528-01-kv.vault.azure.net/"
    secret_name: str = "ssa-ai-key"

    # Direct override for environments with no reachable managed/workload identity
    # (e.g. this on-prem cluster's IMDS probe always times out): when set, get_api_key()
    # returns this value and skips DefaultAzureCredential/Key Vault entirely.
    api_key: str | None = None

    # Single PostgreSQL runtime-state store: LangGraph checkpoints live in tables
    # created by PostgresSaver.setup(); session/audit/memory tables are created by
    # db/schema.sql. Same database, separate table groups (see PLAN.md Phase 2).
    database_url: str = "postgresql://postgres:postgres@localhost:5432/ai_enabled_analytics_v2"

    # Local dev transport for the MCP capability adaptor: "stdio" (default, simplest
    # for a single-process dev loop) or "streamable-http" (separate MCP processes).
    mcp_transport: str = "stdio"
    mcp_starrocks_http_url: str = "http://127.0.0.1:8801/mcp"
    mcp_analytics_api_http_url: str = "http://127.0.0.1:8802/mcp"


@lru_cache
def get_settings() -> FoundationSettings:
    return FoundationSettings()


# Module-level and never shut down on purpose: a `with ThreadPoolExecutor(...)`
# blocks on `__exit__` (`shutdown(wait=True)`) until its submitted work
# finishes, which would silently defeat the `future.result(timeout=...)` below
# whenever the Key Vault fetch itself hangs - the whole point of this executor.
_KEY_VAULT_EXECUTOR = concurrent.futures.ThreadPoolExecutor(
    max_workers=2, thread_name_prefix="key-vault-fetch"
)


@lru_cache
def get_api_key() -> str:
    """Read the gateway key from the Key Vault behind Databricks scope lis-analytics-15528.

    Bounded by a hard timeout: `DefaultAzureCredential`'s managed-identity/IMDS
    probe can otherwise hang for minutes with no reachable Azure endpoint (e.g.
    no identity configured for this pod in-cluster), which would hang whichever
    request triggered it instead of failing fast into the caller's fallback path.
    """
    settings = get_settings()
    if settings.api_key:
        return settings.api_key
    client = SecretClient(
        vault_url=settings.key_vault_url,
        # Picks up the local `az login` session, or a managed identity when deployed
        credential=DefaultAzureCredential(),
    )

    def _fetch_secret() -> str:
        return client.get_secret(settings.secret_name).value

    future = _KEY_VAULT_EXECUTOR.submit(_fetch_secret)
    try:
        return future.result(timeout=KEY_VAULT_FETCH_TIMEOUT_SECONDS)
    except concurrent.futures.TimeoutError as exc:
        raise TimeoutError(
            f"Key Vault secret fetch for {settings.secret_name!r} did not complete within "
            f"{KEY_VAULT_FETCH_TIMEOUT_SECONDS}s (no reachable credential source, e.g. no "
            "managed/workload identity configured for this pod)"
        ) from exc
