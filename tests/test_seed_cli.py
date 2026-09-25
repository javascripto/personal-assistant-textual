from datetime import datetime
from pathlib import Path

from personal_assistant.database import Database
from personal_assistant.seed_cli import backup_database


def test_backup_database_creates_a_timestamped_consistent_copy(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "assistant.db"
    database = Database(database_path, seed=False)
    task_id = database.create_task("Tarefa para backup")
    database.close()

    backup_path = backup_database(database_path, datetime(2026, 9, 25, 18, 0))

    assert backup_path is not None
    assert backup_path == tmp_path / "assistant.backup-20260925-180000.db"
    assert backup_path.is_file()
    backup = Database(backup_path, seed=False)
    task = backup.get_task(task_id)
    assert task is not None
    assert task.title == "Tarefa para backup"
    backup.close()


def test_backup_database_skips_a_missing_source(tmp_path: Path) -> None:
    assert backup_database(tmp_path / "missing.db") is None
