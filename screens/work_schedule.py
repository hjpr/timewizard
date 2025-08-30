
import calendar

from datetime import datetime
from textual import log
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import Reactive, reactive
from textual.widget import Widget
from textual.widgets import (
    Footer,
    Header,
    Label,
    Select,
)

from .database import DatabaseManager, DatabaseScreen

class Calendar(Widget):
    db_manager: DatabaseManager = DatabaseManager()
    month_from_db: Reactive[dict[str, list[dict[str, str | int | bool]]]] = reactive({}, recompose=True)
    today: datetime = datetime.now()
    today_month: int = today.month
    today_year: int = today.year
    selected_month: Reactive = reactive(calendar.month_name[today_month])
    selected_year: Reactive = reactive(today_year)

    def compose(self):
        with Container(id="calendar-container"):
            with Horizontal(classes="calendar-top"):
                yield Select.from_values([month for month in calendar.month_name if month], value=self.selected_month, id="select-month")
                yield Select.from_values([self.today_year - 1, self.today_year, self.today_year + 1], value=self.today_year, id="select-year")
            with Container(id="date-container"):
                for _, week_data in self.month_from_db.items():
                    for day in week_data:
                        with Container(classes="day-container"):
                            yield Label(f"{day["day"]}"),

    def on_mount(self) -> None:
        # Ensure current year, previous year, and next year's calendar is prebuilt into database.
        current_year = datetime.now().year
        for increment in (-1, 0, 1):
            if not self.db_manager.year_exists(current_year + increment):
                self.db_manager.insert_full_year(current_year + increment)

        # Grab current calendar month
        selected_month_int = list(calendar.month_name).index(self.selected_month)
        self.month_from_db = self.db_manager.get_month_data(self.selected_year, selected_month_int)

    def on_select_changed(self, event: Select.Changed) -> None:
        pass

class WorkScheduleScreen(DatabaseScreen):

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container():
            yield Calendar()
        yield Footer()
        