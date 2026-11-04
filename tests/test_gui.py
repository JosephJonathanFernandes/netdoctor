"""GUI tests for NetDoctor using pytest-qt."""

import pytest
from PySide6.QtWidgets import QApplication

from app.ui.main_window import MainWindow


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_main_window_creation(app, qtbot):
    """Verify the main window instantiates with all 6 pages."""
    window = MainWindow()
    qtbot.addWidget(window)

    expected = ["dashboard", "speed_test", "monitor", "history", "diagnostics", "settings"]
    for key in expected:
        assert key in window._pages, f"missing page: {key}"

    assert window._tray is not None
    assert window._notification_service is not None
    window.close()


def test_navigate_between_pages(app, qtbot):
    """Verify navigation switches the stacked widget page."""
    window = MainWindow()
    qtbot.addWidget(window)

    window._show_speed_test()
    assert window._stack.currentWidget() is window._pages["speed_test"]

    window._show_dashboard()
    assert window._stack.currentWidget() is window._pages["dashboard"]

    window._show_history()
    assert window._stack.currentWidget() is window._pages["history"]

    window.close()


def test_dashboard_refresh(app, qtbot):
    """Verify dashboard refreshes without crashing."""
    window = MainWindow()
    qtbot.addWidget(window)

    dashboard = window._pages["dashboard"]
    dashboard.refresh()  # should not raise with empty DB
    window.close()


def test_settings_theme_toggle(app, qtbot):
    """Verify settings page applies theme changes."""
    window = MainWindow()
    qtbot.addWidget(window)

    settings = window._pages["settings"]
    settings.theme_combo.setCurrentIndex(1)  # Light
    settings._apply_theme()
    assert window._dark is False

    settings.theme_combo.setCurrentIndex(0)  # Dark
    settings._apply_theme()
    assert window._dark is True

    window.close()
