"""Unit tests for the SQLite repository and CSV export."""

import csv
import os
import tempfile

import pytest

from app.database.db import Database
from app.database.repository import (
    MonitoringRepository,
    SpeedTestRepository,
    export_speed_tests_csv,
)


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = Database(path)
    yield db
    db.close()
    os.remove(path)


@pytest.fixture
def repo(temp_db):
    return SpeedTestRepository(temp_db)


def test_insert_and_fetch(repo):
    rid = repo.insert(
        {
            "timestamp": "2026-01-01T12:00:00+00:00",
            "timestamp_utc": "2026-01-01T12:00:00+00:00",
            "download_mbps": 50.5,
            "upload_mbps": 20.2,
            "latency_ms": 25.0,
            "jitter_ms": 3.0,
            "packet_loss_percent": 0.0,
            "server_name": "Test Server",
            "server_sponsor": "Test ISP",
            "server_country": "US",
            "status": "completed",
        }
    )
    assert rid == 1
    records = repo.fetch_all()
    assert len(records) == 1
    assert records[0]["download_mbps"] == 50.5
    assert records[0]["status"] == "completed"


def test_fetch_by_id(repo):
    rid = repo.insert({"timestamp_utc": "2026-01-01T12:00:00+00:00", "status": "completed"})
    rec = repo.fetch_by_id(rid)
    assert rec is not None
    assert rec["id"] == rid
    assert repo.fetch_by_id(9999) is None


def test_delete(repo):
    rid = repo.insert({"timestamp_utc": "2026-01-01T12:00:00+00:00", "status": "completed"})
    assert repo.delete(rid) is True
    assert repo.fetch_by_id(rid) is None
    assert repo.delete(rid) is False


def test_clear_all(repo):
    repo.insert({"timestamp_utc": "2026-01-01T12:00:00+00:00", "status": "completed"})
    repo.insert({"timestamp_utc": "2026-01-02T12:00:00+00:00", "status": "completed"})
    assert repo.clear_all() == 2
    assert repo.fetch_all() == []


def test_stats(repo):
    repo.insert({"timestamp_utc": "2026-01-01T12:00:00+00:00", "download_mbps": 40.0,
                 "upload_mbps": 10.0, "latency_ms": 20.0, "status": "completed"})
    repo.insert({"timestamp_utc": "2026-01-02T12:00:00+00:00", "download_mbps": 60.0,
                 "upload_mbps": 20.0, "latency_ms": 40.0, "status": "completed"})
    stats = repo.stats()
    assert stats["count"] == 2
    assert abs(stats["avg_download"] - 50.0) < 0.01
    assert stats["max_download"] == 60.0
    assert stats["min_download"] == 40.0


def test_latest(repo):
    assert repo.latest() is None
    repo.insert({"timestamp_utc": "2026-01-01T12:00:00+00:00", "download_mbps": 10.0,
                 "status": "completed"})
    latest = repo.latest()
    assert latest is not None
    assert latest["download_mbps"] == 10.0


def test_csv_export(tmp_path, repo):
    repo.insert({"timestamp_utc": "2026-01-01T12:00:00+00:00", "download_mbps": 50.0,
                 "status": "completed"})
    out = tmp_path / "history.csv"
    written = export_speed_tests_csv(str(out), repo.fetch_all())
    assert written == 1
    assert out.exists()
    with open(out, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["download_mbps"] == "50.0"


def test_monitoring_repository(temp_db):
    mrepo = MonitoringRepository(temp_db)
    sid = mrepo.insert_sample(
        {
            "timestamp": "2026-01-01T12:00:00+00:00",
            "bytes_sent": 1000,
            "bytes_recv": 2000,
            "upload_bps": 500.0,
            "download_bps": 1000.0,
            "latency_ms": 20.0,
        }
    )
    assert sid == 1
    samples = mrepo.fetch_recent()
    assert len(samples) == 1
    assert samples[0]["upload_bps"] == 500.0
