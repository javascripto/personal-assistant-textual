"""SQLite persistence with explicit, small operations for the TUI."""

import sqlite3
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

from personal_assistant.models import Task, TaskStatus
from personal_assistant.seed import SEED_TASKS

DEFAULT_DATABASE_PATH = Path("data/personal_assistant.db")


class Database:
    """Repository for tasks and UI preferences."""

    def __init__(
        self, path: Path = DEFAULT_DATABASE_PATH, *, seed: bool = True
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self._migrate()
        if seed:
            self._seed_if_empty()

    def close(self) -> None:
        """Close the SQLite connection held by this repository."""
        self.connection.close()

    def _migrate(self) -> None:
        self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL CHECK(length(trim(title)) > 0),
                tag TEXT NOT NULL DEFAULT 'tarefa' CHECK(length(trim(tag)) > 0),
                description TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'pending'
                    CHECK(status IN ('pending', 'completed')),
                created_at TEXT NOT NULL,
                completed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """)
        task_columns = {
            str(row["name"])
            for row in self.connection.execute(
                "PRAGMA table_info(tasks)"
            ).fetchall()
        }
        if "description" not in task_columns:
            self.connection.execute(
                "ALTER TABLE tasks ADD COLUMN description "
                "TEXT NOT NULL DEFAULT ''"
            )
        self.connection.commit()

    def _seed_if_empty(self) -> None:
        row = self.connection.execute(
            "SELECT COUNT(*) AS count FROM tasks"
        ).fetchone()
        if row is None or int(row["count"]) != 0:
            return

        self.seed_missing_tasks()

    def seed_missing_tasks(self) -> int:
        """Insert missing generic seed tasks without changing existing tasks."""
        existing_rows = self.connection.execute(
            "SELECT title, tag, created_at FROM tasks"
        ).fetchall()
        existing_keys = {
            (str(row["title"]), str(row["tag"]), str(row["created_at"]))
            for row in existing_rows
        }
        missing_tasks = tuple(
            task
            for task in SEED_TASKS
            if (task[2], task[1], task[0].isoformat()) not in existing_keys
        )
        if not missing_tasks:
            return 0

        self._insert_seed_tasks(missing_tasks)
        self.connection.commit()
        return len(missing_tasks)

    def _insert_seed_tasks(
        self, tasks: Iterable[tuple[datetime, str, str, TaskStatus]]
    ) -> None:
        rows = [
            (
                title,
                tag,
                "",
                status.value,
                created_at.isoformat(),
                (
                    created_at.isoformat()
                    if status is TaskStatus.COMPLETED
                    else None
                ),
            )
            for created_at, tag, title, status in tasks
        ]
        self.connection.executemany(
            """
            INSERT INTO tasks(
                title, tag, description, status, created_at, completed_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            rows,
        )

    def create_task(
        self, title: str, tag: str = "tarefa", description: str = ""
    ) -> int:
        cursor = self.connection.execute(
            """
            INSERT INTO tasks(
                title, tag, description, status, created_at, completed_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                title.strip(),
                tag.strip() or "tarefa",
                description.strip(),
                TaskStatus.PENDING.value,
                datetime.now().isoformat(),
                None,
            ),
        )
        self.connection.commit()
        if cursor.lastrowid is None:
            raise RuntimeError("SQLite did not return the new task identifier.")
        return cursor.lastrowid

    def update_task(
        self, task_id: int, title: str, tag: str, description: str
    ) -> None:
        self.connection.execute(
            "UPDATE tasks SET title = ?, tag = ?, description = ? WHERE id = ?",
            (
                title.strip(),
                tag.strip() or "tarefa",
                description.strip(),
                task_id,
            ),
        )
        self.connection.commit()

    def delete_task(self, task_id: int) -> None:
        self.connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self.connection.commit()

    def toggle_task(self, task_id: int) -> None:
        row = self.connection.execute(
            "SELECT status FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if row is None:
            return
        status = TaskStatus(row["status"])
        next_status = (
            TaskStatus.COMPLETED
            if status is TaskStatus.PENDING
            else TaskStatus.PENDING
        )
        completed_at = (
            datetime.now().isoformat()
            if next_status is TaskStatus.COMPLETED
            else None
        )
        self.connection.execute(
            "UPDATE tasks SET status = ?, completed_at = ? WHERE id = ?",
            (next_status.value, completed_at, task_id),
        )
        self.connection.commit()

    def get_task(self, task_id: int) -> Task | None:
        row = self.connection.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        return self._to_task(row) if row is not None else None

    def list_tasks(
        self, status: TaskStatus | None = None, order: str = "desc"
    ) -> list[Task]:
        direction = "ASC" if order == "asc" else "DESC"
        sql = "SELECT * FROM tasks"
        parameters: tuple[str, ...] = ()
        if status is not None:
            sql += " WHERE status = ?"
            parameters = (status.value,)
        sql += f" ORDER BY created_at {direction}, id {direction}"
        rows = self.connection.execute(sql, parameters).fetchall()
        return [self._to_task(row) for row in rows]

    def set_setting(self, key: str, value: str) -> None:
        self.connection.execute(
            """
            INSERT INTO settings(key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )
        self.connection.commit()

    def get_setting(self, key: str, default: str) -> str:
        row = self.connection.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
        return str(row["value"]) if row is not None else default

    @staticmethod
    def _to_task(row: sqlite3.Row) -> Task:
        completed_at = row["completed_at"]
        return Task(
            id=int(row["id"]),
            title=str(row["title"]),
            tag=str(row["tag"]),
            description=str(row["description"]),
            status=TaskStatus(row["status"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
            completed_at=(
                datetime.fromisoformat(str(completed_at))
                if completed_at
                else None
            ),
        )
