"""Integration test: speed test result flows into SQLite and dashboard refresh."""

import time

import pytest
from PySide6.QtWidgets import QApplication

from app.services.speed_test import SpeedTestResult
from app.ui.main_window import MainWindow


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def _wait_until(condition, timeout=30.0):
    start = time.time()
    while not condition():
        if time.time() - start > timeout:
            raise TimeoutError("condition not met within timeout")
        QApplication.processEvents()
        time.sleep(0.05)


def make_speedtest_mock():
    from app.services.speed_test import ServerInfo

    server = ServerInfo(
        id="srv-1",
        name="Integration City",
        sponsor="Integration ISP",
        country="US",
        host="int.example.com:8080",
    )
    return server


def make_speedtest_client_mock(download_bps=40_000_000, upload_bps=15_000_000):
    from unittest.mock import MagicMock

    mock = MagicMock()
    mock.download.return_value = download_bps
    mock.upload.return_value = upload_bps
    return mock


def test_end_to_end_speed_test_saved(qapp, monkeypatch, tmp_path):
    from app.services import speed_test as st_mod

    # No real network.
    monkeypatch.setattr(st_mod, "check_connectivity", lambda timeout=5.0: True)
    monkeypatch.setattr(
        st_mod.SpeedTestService,
        "_select_server",
        lambda self: make_speedtest_mock(),
    )
    monkeypatch.setattr(
        st_mod,
        "ping_host",
        lambda host, count=4, timeout=3.0: {
            "success": True,
            "packets_sent": count,
            "packets_received": count,
            "avg_ms": 20.0,
            "min_ms": 18.0,
            "max_ms": 22.0,
            "jitter_ms": 1.5,
            "packet_loss_percent": 0.0,
            "raw": "",
            "error": None,
        },
    )
    monkeypatch.setattr("speedtest.Speedtest", lambda timeout=60: make_speedtest_client_mock())

    window = MainWindow()
    # Swap the repo for a temp-file one so we don't touch the real app DB.
    from app.database.db import Database
    temp_db = Database(str(tmp_path / "integration.db"))
    from app.database.repository import SpeedTestRepository
    window._repo = SpeedTestRepository(temp_db)

    speed_page = window._pages["speed_test"]

    result_holder = {}

    def on_completed(result: SpeedTestResult):
        result_holder["result"] = result
        window._repo.insert(result.to_dict())
        window._pages["dashboard"].refresh()
        window._pages["history"].refresh()

    speed_page.test_completed.disconnect()
    speed_page.test_completed.connect(on_completed)

    speed_page.start_test()
    _wait_until(lambda: result_holder.get("result") is not None, timeout=60.0)

    result = result_holder["result"]
    assert result.status == "completed"
    assert result.download_mbps == 40.0
    assert result.upload_mbps == 15.0
    assert result.server is not None
    assert result.server.name == "Integration City"

    # Verify persisted in SQLite.
    records = window._repo.fetch_all()
    assert len(records) == 1
    assert records[0]["download_mbps"] == 40.0
    assert records[0]["server_name"] == "Integration City"

    latest = window._repo.latest()
    assert latest is not None and latest["download_mbps"] == 40.0

    temp_db.close()
    window.close()
