import asyncio
from pathlib import Path
from typing import cast

from textual.containers import Container, Horizontal
from textual.widgets import (
    Button,
    DataTable,
    Input,
    Static,
    TabbedContent,
    TextArea,
)

from personal_assistant.app import RETRO_THEME_NAME, PersonalAssistant
from personal_assistant.database import Database


def test_application_mounts_with_the_retro_task_table(tmp_path: Path) -> None:
    database = Database(tmp_path / "assistant.db", seed=False)
    app = PersonalAssistant(database)

    async def mount() -> None:
        async with app.run_test(size=(120, 40)):
            table = cast(
                DataTable[str],
                app.query_one("#tasks-all", DataTable),
            )
            frame = app.query_one("#application-frame", Container)
            panel_title = app.query_one("#panel-title", Static)
            clock = app.query_one("#clock", Static)
            assert {key.value for key in table.columns} == {
                "status",
                "date",
                "tag",
                "title",
            }
            assert frame.region.width == 120
            assert clock.region.y == panel_title.region.y
            assert clock.region.x > panel_title.region.x

    asyncio.run(mount())


def test_clock_timer_tolerates_removing_the_header(tmp_path: Path) -> None:
    app = PersonalAssistant(Database(tmp_path / "assistant.db", seed=False))

    async def remove_header() -> None:
        async with app.run_test(size=(120, 40)) as pilot:
            await app.query_one("#application-header", Horizontal).remove()
            # Let the real interval fire after its target leaves the DOM.
            await pilot.pause(1.1)
            assert not app.query("#clock")

    asyncio.run(remove_header())


def test_new_and_edit_shortcuts_open_the_confirmable_task_form(
    tmp_path: Path,
) -> None:
    database = Database(tmp_path / "assistant.db", seed=False)
    database.create_task(
        "Tarefa existente",
        description="Contexto da tarefa existente.",
    )
    app = PersonalAssistant(database)

    async def exercise_shortcuts() -> None:
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.press("n")
            confirm = app.screen.query_one("#confirm", Button)
            cancel = app.screen.query_one("#cancel", Button)
            assert confirm.label == "Confirmar"
            assert cancel.label == "Cancelar"
            assert confirm.region.height > 0
            assert cancel.region.height > 0
            assert (
                app.screen.query_one(
                    "#task-description", TextArea
                ).region.height
                >= 10
            )
            await pilot.press("escape")

            await pilot.press("e")
            assert (
                app.screen.query_one("#task-title", Input).value
                == "Tarefa existente"
            )
            assert (
                app.screen.query_one("#task-description", TextArea).text
                == "Contexto da tarefa existente."
            )
            await pilot.press("ctrl+enter")

            await pilot.press("n")
            app.screen.query_one("#task-title", Input).value = "Nova tarefa"
            description = app.screen.query_one("#task-description", TextArea)
            description.load_text("Primeira linha\nSegunda linha")
            description.focus()
            await pilot.press("ctrl+enter")
            assert any(
                task.title == "Nova tarefa"
                and task.description == "Primeira linha\nSegunda linha"
                for task in database.list_tasks()
            )

            assert app.focused is app.query_one("#tasks-all", DataTable)
            await pilot.press("enter")
            details_description = app.screen.query_one(
                "#details-description", TextArea
            )
            assert details_description.read_only
            assert details_description.text == "Contexto da tarefa existente."

    asyncio.run(exercise_shortcuts())


def test_tab_navigation_keeps_focus_on_tabs_until_tab_is_pressed_again(
    tmp_path: Path,
) -> None:
    database = Database(tmp_path / "assistant.db", seed=False)
    database.create_task("Tarefa existente")
    app = PersonalAssistant(database)

    async def navigate_tabs() -> None:
        async with app.run_test(size=(120, 40)) as pilot:
            table = cast(
                DataTable[str],
                app.query_one("#tasks-all", DataTable),
            )
            await pilot.press("tab")
            tabs_focus = app.focused
            assert tabs_focus is not None
            assert tabs_focus is not table

            await pilot.press("right")
            assert app.focused is tabs_focus
            assert app.query_one("#filters", TabbedContent).active == "pending"

    asyncio.run(navigate_tabs())


def test_status_toggle_preserves_the_selected_task(tmp_path: Path) -> None:
    database = Database(tmp_path / "assistant.db", seed=False)
    database.create_task("Primeira tarefa")
    database.create_task("Segunda tarefa")
    app = PersonalAssistant(database)

    async def toggle_status() -> None:
        async with app.run_test(size=(120, 40)) as pilot:
            selected_task_id = app.selected_task_id()
            assert selected_task_id is not None

            await pilot.press("space")

            assert app.selected_task_id() == selected_task_id

    asyncio.run(toggle_status())


def test_selected_theme_applies_to_the_app_and_is_persisted(
    tmp_path: Path,
) -> None:
    database = Database(tmp_path / "assistant.db", seed=False)
    app = PersonalAssistant(database)

    async def change_theme() -> None:
        async with app.run_test(size=(120, 40)):
            assert app.theme == RETRO_THEME_NAME
            app.theme = "nord"
            assert app.current_theme.name == "nord"
            assert database.get_setting("theme", "") == "nord"

    asyncio.run(change_theme())


def test_command_bar_wraps_instead_of_hiding_shortcuts(tmp_path: Path) -> None:
    database = Database(tmp_path / "assistant.db", seed=False)
    app = PersonalAssistant(database)

    async def render_narrow_terminal() -> None:
        async with app.run_test(size=(40, 40)):
            command_bar = app.query_one("#command-bar", Static)
            assert "q[/] Sair" in str(command_bar.content)
            assert command_bar.region.height > 1

    asyncio.run(render_narrow_terminal())


def test_theme_shortcut_selects_the_next_available_theme(
    tmp_path: Path,
) -> None:
    database = Database(tmp_path / "assistant.db", seed=False)
    app = PersonalAssistant(database)

    async def advance_theme() -> None:
        async with app.run_test(size=(120, 40)) as pilot:
            theme_names = tuple(app.available_themes)
            expected_theme = theme_names[
                (theme_names.index(app.theme) + 1) % len(theme_names)
            ]

            await pilot.press("t")

            assert app.theme == expected_theme
            assert database.get_setting("theme", "") == expected_theme

    asyncio.run(advance_theme())
