
import calendar
from datetime import datetime
from textual import log
from typing import Any

from textual.app import ComposeResult, RenderResult
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import (
    Button,
    Footer,
    Header,
    Label,
    Select,
    Switch
)

import calendar

class Calendar(Widget):
    built_calendar: list[list[int]] = reactive([], recompose=True)
    today: datetime = datetime.now()
    today_month = today.month
    today_year = today.year
    selected_month = reactive(calendar.month_name[today_month])
    selected_year = reactive(today_year)

    def compose(self):
        with Container(id="calendar-container"):
            with Horizontal(classes="calendar-top"):
                yield Select.from_values([month for month in calendar.month_name if month], value=self.selected_month, id="select-month")
                yield Select.from_values([self.today_year - 1, self.today_year, self.today_year + 1], value=self.today_year, id="select-year")
            with Container(id="date-container"):
                for _ in range(42):
                    yield Container(classes="day-container")

    def on_mount(self) -> None:
        pass

    def on_select_changed(self, event: Select.Changed) -> None:
        pass

class WorkScheduleScreen(Screen):

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container():
            yield Calendar()
        yield Footer()