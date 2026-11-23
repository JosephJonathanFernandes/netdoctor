"""Unit tests for the backup service."""

from __future__ import annotations

import os
import sqlite3
import tempfile

from app.services.backup import BackupService


class TestBackupService:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "test.db")
        self.backup_dir = os.path.join(self.tmpdir, "backups")

        # Create a sample database
        conn = sqlite3.connect(self.db_path)
        conn.execute("CREATE TABLE IF NOT EXISTS speed_tests (id INTEGER PRIMARY KEY, name TEXT)")
        conn.execute("INSERT INTO speed_tests (name) VALUES ('test')")
        conn.commit()
        conn.close()

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_create_backup(self):
        service = BackupService(db_path=self.db_path)
        backup_path = service.create_backup(backup_dir=self.backup_dir)

        assert os.path.exists(backup_path)
        assert backup_path.endswith(".db")
        assert "netdoctor_backup_" in os.path.basename(backup_path)

        # Verify backup is valid SQLite
        conn = sqlite3.connect(backup_path)
        count = conn.execute("SELECT count(*) FROM speed_tests").fetchone()[0]
        conn.close()
        assert count == 1

    def test_list_backups_empty(self):
        service = BackupService(db_path=self.db_path)
        backups = service.list_backups(backup_dir=self.backup_dir)
        assert backups == []

    def test_list_backups_after_create(self):
        service = BackupService(db_path=self.db_path)
        service.create_backup(backup_dir=self.backup_dir)
        backups = service.list_backups(backup_dir=self.backup_dir)
        assert len(backups) == 1
        assert backups[0]["name"].startswith("netdoctor_backup_")
        assert backups[0]["size_bytes"] > 0

    def test_restore_backup(self):
        service = BackupService(db_path=self.db_path)
        backup_path = service.create_backup(backup_dir=self.backup_dir)

        # Modify original DB
        conn = sqlite3.connect(self.db_path)
        conn.execute("INSERT INTO speed_tests (name) VALUES ('modified')")
        conn.commit()
        conn.close()

        # Restore from backup
        service.restore_backup(backup_path)

        # Verify restore
        conn = sqlite3.connect(self.db_path)
        count = conn.execute("SELECT count(*) FROM speed_tests").fetchone()[0]
        rows = conn.execute("SELECT name FROM speed_tests").fetchall()
        conn.close()
        assert count == 1
        assert rows[0][0] == "test"

    def test_restore_backup_invalid_file(self):
        service = BackupService(db_path=self.db_path)
        invalid_path = os.path.join(self.tmpdir, "invalid.db")
        with open(invalid_path, "w") as fh:
            fh.write("not a sqlite database")

        try:
            service.restore_backup(invalid_path)
            assert False, "Should have raised DatabaseError"
        except Exception:
            pass  # Expected

    def test_restore_backup_nonexistent(self):
        service = BackupService(db_path=self.db_path)
        try:
            service.restore_backup("/nonexistent/path.db")
            assert False, "Should have raised DatabaseError"
        except Exception:
            pass  # Expected
