"""SQLite database connection and schema management for NetDoctor.

Created automatically on first launch. A schema_version table tracks migrations
so future schema changes can be applied safely.
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from typing import Iterator, Optional

DEFAULT_DB_NAME = "netdoctor.db"


def get_app_data_dir() -> str:
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        return os.path.join(base, "NetDoctor")
    return os.path.join(os.path.expanduser("~"), ".local", "share", "netdoctor")


def get_default_db_path() -> str:
    return os.path.join(get_app_data_dir(), DEFAULT_DB_NAME)


SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS speed_tests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    timestamp_utc TEXT NOT NULL,
    download_mbps REAL,
    upload_mbps REAL,
    latency_ms REAL,
    jitter_ms REAL,
    packet_loss_percent REAL,
    server_name TEXT,
    server_sponsor TEXT,
    server_country TEXT,
    server_host TEXT,
    status TEXT NOT NULL DEFAULT 'completed',
    error_message TEXT,
    note TEXT
);

CREATE TABLE IF NOT EXISTS monitoring_samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    interface_name TEXT,
    bytes_sent INTEGER,
    bytes_recv INTEGER,
    upload_bps REAL,
    download_bps REAL,
    latency_ms REAL
);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    metric TEXT NOT NULL,
    value REAL NOT NULL,
    threshold REAL NOT NULL,
    message TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_speed_tests_timestamp ON speed_tests(timestamp_utc);
CREATE INDEX IF NOT EXISTS idx_monitoring_samples_timestamp ON monitoring_samples(timestamp);
CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp);
"""

LATEST_SCHEMA_VERSION = 1


class Database:
    def __init__(self, db_path: Optional[str] = None):
        from app.config import get_default_db_path as _gdp
        self.db_path = db_path or _gdp()
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        with self.conn:
            self.conn.executescript(SCHEMA)
            cur = self.conn.execute("SELECT version FROM schema_version")
            row = cur.fetchone()
            if row is None:
                self.conn.execute(
                    "INSERT INTO schema_version (version) VALUES (?)",
                    (LATEST_SCHEMA_VERSION,),
                )
            else:
                self._migrate(row["version"])

    def _migrate(self, current_version: int) -> None:
        pass

    @contextmanager
    def cursor(self) -> Iterator[sqlite3.Cursor]:
        try:
            yield self.conn.cursor()
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass


_default_db: Optional[Database] = None


def get_default_database() -> Database:
    global _default_db
    if _default_db is None:
        _default_db = Database()
    return _default_db
