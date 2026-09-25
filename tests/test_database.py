import sqlite3
from datetime import datetime
from pathlib import Path

from personal_assistant.database import Database
from personal_assistant.models import TaskStatus


def test_create_update_toggle_and_delete_task(tmp_path: Path) -> None:
    database = Database(tmp_path / "assistant.db", seed=False)

    task_id = database.create_task("Preparar release", "deploy")
    task = database.get_task(task_id)
    assert task is not None
    assert task.title == "Preparar release"
    assert task.tag == "deploy"
    assert task.status is TaskStatus.PENDING

    database.update_task(
        task_id,
        "Preparar release 2",
        "release",
        "Descrição da release.",
    )
    database.toggle_task(task_id)
    updated_task = database.get_task(task_id)
    assert updated_task is not None
    assert updated_task.title == "Preparar release 2"
    assert updated_task.description == "Descrição da release."
    assert updated_task.status is TaskStatus.COMPLETED
    assert updated_task.completed_at is not None

    database.toggle_task(task_id)
    assert database.get_task(task_id).status is TaskStatus.PENDING  # type: ignore[union-attr]
    database.delete_task(task_id)
    assert database.get_task(task_id) is None
    database.close()


def test_filter_order_and_settings_persist(tmp_path: Path) -> None:
    database = Database(tmp_path / "assistant.db", seed=False)
    older = database.create_task("Mais antiga")
    database.connection.execute(
        "UPDATE tasks SET created_at = ? WHERE id = ?",
        (datetime(2026, 1, 1).isoformat(), older),
    )
    newer = database.create_task("Mais nova")
    database.toggle_task(newer)
    database.connection.commit()

    assert [task.id for task in database.list_tasks(order="asc")] == [
        older,
        newer,
    ]
    assert [task.id for task in database.list_tasks(TaskStatus.COMPLETED)] == [
        newer
    ]
    database.set_setting("task_order", "asc")
    assert database.get_setting("task_order", "desc") == "asc"
    database.close()


def test_new_database_receives_anonymous_generic_seed(tmp_path: Path) -> None:
    database = Database(tmp_path / "assistant.db")
    tasks = database.list_tasks()
    assert len(tasks) == 10
    assert tasks[0].title == "Revisar documentação do projeto"
    database.close()


def test_seed_missing_tasks_is_idempotent(tmp_path: Path) -> None:
    database = Database(tmp_path / "assistant.db", seed=False)

    assert database.seed_missing_tasks() == 10
    assert database.seed_missing_tasks() == 0
    assert len(database.list_tasks()) == 10
    database.close()


def test_existing_database_is_migrated_with_a_description_column(
    tmp_path: Path,
) -> None:
    path = tmp_path / "legacy.db"
    legacy = sqlite3.connect(path)
    legacy.executescript("""
        CREATE TABLE tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            tag TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            completed_at TEXT
        );
        CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        INSERT INTO tasks(title, tag, status, created_at, completed_at)
        VALUES (
            'Tarefa antiga', 'tarefa', 'pending', '2026-09-25T17:00:00', NULL
        );
        """)
    legacy.close()

    database = Database(path, seed=False)
    task = database.list_tasks()[0]
    assert task.description == ""
    database.update_task(task.id, task.title, task.tag, "Descrição adicionada")
    updated_task = database.get_task(task.id)
    assert updated_task is not None
    assert updated_task.description == "Descrição adicionada"
    database.close()
