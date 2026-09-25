"""Domain types for persisted tasks."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class TaskStatus(StrEnum):
    """The two task states currently supported by the application."""

    PENDING = "pending"
    COMPLETED = "completed"


@dataclass(frozen=True, slots=True)
class Task:
    """A task as stored in SQLite and rendered by the TUI."""

    id: int
    title: str
    tag: str
    description: str
    status: TaskStatus
    created_at: datetime
    completed_at: datetime | None


@dataclass(frozen=True, slots=True)
class TaskDraft:
    """Editable task data returned by the task editor modal."""

    title: str
    tag: str
    description: str
