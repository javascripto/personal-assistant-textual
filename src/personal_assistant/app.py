"""Textual application inspired by the supplied retro task-manager reference."""

from collections.abc import Callable, Iterable
from datetime import datetime
from typing import cast

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.theme import Theme
from textual.widgets import (
    Button,
    DataTable,
    Input,
    Label,
    Static,
    TabbedContent,
    TabPane,
    TextArea,
)

from personal_assistant.database import Database
from personal_assistant.exporter import export_tasks
from personal_assistant.models import Task, TaskDraft, TaskStatus

RETRO_THEME_NAME = "personal-assistant-retro"
RETRO_THEME = Theme(
    name=RETRO_THEME_NAME,
    primary="#2222aa",
    secondary="#008888",
    warning="#ffaa00",
    error="#dd5555",
    success="#55aa44",
    accent="#ffff55",
    foreground="#dddddd",
    background="#111111",
    surface="#151515",
    panel="#222222",
    variables={"footer-key-foreground": "#ffff55"},
)


class TaskModal(ModalScreen[TaskDraft | None]):
    """Create or edit a task without leaving the keyboard-driven flow."""

    BINDINGS = [Binding("escape", "dismiss_modal", "Voltar", show=False)]

    def __init__(
        self, title: str = "", tag: str = "tarefa", description: str = ""
    ) -> None:
        super().__init__()
        self.initial_title = title
        self.initial_tag = tag
        self.initial_description = description

    def compose(self) -> ComposeResult:
        with Container(id="task-dialog"):
            yield Label(
                "Editar tarefa" if self.initial_title else "Nova tarefa",
                id="dialog-title",
            )
            yield Label("Título")
            yield Input(
                value=self.initial_title,
                placeholder="Descrição da tarefa",
                id="task-title",
            )
            yield Label("Tag")
            yield Input(
                value=self.initial_tag, placeholder="tarefa", id="task-tag"
            )
            yield Label("Descrição")
            yield TextArea(
                self.initial_description,
                soft_wrap=True,
                id="task-description",
                placeholder="Detalhes, contexto e próximos passos",
            )
            with Horizontal():
                yield Button("Confirmar", variant="primary", id="confirm")
                yield Button("Cancelar", id="cancel")

    def on_mount(self) -> None:
        self.query_one("#task-title", Input).focus()

    def action_dismiss_modal(self) -> None:
        self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._save()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm":
            self._save()
        elif event.button.id == "cancel":
            self.dismiss(None)

    def _save(self) -> None:
        title = self.query_one("#task-title", Input).value.strip()
        tag = self.query_one("#task-tag", Input).value.strip()
        description = self.query_one("#task-description", TextArea).text.strip()
        if not title:
            self.notify("Informe um título para a tarefa.", severity="warning")
            return
        self.dismiss(
            TaskDraft(
                title=title,
                tag=tag or "tarefa",
                description=description,
            )
        )


class ConfirmDeleteModal(ModalScreen[bool]):
    """Prevent accidental deletion from a single keypress."""

    BINDINGS = [Binding("escape", "cancel", "Voltar", show=False)]

    def __init__(self, title: str) -> None:
        super().__init__()
        self.task_title = title

    def compose(self) -> ComposeResult:
        with Container(id="confirm-dialog"):
            yield Label("Excluir tarefa?", id="dialog-title")
            yield Static(f'"{self.task_title}"', id="confirm-task-title")
            yield Static("Esta ação não pode ser desfeita.")
            with Horizontal():
                yield Button("Excluir", variant="error", id="confirm-delete")
                yield Button("Cancelar", id="cancel-delete")

    def action_cancel(self) -> None:
        self.dismiss(False)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "confirm-delete")


