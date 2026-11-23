"""Unit tests for the auto-updater service."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.services.updater import ReleaseInfo, check_for_updates_sync


class TestReleaseInfo:
    def test_create(self):
        release = ReleaseInfo(
            version="2.1.0",
            tag_name="v2.1.0",
            html_url="https://github.com/org/repo/releases/tag/v2.1.0",
            download_url="https://github.com/org/repo/releases/download/v2.1.0/NetDoctor.zip",
            body="Bug fixes",
            prerelease=False,
            published_at="2026-01-01T00:00:00Z",
        )
        assert release.version == "2.1.0"
        assert release.prerelease is False


class TestCheckForUpdatesSync:
    @patch("app.services.updater.requests.get")
    def test_no_github_repo(self, mock_get):
        from app.config import GITHUB_REPO
        # Temporarily set to None
        import app.services.updater as updater_mod
        original = updater_mod.GITHUB_REPO
        updater_mod.GITHUB_REPO = None
        try:
            result = check_for_updates_sync()
            assert result is None
        finally:
            updater_mod.GITHUB_REPO = original

    @patch("app.services.updater.requests.get")
    def test_update_available(self, mock_get):
        import app.services.updater as updater_mod
        original = updater_mod.GITHUB_REPO
        updater_mod.GITHUB_REPO = "org/repo"
        try:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "tag_name": "v2.1.0",
                "html_url": "https://github.com/org/repo/releases/tag/v2.1.0",
                "assets": [],
                "body": "Bug fixes",
                "prerelease": False,
                "published_at": "2026-01-01T00:00:00Z",
            }
            mock_get.return_value = mock_response

            result = check_for_updates_sync()
            assert result is not None
            assert result.version == "2.1.0"
            assert result.tag_name == "v2.1.0"
        finally:
            updater_mod.GITHUB_REPO = original

    @patch("app.services.updater.requests.get")
    def test_no_update_available(self, mock_get):
        import app.services.updater as updater_mod
        original = updater_mod.GITHUB_REPO
        updater_mod.GITHUB_REPO = "org/repo"
        try:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "tag_name": "v1.0.0",
                "html_url": "https://github.com/org/repo/releases/tag/v1.0.0",
                "assets": [],
                "body": "",
                "prerelease": False,
                "published_at": "2026-01-01T00:00:00Z",
            }
            mock_get.return_value = mock_response

            result = check_for_updates_sync()
            assert result is None
        finally:
            updater_mod.GITHUB_REPO = original

    @patch("app.services.updater.requests.get")
    def test_api_error(self, mock_get):
        import app.services.updater as updater_mod
        original = updater_mod.GITHUB_REPO
        updater_mod.GITHUB_REPO = "org/repo"
        try:
            mock_get.side_effect = Exception("network error")
            result = check_for_updates_sync()
            assert result is None
        finally:
            updater_mod.GITHUB_REPO = original
