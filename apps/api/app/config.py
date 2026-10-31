from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="STUDIO_")

    database_url: str = "postgresql+psycopg://studio:studio@db:5432/studio"
    llm_mode: Literal["replay", "live"] = "replay"
    storage_root: str = "/workspace/storage"


@lru_cache
def get_settings() -> Settings:
    return Settings()
