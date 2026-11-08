"""Database backup and restore for NetDoctor.

Creates timestamped copies of the SQLite database (including WAL/SHM sidecars)
and can restore from a previously created backup.
"""

from __future__ import annotations

import os
import shutil
import sqlite3
from datetime import UTC, datetime

from app.config import get_default_db_path
from app.exceptions import DatabaseError
from app.utils.logging import get_logger

logger = get_logger(__name__)


class BackupService:
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or get_default_db_path()

    def list_backups(self, backup_dir: str | None = None) -> list[dict]:
        """Return available backups sorted newest first."""
        backup_dir = backup_dir or self._default_backup_dir()
        os.makedirs(backup_dir, exist_ok=True)
        backups = []
        for entry in os.listdir(backup_dir):
            if entry.startswith("netdoctor_backup_") and entry.endswith(".db"):
                full = os.path.join(backup_dir, entry)
                try:
                    stat = os.stat(full)
                    backups.append({
                        "path": full,
                        "name": entry,
                        "created": datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat(),
                        "size_bytes": stat.st_size,
                    })
                except OSError:
                    continue
        backups.sort(key=lambda b: b["created"], reverse=True)
        return backups

    def create_backup(self, backup_dir: str | None = None) -> str:
        """Create a consistent backup of the SQLite database using the backup API.

        Returns the path to the created backup file.
        """
        backup_dir = backup_dir or self._default_backup_dir()
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"netdoctor_backup_{timestamp}.db")

        try:
            source = sqlite3.connect(self.db_path)
            dest = sqlite3.connect(backup_path)
            with dest:
                source.backup(dest)
            source.close()
            dest.close()
            logger.info("Database backup created: %s", backup_path)
            return backup_path
        except sqlite3.Error as exc:
            logger.exception("Backup failed")
            raise DatabaseError(f"Failed to create backup: {exc}") from exc

    def restore_backup(self, backup_path: str) -> None:
        """Restore the database from a backup file.

        The current database is replaced. All connections should be closed
        before calling this.
        """
        if not os.path.exists(backup_path):
            raise DatabaseError(f"Backup file not found: {backup_path}")
        # Verify it's a valid SQLite database
        try:
            test = sqlite3.connect(backup_path)
            test.execute("SELECT count(*) FROM speed_tests")
            test.close()
        except sqlite3.Error as exc:
            raise DatabaseError(f"Invalid backup file: {exc}") from exc

        # Replace current DB
        try:
            if os.path.exists(self.db_path):
                shutil.copy2(self.db_path, self.db_path + ".pre_restore.bak")
            shutil.copy2(backup_path, self.db_path)
            # Remove WAL/SHM so SQLite rebuilds them
            for ext in ("-wal", "-shm"):
                p = self.db_path + ext
                if os.path.exists(p):
                    os.remove(p)
            logger.info("Database restored from %s", backup_path)
        except OSError as exc:
            logger.exception("Restore failed")
            raise DatabaseError(f"Failed to restore backup: {exc}") from exc

    def _default_backup_dir(self) -> str:
        app_dir = os.path.dirname(get_default_db_path())
        return os.path.join(app_dir, "backups")
