"""Desktop notification service for NetDriver.

Uses Windows Toast notifications via win10toast-click when available, falling
back to QSystemTrayIcon.showMessage. Never requires network or user accounts.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import QSystemTrayIcon


class NotificationService:
    def __init__(self, tray_icon: Optional[QSystemTrayIcon] = None):
        self._tray = tray_icon
        self._toaster = None
        self._enabled = True
        try:
            from win10toast import ToastNotifier
            self._toaster = ToastNotifier()
        except Exception:
            self._toaster = None

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled

    def notify(self, title: str, message: str, duration: int = 5) -> None:
        if not self._enabled:
            return
        # Windows toast
        if self._toaster is not None:
            try:
                self._toaster.show_toast(title, message, duration=duration, threaded=True)
                return
            except Exception:
                pass
        # Fallback to tray
        if self._tray is not None:
            try:
                self._tray.showMessage(title, message, QSystemTrayIcon.Information, duration * 1000)
            except Exception:
                pass
