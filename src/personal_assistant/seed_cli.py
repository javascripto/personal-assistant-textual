"""Command-line entry point for safely inserting the generic task seed."""

import sqlite3
from datetime import datetime
from pathlib import Path

from personal_assistant.database import DEFAULT_DATABASE_PATH, Database


def backup_database(
    database_path: Path,
    timestamp: datetime | None = None,
) -> Path | None:
    """Create a consistent timestamped SQLite backup when the source exists."""
    if not database_path.exists():
        return None

    created_at = timestamp or datetime.now()
    backup_path = database_path.with_name(
        f"{database_path.stem}.backup-{created_at:%Y%m%d-%H%M%S}"
        f"{database_path.suffix}"
    )
    sequence = 2
    while backup_path.exists():
        backup_path = database_path.with_name(
            f"{database_path.stem}.backup-{created_at:%Y%m%d-%H%M%S}-{sequence}"
            f"{database_path.suffix}"
        )
        sequence += 1
    source = sqlite3.connect(database_path)
    destination = sqlite3.connect(backup_path)
    try:
        source.backup(destination)
    finally:
        destination.close()
        source.close()
    return backup_path


def main() -> None:
    """Insert generic seed tasks absent from the local SQLite database."""
    backup_path = backup_database(DEFAULT_DATABASE_PATH)
    database = Database(seed=False)
    try:
        added_tasks = database.seed_missing_tasks()
    finally:
        database.close()

    if backup_path is not None:
        print(f"Backup criado: {backup_path}")
    print(f"{added_tasks} tarefa(s) genérica(s) adicionada(s).")


if __name__ == "__main__":
    main()
