from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class Settings(BaseSettings):
    environment: Literal["development", "test", "production"] = "development"
    database_url: str = ""

    model_config = SettingsConfigDict(
        env_prefix="TUTORING_",
        env_file=".env",
        extra="forbid",
    )

    @model_validator(mode="after")
    def require_database_boundary(self) -> "Settings":
        if self.database_url:
            database_url = self.database_url
        elif self.environment == "development":
            self.database_url = "sqlite:///backend/var/tutoring.sqlite3"
            database_url = self.database_url
        else:
            raise ValueError("database_url is required outside development")

        parsed_url = make_url(database_url)
        if parsed_url.drivername.startswith("sqlite") and parsed_url.database not in {
            None,
            "",
            ":memory:",
        }:
            repository = Path.cwd().resolve()
            database_path = Path(parsed_url.database).resolve()
            ignored_development_directory = (repository / "backend" / "var").resolve()
            if database_path.is_relative_to(repository) and not database_path.is_relative_to(
                ignored_development_directory
            ):
                raise ValueError("database path must not be tracked or frontend-served")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
