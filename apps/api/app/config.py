from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="STUDIO_")

    database_url: str = "postgresql+psycopg://studio:studio@db:5432/studio"
    llm_mode: Literal["replay", "live"] = "replay"
    llm_model: str = "claude-opus-5-5"
    storage_root: str = "/workspace/storage"
    # Blob Storage replaces the local folder when either of these is set.
    blob_account_url: str = ""
    blob_connection_string: str = ""
    blob_container: str = "studio"


@lru_cache
def get_settings() -> Settings:
    return Settings()