class TaskDetailsModal(ModalScreen[bool | None]):
    """Read a task and its long description without entering edit mode."""

    BINDINGS = [
        Binding("escape", "close_details", "Voltar", show=False),
        Binding("e", "edit", "Editar", show=False),
    ]

    def __init__(self, task: Task) -> None:
        super().__init__()
        self.task_model = task

    def compose(self) -> ComposeResult:
        status = (
            "Concluída"
            if self.task_model.status is TaskStatus.COMPLETED
            else "Pendente"
        )
        with Container(id="task-details-dialog"):
            yield Label("Detalhes da tarefa", id="dialog-title")
            yield Static(self.task_model.title, id="details-title")
            yield Static(
                f"Tag: {self.task_model.tag}   Status: {status}   "
                f"Criada: {self.task_model.created_at:%d/%m/%Y %H:%M}",
                id="details-metadata",
            )
            yield Label("Descrição")
            yield TextArea(
                self.task_model.description,
                read_only=True,
                show_cursor=False,
                soft_wrap=True,
                id="details-description",
                placeholder="Nenhuma descrição informada.",
            )
            with Horizontal():
                yield Button("Editar", variant="primary", id="edit-details")
                yield Button("Voltar", id="close-details")

    def on_mount(self) -> None:
        self.query_one("#details-description", TextArea).focus()

    def action_close_details(self) -> None:
        self.dismiss(None)

    def action_edit(self) -> None:
        self.dismiss(True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(True if event.button.id == "edit-details" else None)


class PersonalAssistant(App[None]):
    """Retro Clipper/QBasic-inspired task manager."""

    CSS_PATH = "personal_assistant.tcss"
    TITLE = "Personal Assistant"
    BINDINGS = [
        Binding("n", "new_task", "Novo"),
        Binding("d", "delete_task", "Deletar"),
        Binding("space", "toggle_task", "Concluir/Pendente"),
        Binding("o", "toggle_order", "Ordenação"),
        Binding("x", "export", "Exportar XLSX"),
        Binding("t", "next_theme", "Próx. tema"),
        Binding("e", "edit_task", "Editar"),
        Binding("ctrl+p", "palette", "Palette", show=False),
        Binding("q", "quit", "Sair", show=False),
    ]

    def __init__(self, database: Database | None = None) -> None:
        super().__init__()
        self.database = database or Database()
        self.register_theme(RETRO_THEME)
        saved_theme = self.database.get_setting("theme", RETRO_THEME_NAME)
        self.theme = (
            saved_theme
            if self.get_theme(saved_theme) is not None
            else RETRO_THEME_NAME
        )
        saved_order = self.database.get_setting("task_order", "desc")
        self.order = saved_order if saved_order in {"asc", "desc"} else "desc"

    def watch_theme(self, theme_name: str) -> None:
        """Persist a theme selected through Textual's native command palette."""
        self.database.set_setting("theme", theme_name)

    def compose(self) -> ComposeResult:
        with Container(id="application-frame"):
            with Container(id="main-panel"):
                with Horizontal(id="application-header"):
                    yield Static("Personal Assistant", id="panel-title")
                    yield Static("", id="clock")
                yield Static("", id="order-label")
                with TabbedContent(initial="all", id="filters"):
                    with TabPane("Todos", id="all"):
                        yield DataTable[str](id="tasks-all", cursor_type="row")
                    with TabPane("Pendentes", id="pending"):
                        yield DataTable[str](
                            id="tasks-pending", cursor_type="row"
                        )
                    with TabPane("Concluídos", id="completed"):
                        yield DataTable[str](
                            id="tasks-completed", cursor_type="row"
                        )
            yield Static(
                "[bold yellow]n[/] Novo  [bold yellow]e[/] Editar  "
                "[bold yellow]enter[/] Detalhes  "
                "[bold yellow]d[/] Deletar  "
                "[bold yellow]space[/] Concluir/Pendente  "
                "[bold yellow]o[/] Ordenação  [bold yellow]x[/] Exportar XLSX  "
                "[bold yellow]t[/] Próx. tema  "
                "[bold yellow]esc[/] Voltar  [bold yellow]^p[/] Palette  "
                "[bold yellow]q[/] Sair",
                id="command-bar",
            )

    def on_mount(self) -> None:
        tables = cast(
            Iterable[DataTable[str]],
            self.query(DataTable),
        )
        for table in tables:
            table.add_column("Status", key="status")
            table.add_column("Data", key="date")
            table.add_column("Tags", key="tag")
            table.add_column("Título", key="title")
        self.set_interval(1, self._update_clock)
        self._update_clock()
        self.refresh_tasks()
        self.current_table().focus()

    def on_unmount(self) -> None:
        self.database.close()

    def _update_clock(self) -> None:
        self.query_one("#clock", Static).update(
            datetime.now().strftime("%H:%M:%S")
        )

    def current_table(self) -> DataTable[str]:
        tabs = self.query_one("#filters", TabbedContent)
        selectors = {
            "all": "#tasks-all",
            "pending": "#tasks-pending",
            "completed": "#tasks-completed",
        }
        return cast(
            DataTable[str], self.query_one(selectors[tabs.active], DataTable)
        )

    def refresh_tasks(self, selected_task_id: int | None = None) -> None:
        selected_task_id = selected_task_id or self.selected_task_id()
        table_filters = {
            "#tasks-all": None,
            "#tasks-pending": TaskStatus.PENDING,
            "#tasks-completed": TaskStatus.COMPLETED,
        }
        selected_row: int | None = None
        for selector, status in table_filters.items():
            table = cast(DataTable[str], self.query_one(selector, DataTable))
            table.clear()
            for row_index, task in enumerate(
                self.database.list_tasks(status=status, order=self.order)
            ):
                status_icon = (
                    "[green]✓[/green]"
                    if task.status is TaskStatus.COMPLETED
                    else "[yellow]○[/yellow]"
                )
                table.add_row(
                    status_icon,
                    task.created_at.strftime("%d/%m/%Y %H:%M"),
                    task.tag,
                    task.title,
                    key=str(task.id),
                )
                if (
                    selector == self._current_table_selector()
                    and task.id == selected_task_id
                ):
                    selected_row = row_index
        direction = "crescente" if self.order == "asc" else "decrescente"
        self.query_one("#order-label", Static).update(
            f"Ordenado por: Data ({direction} - o para alternar)"
        )
        if selected_row is not None:
            self.current_table().move_cursor(
                row=selected_row, column=0, animate=False
            )

    def selected_task_id(self) -> int | None:
        table = self.current_table()
        if table.row_count == 0:
            return None
        try:
            cell_key = table.coordinate_to_cell_key(table.cursor_coordinate)
            row_key = cell_key.row_key.value
            return int(row_key) if row_key is not None else None
        except (IndexError, TypeError, ValueError):
            return None

    def action_new_task(self) -> None:
        self.push_screen(TaskModal(), self._create_task)

    def _create_task(self, draft: TaskDraft | None) -> None:
        if draft is not None:
            self.database.create_task(draft.title, draft.tag, draft.description)
            self.refresh_tasks()
        self._restore_table_focus()

    def action_edit_task(self) -> None:
        task = self._selected_task()
        if task is not None:
            self.push_screen(
                TaskModal(task.title, task.tag, task.description),
                self._update_task(task.id),
            )

    def _update_task(self, task_id: int) -> Callable[[TaskDraft | None], None]:
        def update(draft: TaskDraft | None) -> None:
            if draft is not None:
                self.database.update_task(
                    task_id,
                    draft.title,
                    draft.tag,
                    draft.description,
                )
                self.refresh_tasks()
            self._restore_table_focus()

        return update

    def action_show_task_details(self) -> None:
        task = self._selected_task()
        if task is not None:
            self.push_screen(TaskDetailsModal(task), self._handle_task_details)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Use DataTable's native Enter event to open task details."""
        self.action_show_task_details()

    def _handle_task_details(self, edit_requested: bool | None) -> None:
        if edit_requested:
            self.action_edit_task()
        else:
            self._restore_table_focus()

    def action_toggle_task(self) -> None:
        task_id = self.selected_task_id()
        if task_id is not None:
            self.database.toggle_task(task_id)
            self.refresh_tasks(selected_task_id=task_id)

    def action_delete_task(self) -> None:
        task = self._selected_task()
        if task is not None:
            self.push_screen(
                ConfirmDeleteModal(task.title), self._delete_task(task.id)
            )

    def _delete_task(self, task_id: int) -> Callable[[bool | None], None]:
        def delete(confirmed: bool | None) -> None:
            if confirmed:
                self.database.delete_task(task_id)
                self.refresh_tasks()
            self._restore_table_focus()

        return delete

    def action_toggle_order(self) -> None:
        self.order = "asc" if self.order == "desc" else "desc"
        self.database.set_setting("task_order", self.order)
        self.refresh_tasks()

    def action_export(self) -> None:
        path = export_tasks(self.database.list_tasks(order=self.order))
        self.notify(f"Exportado: {path}", title="XLSX criado")

    def action_next_theme(self) -> None:
        """Activate the next theme offered by Textual's command palette."""
        theme_names = tuple(self.available_themes)
        current_index = theme_names.index(self.theme)
        self.theme = theme_names[(current_index + 1) % len(theme_names)]
        self.notify(f"Tema: {self.current_theme.name}", title="Tema alterado")

    def action_palette(self) -> None:
        self.action_command_palette()

    def _selected_task(self) -> Task | None:
        task_id = self.selected_task_id()
        return self.database.get_task(task_id) if task_id is not None else None

    def _current_table_selector(self) -> str:
        tabs = self.query_one("#filters", TabbedContent)
        return {
            "all": "#tasks-all",
            "pending": "#tasks-pending",
            "completed": "#tasks-completed",
        }[tabs.active]

    def _restore_table_focus(self) -> None:
        self.current_table().focus()


def main() -> None:
    """Launch the terminal application."""
    PersonalAssistant().run()


if __name__ == "__main__":
    main()
