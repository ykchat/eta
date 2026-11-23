from pathlib import Path
from datetime import datetime, timezone
import sqlite3
from typing import Self

from eta import config
from eta.models import Source, Operator

SQLITE_FILE_NAME = "eta.sqlite3"

SCHEMA_VERSION = 26112301

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS operators (
    id        TEXT PRIMARY KEY,   -- id of Operator
    source_id TEXT NOT NULL,      -- id of Source
    operator  TEXT NOT NULL       -- json of Operator
);
CREATE TABLE IF NOT EXISTS updates (
    table_name  TEXT NOT NULL,            -- name of Table
    source_id   TEXT NOT NULL,            -- id of Sourc
    updated_at  TEXT NOT NULL,            -- ISO 8601(UTC)
    PRIMARY KEY (table_name, source_id)
);
"""

DROP_SQL = """
DROP TABLE IF EXISTS operators;
DROP TABLE IF EXISTS updates;
"""

GET_SOURCES_SQL = """
SELECT updates.source_id, COUNT(operators.id), updates.updated_at
FROM updates
LEFT JOIN operators ON operators.source_id = updates.source_id
WHERE updates.table_name = 'operators'
GROUP BY updates.source_id
ORDER BY updates.source_id
"""

class SQLiteStaticDB:

    def __init__(self: Self, path: Path | None = None) -> None:

        path = path or config.path_db(SQLITE_FILE_NAME)
        self._connection = sqlite3.connect(path)
        self.prepare()

    def prepare(self: Self) -> None:

        (version,) = self._connection.execute("PRAGMA user_version").fetchone()

        if version != SCHEMA_VERSION:
            self._connection.executescript(DROP_SQL)
            self._connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

        self._connection.executescript(CREATE_SQL)

    def connection(self: Self) -> sqlite3.Connection:

        return self._connection

    def get_sources(self) -> list[Source]:

        sources = self.connection().execute(GET_SOURCES_SQL).fetchall()

        return [
            Source.model_validate({"id": id, "operator_count": operators, "updated_at": updated_at})
            for id, operators, updated_at in sources
        ]

    def get_operators(self: Self) -> list[Operator]:

        operators = self._connection.execute("SELECT operator FROM operators ORDER BY id").fetchall()

        return [
            Operator.model_validate_json(operator)
            for (operator,) in operators
        ]

    def save_operators(self: Self, source_id: str, operators: list[Operator]) -> None:

        self._connection.execute("DELETE FROM operators WHERE source_id = ?", (source_id,))

        self._connection.executemany(
            "INSERT INTO operators (id, source_id, operator) VALUES (?, ?, ?)",
            [(operator.id, source_id, operator.model_dump_json()) for operator in operators],
        )

        self._connection.execute(
            "INSERT OR REPLACE INTO updates (table_name, source_id, updated_at) VALUES ('operators', ?, ?)",
            (source_id, datetime.now(timezone.utc).isoformat()),
        )