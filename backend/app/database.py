from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError


def readiness_status(database_url: str) -> str:
    engine = create_engine(database_url)
    try:
        try:
            with engine.connect() as connection:
                current_revision = MigrationContext.configure(
                    connection
                ).get_current_revision()
        except SQLAlchemyError:
            return "database"

        alembic_config = Config("backend/alembic.ini")
        expected_revision = ScriptDirectory.from_config(
            alembic_config
        ).get_current_head()
        if current_revision == expected_revision:
            return "ready"
        return "schema"
    finally:
        engine.dispose()
