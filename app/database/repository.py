"""Data-access repository for NetDoctor persistence."""

from __future__ import annotations

import csv
import json
import os
import sqlite3

from app.database.db import Database, get_default_database
from app.exceptions import DatabaseError


class SpeedTestRepository:
    """Repository for speed-test results."""

    def __init__(self, db: Database | None = None):
        self.db = db or get_default_database()

    def insert(self, result: dict) -> int:
        """Insert a speed-test result and return the new row id."""
        try:
            with self.db.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO speed_tests
                    (timestamp, timestamp_utc, download_mbps, upload_mbps, latency_ms,
                     jitter_ms, packet_loss_percent, server_name, server_sponsor,
                     server_country, server_host, status, error_message, note)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        result.get("timestamp") or result.get("timestamp_utc"),
                        result.get("timestamp_utc"),
                        result.get("download_mbps"),
                        result.get("upload_mbps"),
                        result.get("latency_ms"),
                        result.get("jitter_ms"),
                        result.get("packet_loss_percent"),
                        result.get("server_name"),
                        result.get("server_sponsor"),
                        result.get("server_country"),
                        result.get("server_host"),
                        result.get("status", "completed"),
                        result.get("error_message"),
                        result.get("note"),
                    ),
                )
                return int(cur.lastrowid)
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to insert speed test: {exc}") from exc

    def fetch_all(self, limit: int | None = None) -> list[dict]:
        try:
            with self.db.cursor() as cur:
                if limit is not None:
                    cur.execute(
                        "SELECT * FROM speed_tests ORDER BY timestamp_utc DESC LIMIT ?",
                        (limit,),
                    )
                else:
                    cur.execute("SELECT * FROM speed_tests ORDER BY timestamp_utc DESC")
                return [dict(row) for row in cur.fetchall()]
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to fetch speed tests: {exc}") from exc

    def fetch_by_id(self, test_id: int) -> dict | None:
        try:
            with self.db.cursor() as cur:
                cur.execute("SELECT * FROM speed_tests WHERE id = ?", (test_id,))
                row = cur.fetchone()
                return dict(row) if row else None
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to fetch speed test {test_id}: {exc}") from exc

    def fetch_date_range(self, start_utc: str, end_utc: str) -> list[dict]:
        try:
            with self.db.cursor() as cur:
                cur.execute(
                    """
                    SELECT * FROM speed_tests
                    WHERE timestamp_utc >= ? AND timestamp_utc <= ?
                    ORDER BY timestamp_utc DESC
                    """,
                    (start_utc, end_utc),
                )
                return [dict(row) for row in cur.fetchall()]
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to fetch speed tests by date: {exc}") from exc

    def delete(self, test_id: int) -> bool:
        try:
            with self.db.cursor() as cur:
                cur.execute("DELETE FROM speed_tests WHERE id = ?", (test_id,))
                return cur.rowcount > 0
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to delete speed test {test_id}: {exc}") from exc

    def clear_all(self) -> int:
        try:
            with self.db.cursor() as cur:
                cur.execute("DELETE FROM speed_tests")
                return cur.rowcount
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to clear speed tests: {exc}") from exc

    def stats(self) -> dict:
        try:
            with self.db.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        COUNT(*) AS count,
                        AVG(download_mbps) AS avg_download,
                        AVG(upload_mbps) AS avg_upload,
                        AVG(latency_ms) AS avg_latency,
                        MIN(download_mbps) AS min_download,
                        MAX(download_mbps) AS max_download,
                        MIN(upload_mbps) AS min_upload,
                        MAX(upload_mbps) AS max_upload,
                        MIN(latency_ms) AS min_latency,
                        MAX(latency_ms) AS max_latency
                    FROM speed_tests
                    WHERE status = 'completed'
                    """
                )
                row = cur.fetchone()
                return dict(row) if row else {}
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to compute stats: {exc}") from exc

    def latest(self) -> dict | None:
        try:
            with self.db.cursor() as cur:
                cur.execute(
                    "SELECT * FROM speed_tests WHERE status = 'completed' "
                    "ORDER BY timestamp_utc DESC LIMIT 1"
                )
                row = cur.fetchone()
                return dict(row) if row else None
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to fetch latest speed test: {exc}") from exc

    def recent_series(self, limit: int = 50) -> list[dict]:
        try:
            with self.db.cursor() as cur:
                cur.execute(
                    "SELECT * FROM speed_tests WHERE status = 'completed' "
                    "ORDER BY timestamp_utc ASC LIMIT ?",
                    (limit,),
                )
                return [dict(row) for row in cur.fetchall()]
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to fetch recent series: {exc}") from exc


class MonitoringRepository:
    """Repository for monitoring samples."""

    def __init__(self, db: Database | None = None):
        self.db = db or get_default_database()

    def insert_sample(self, sample: dict) -> int:
        try:
            with self.db.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO monitoring_samples
                    (timestamp, interface_name, bytes_sent, bytes_recv,
                     upload_bps, download_bps, latency_ms)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        sample.get("timestamp"),
                        sample.get("interface_name"),
                        sample.get("bytes_sent"),
                        sample.get("bytes_recv"),
                        sample.get("upload_bps"),
                        sample.get("download_bps"),
                        sample.get("latency_ms"),
                    ),
                )
                return int(cur.lastrowid)
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to insert monitoring sample: {exc}") from exc

    def fetch_recent(self, limit: int = 1000) -> list[dict]:
        try:
            with self.db.cursor() as cur:
                cur.execute(
                    "SELECT * FROM monitoring_samples ORDER BY timestamp DESC LIMIT ?",
                    (limit,),
                )
                return [dict(row) for row in cur.fetchall()]
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to fetch monitoring samples: {exc}") from exc

    def clear_all(self) -> int:
        try:
            with self.db.cursor() as cur:
                cur.execute("DELETE FROM monitoring_samples")
                return cur.rowcount
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to clear monitoring samples: {exc}") from exc


class AlertRepository:
    """Repository for alert records."""

    def __init__(self, db: Database | None = None):
        self.db = db or get_default_database()

    def insert(self, alert: dict) -> int:
        try:
            with self.db.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO alerts (timestamp, metric, value, threshold, message)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        alert.get("timestamp"),
                        alert.get("metric"),
                        alert.get("value"),
                        alert.get("threshold"),
                        alert.get("message"),
                    ),
                )
                return int(cur.lastrowid)
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to insert alert: {exc}") from exc

    def fetch_recent(self, limit: int = 50) -> list[dict]:
        try:
            with self.db.cursor() as cur:
                cur.execute(
                    "SELECT * FROM alerts ORDER BY timestamp DESC LIMIT ?",
                    (limit,),
                )
                return [dict(row) for row in cur.fetchall()]
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to fetch alerts: {exc}") from exc


def export_speed_tests_csv(
    file_path: str, records: list[dict] | None = None
) -> int:
    repo = SpeedTestRepository()
    if records is None:
        records = repo.fetch_all()
    fieldnames = [
        "id", "timestamp", "timestamp_utc", "download_mbps", "upload_mbps",
        "latency_ms", "jitter_ms", "packet_loss_percent", "server_name",
        "server_sponsor", "server_country", "server_host", "status",
        "error_message", "note",
    ]
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    with open(file_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow(record)
    return len(records)


def export_speed_tests_json(
    file_path: str, records: list[dict] | None = None
) -> int:
    repo = SpeedTestRepository()
    if records is None:
        records = repo.fetch_all()
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as fh:
        json.dump(records, fh, indent=2, ensure_ascii=False)
    return len(records)
