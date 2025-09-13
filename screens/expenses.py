
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.reactive import Reactive, reactive
from textual.widget import Widget
from textual.widgets import (
    Footer,
    Header,
    Label,
    Select,
    Static,
    Switch
)

from .database import DatabaseManager, DatabaseScreen


class ExpenseView(Widget):
    db_manager: DatabaseManager = DatabaseManager()

    def compose(self) -> ComposeResult:
        self.db_manager.create_expenses_table()


class ExpensesScreen(DatabaseScreen):

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container():
            yield ExpenseView()
        yield Footer()