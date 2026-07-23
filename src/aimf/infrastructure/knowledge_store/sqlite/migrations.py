"""Schema migrations for the SQLite knowledge store."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable

from aimf.application.knowledge.errors import KnowledgeStoreError, KnowledgeStoreVersionError
from aimf.infrastructure.knowledge_store.defaults import (
    CURRENT_SCHEMA_VERSION,
    SCHEMA_VERSION_KEY,
)
from aimf.infrastructure.knowledge_store.sqlite.schema import (
    SCHEMA_V1_STATEMENTS,
    SCHEMA_V2_STATEMENTS,
)

MigrationFn = Callable[[sqlite3.Connection], None]


def read_schema_version(connection: sqlite3.Connection) -> int | None:
    """Return the stored schema version, or ``None`` if uninitialized."""

    try:
        row = connection.execute(
            "SELECT value FROM schema_metadata WHERE key = ?",
            (SCHEMA_VERSION_KEY,),
        ).fetchone()
    except sqlite3.Error:
        return None
    if row is None:
        return None
    try:
        return int(row[0])
    except (TypeError, ValueError) as error:
        raise KnowledgeStoreVersionError(
            f"Invalid schema_version metadata value: {row[0]!r}"
        ) from error


def set_schema_version(connection: sqlite3.Connection, version: int) -> None:
    """Upsert the schema version metadata row."""

    connection.execute(
        """
        INSERT INTO schema_metadata(key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        (SCHEMA_VERSION_KEY, str(version)),
    )


def migrate_to_v1(connection: sqlite3.Connection) -> None:
    """Create schema version 1 tables and indexes."""

    for statement in SCHEMA_V1_STATEMENTS:
        connection.execute(statement)
    set_schema_version(connection, 1)


def migrate_to_v2(connection: sqlite3.Connection) -> None:
    """Add snapshot, run, and artifact tables for schema version 2."""

    for statement in SCHEMA_V2_STATEMENTS:
        connection.execute(statement)
    set_schema_version(connection, 2)


def apply_migrations(connection: sqlite3.Connection) -> int:
    """Apply pending migrations inside the caller's transaction."""

    current = read_schema_version(connection)
    if current is None:
        current = 0
    if current > CURRENT_SCHEMA_VERSION:
        raise KnowledgeStoreVersionError(
            f"Knowledge store schema version {current} is newer than supported "
            f"version {CURRENT_SCHEMA_VERSION}. Upgrade CodeStrata/AIMF before opening."
        )
    if current == CURRENT_SCHEMA_VERSION:
        return current

    migrations: dict[int, MigrationFn] = {
        1: migrate_to_v1,
        2: migrate_to_v2,
    }

    version = current
    while version < CURRENT_SCHEMA_VERSION:
        next_version = version + 1
        migration = migrations.get(next_version)
        if migration is None:
            raise KnowledgeStoreError(
                f"No migration registered for schema version {next_version}"
            )
        migration(connection)
        version = next_version
        if read_schema_version(connection) != version:
            set_schema_version(connection, version)
    return version


_MIGRATIONS: dict[int, MigrationFn] = {
    1: migrate_to_v1,
    2: migrate_to_v2,
}
