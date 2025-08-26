
import calendar
from datetime import datetime
from textual import log

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
                yield Select.from_values([2025, 2026, 2027, 2028, 2029, 2030], value=2025, id="select-year")
            with Vertical(id="date-container"):
                with Horizontal(classes="calendar-top"):
                    yield Container(Label("Sun"), classes="title")
                    yield Container(Label("Mon"), classes="title")
                    yield Container(Label("Tues"), classes="title")
                    yield Container(Label("Wed"), classes="title")
                    yield Container(Label("Thurs"), classes="title")
                    yield Container(Label("Fri"), classes="title")
                    yield Container(Label("Sat"), classes="title")
                for row in self.built_calendar:
                    with Horizontal(classes="centered"):
                        for index, day in enumerate(row, start=1):
                            with Container(classes="day-container"):
                                yield Label(f"{day}" if day else "")
                                if day:
                                    yield Label("[bold red]$774[/bold red]" if index in (1,7,8,14,15,21,22,28,29) else "[bold green]$654[/bold green]")
                                yield Switch(disabled=True if not day else False, id=f"day-{day}" if day else None)

    def build_calendar(self, month, year) -> None:
        calendar_structure = calendar.Calendar(firstweekday=calendar.SUNDAY).monthdayscalendar(year, month)
        self.built_calendar = calendar_structure

    def on_mount(self) -> None:
        self.build_calendar(self.today_month, self.today_year)

    def on_select_changed(self, event: Select.Changed) -> None:
        if isinstance(event.value, str):
            self.selected_month = event.value
            selected_month = list(calendar.month_name).index(event.value, 1)
            self.build_calendar(selected_month, self.selected_year)

class WorkScheduleScreen(Screen):

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container():
            yield Calendar()
        yield Footer()