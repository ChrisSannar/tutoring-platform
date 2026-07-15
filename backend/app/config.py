from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: Literal["development", "test", "production"] = "development"

    model_config = SettingsConfigDict(
        env_prefix="TUTORING_",
        env_file=".env",
        extra="forbid",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
