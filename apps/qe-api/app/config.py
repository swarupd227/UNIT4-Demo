from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="QE_")

    database_url: str = "postgresql+psycopg://qe:qe@qe-db:5432/qe"
    llm_mode: Literal["replay", "live"] = "replay"
    llm_model: str = "claude-opus-5-5"
    # The module's repository, test estate and answer key, as mounted in the container.
    estate_root: str = "/workspace/qe/estate"
    history_repo: str = "/workspace/qe/history/repo"
    answer_key: str = "/workspace/qe/answer-key"
    # Demo setting for the MOSAIC coverage gate. Unit4's real gate rule is a discovery item.
    gate_percent: int = 80


@lru_cache
def get_settings() -> Settings:
    return Settings()
