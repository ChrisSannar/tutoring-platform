from collections.abc import Iterator
from contextlib import contextmanager
from typing import Literal

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine
from sqlalchemy.engine import Connection
from sqlalchemy.exc import SQLAlchemyError


@contextmanager
def db_connection(
    database_url: str, *, mode: Literal["read", "write", "immediate"] = "write"
) -> Iterator[Connection]:
    """Yield a connection, always disposing the engine.

    read: plain connect. write: commit on success, rollback on exception.
    immediate: BEGIN IMMEDIATE and commit on success.
    """
    engine = create_engine(database_url)
    try:
        if mode == "read":
            with engine.connect() as connection:
                yield connection
        elif mode == "immediate":
            connection = engine.connect()
            try:
                connection.exec_driver_sql("BEGIN IMMEDIATE")
                yield connection
                if connection.in_transaction():
                    connection.commit()
            except Exception:
                if connection.in_transaction():
                    connection.rollback()
                raise
            finally:
                connection.close()
        else:
            with engine.begin() as connection:
                yield connection
    finally:
        engine.dispose()


def readiness_status(database_url: str) -> str:
    try:
        with db_connection(database_url, mode="read") as connection:
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
