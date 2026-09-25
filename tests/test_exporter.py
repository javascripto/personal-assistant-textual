from datetime import datetime
from pathlib import Path

from openpyxl import load_workbook

from personal_assistant.exporter import export_tasks
from personal_assistant.models import Task, TaskStatus


def test_export_tasks_creates_readable_workbook(tmp_path: Path) -> None:
    task = Task(
        id=1,
        title="Exportar planilha",
        tag="tarefa",
        description="Conferir as colunas exportadas.",
        status=TaskStatus.COMPLETED,
        created_at=datetime(2026, 9, 25, 17, 8),
        completed_at=datetime(2026, 9, 25, 17, 9),
    )

    output = export_tasks([task], tmp_path)

    workbook = load_workbook(output)
    sheet = workbook["Tarefas"]
    assert sheet["A1"].value == "Status"
    assert sheet["A2"].value == "completed"
    assert sheet["D2"].value == "Exportar planilha"
    assert sheet["E2"].value == "Conferir as colunas exportadas."
