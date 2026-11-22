from pathlib import Path
from datetime import datetime, timezone
import sqlite3
from typing import Self

from eta import config
from eta.models import Operator

DB_FILE_NAME = "eta.sqlite3"

SCHEMA_VERSION = 26112201

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS operators (
    id       TEXT PRIMARY KEY,   -- id of Operator
    operator TEXT NOT NULL       -- json of Operator
);
CREATE TABLE IF NOT EXISTS updates (
    table_name  TEXT NOT NULL,            -- name of Table
    operator_id TEXT NOT NULL DEFAULT '', -- id of Operator
    updated_at  TEXT NOT NULL,            -- ISO 8601(UTC)
    PRIMARY KEY (table_name, operator_id)
);
"""

DROP_SQL = """
DROP TABLE IF EXISTS operators;
DROP TABLE IF EXISTS updates;
"""

class SQLiteStaticDB:

    def __init__(self: Self, path: Path | None = None) -> None:

        path = path or config.path_db(DB_FILE_NAME)
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

    def get_operators(self: Self) -> list[Operator]:

        operators = self._connection.execute("SELECT operator FROM operators ORDER BY id").fetchall()

        return [Operator.model_validate_json(operator) for (operator,) in operators]

    def save_operators(self: Self, operators: list[Operator]) -> None:

        self._connection.execute("DELETE FROM operators")

        self._connection.executemany(
            "INSERT INTO operators (id, operator) VALUES (?, ?)",
            [(operator.id, operator.model_dump_json()) for operator in operators],
        )

        self._connection.execute(
            "INSERT OR REPLACE INTO updates (table_name, operator_id, updated_at) VALUES ('operators', '', ?)",
            (datetime.now(timezone.utc).isoformat(),),
        )        