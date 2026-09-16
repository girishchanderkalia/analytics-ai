"""OPO monitoring service settings (v2 BFF)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class OpoMonitoringSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ASML_AI_V2_")

    host: str = "127.0.0.1"
    port: int = 8100


@lru_cache
def get_settings() -> OpoMonitoringSettings:
    return OpoMonitoringSettings()
