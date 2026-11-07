"""Auto-updater for NetDoctor.

Checks GitHub releases for newer versions, downloads the Windows installer /
portable ZIP, and applies the update. Designed to be safe: it never replaces
the running executable while NetDoctor is active; instead it stages the
download and prompts the user to restart.
"""

from __future__ import annotations

import io
import json
import os
import sys
import zipfile
from dataclasses import dataclass
from typing import Optional

import requests
from PySide6.QtCore import QObject, QThread, Signal

from app.config import APP_VERSION, GITHUB_REPO
from app.exceptions import UpdaterError
from app.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ReleaseInfo:
    """Information about a available GitHub release."""

    version: str
    tag_name: str
    html_url: str
    download_url: Optional[str]
    body: str
    prerelease: bool
    published_at: str


class UpdaterSignals(QObject):
    checked = Signal(object)   # ReleaseInfo | None
    download_progress = Signal(int, int)  # bytes_downloaded, total_bytes
    download_finished = Signal(str)  # file path
    error = Signal(str)


class UpdaterService(QThread):
    """Background service that checks for and downloads updates."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.signals = UpdaterSignals()
        self._check_only = False
        self._target_path: Optional[str] = None

    def check_for_updates(self, prerelease: bool = False) -> None:
        """Start a background check for updates."""
        self._check_only = True
        self.start()

    def download_update(self, release_info: ReleaseInfo) -> None:
        """Start downloading the update asset."""
        self._check_only = False
        self._release_info = release_info
        self.start()

    def run(self) -> None:
        try:
            if self._check_only:
                release = self._fetch_latest_release()
                if release and self._is_newer(release.version):
                    self.signals.checked.emit(release)
                else:
                    self.signals.checked.emit(None)
            else:
                self._perform_download()
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Updater failed")
            self.signals.error.emit(str(exc))

    # -- internals -- #
    def _fetch_latest_release(self) -> Optional[ReleaseInfo]:
        if not GITHUB_REPO:
            return None
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        try:
            resp = requests.get(url, timeout=15, headers={"Accept": "application/vnd.github+json"})
            if resp.status_code != 200:
                return None
            data = resp.json()
            # Find a Windows portable ZIP asset
            asset = None
            for a in data.get("assets", []):
                name = a.get("name", "").lower()
                if name.endswith(".zip") and ("win" in name or "portable" in name or "x64" in name):
                    asset = a
                    break
            if not asset and data.get("assets"):
                asset = data["assets"][0]
            download_url = asset.get("browser_download_url") if asset else None
            return ReleaseInfo(
                version=data.get("tag_name", "").lstrip("v"),
                tag_name=data.get("tag_name", ""),
                html_url=data.get("html_url", ""),
                download_url=download_url,
                body=data.get("body", ""),
                prerelease=bool(data.get("prerelease", False)),
                published_at=data.get("published_at", ""),
            )
        except Exception as exc:  # pragma: no cover - network
            logger.warning("Update check failed: %s", exc)
            return None

    def _is_newer(self, remote_version: str) -> bool:
        try:
            remote = tuple(int(x) for x in remote_version.split(".")[:3])
            local = tuple(int(x) for x in APP_VERSION.split(".")[:3])
            return remote > local
        except ValueError:
            return False

    def _perform_download(self) -> None:
        if not hasattr(self, "_release_info") or not self._release_info.download_url:
            self.signals.error.emit("No download URL available")
            return
        url = self._release_info.download_url
        try:
            with requests.get(url, stream=True, timeout=30) as resp:
                resp.raise_for_status()
                total = int(resp.headers.get("content-length", 0))
                downloaded = 0
                buffer = io.BytesIO()
                for chunk in resp.iter_content(chunk_size=65536):
                    if chunk:
                        buffer.write(chunk)
                        downloaded += len(chunk)
                        self.signals.download_progress.emit(downloaded, total)
                buffer.seek(0)
                # Determine output path next to current executable
                target = self._determine_target_path()
                self._target_path = target
                with open(target, "wb") as fh:
                    fh.write(buffer.read())
                self.signals.download_finished.emit(target)
        except Exception as exc:  # pragma: no cover - network
            logger.exception("Update download failed")
            self.signals.error.emit(str(exc))

    def _determine_target_path(self) -> str:
        exe_dir = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.getcwd()
        return os.path.join(exe_dir, "NetDoctor.update.zip")

    def apply_update(self, zip_path: str) -> None:
        """Extract the update ZIP next to the current installation.

        This does not replace the running EXE (Windows locks it). The user
        must restart NetDoctor to use the new version.
        """
        try:
            exe_dir = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.getcwd()
            backup_dir = os.path.join(exe_dir, "NetDoctor.backup")
            os.makedirs(backup_dir, exist_ok=True)
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(exe_dir)
            logger.info("Update extracted to %s", exe_dir)
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Update apply failed")
            raise UpdaterError(f"Failed to apply update: {exc}") from exc


def check_for_updates_sync() -> Optional[ReleaseInfo]:
    """Synchronous one-shot update check (used by CLI)."""
    if not GITHUB_REPO:
        return None
    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    try:
        resp = requests.get(url, timeout=15, headers={"Accept": "application/vnd.github+json"})
        if resp.status_code != 200:
            return None
        data = resp.json()
        version = data.get("tag_name", "").lstrip("v")
        try:
            remote = tuple(int(x) for x in version.split(".")[:3])
            local = tuple(int(x) for x in APP_VERSION.split(".")[:3])
            if remote <= local:
                return None
        except ValueError:
            pass
        return ReleaseInfo(
            version=version,
            tag_name=data.get("tag_name", ""),
            html_url=data.get("html_url", ""),
            download_url=None,
            body=data.get("body", ""),
            prerelease=bool(data.get("prerelease", False)),
            published_at=data.get("published_at", ""),
        )
    except Exception:
        return None
