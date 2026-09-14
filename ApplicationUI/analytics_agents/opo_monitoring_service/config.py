from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """App-local runtime settings (not a platform concern)."""

    model_config = SettingsConfigDict(env_prefix="OPO_MONITORING_SERVICE_")

    checkpoint_db: str = "checkpoints.sqlite"


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()
