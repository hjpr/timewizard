import calendar
import itertools

from calendar import Calendar
from datetime import datetime
from textual import log
from textual.app import ComposeResult
from textual.color import Color
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import Reactive, reactive
from textual.widget import Widget
from textual.widgets import (
    Footer,
    Header,
    Label,
    Select,
    Switch
)

from .database import DatabaseManager, DatabaseScreen

class CalendarView(Widget):
    BASE_RATE_PER_HOUR: float = 54.5
    WEEKEND_RATE_PER_HOUR: int = 10

    db_manager: DatabaseManager = DatabaseManager()
    days: Reactive[list[dict[str, str | int | bool]]] = reactive([], recompose=True)
    today: datetime = datetime.today().date()
    today_month: int = today.month
    today_year: int = today.year
    selected_month: str = calendar.month_name[today_month]
    selected_month_int: int = today_month
    selected_year: int = today_year

    def compose(self):
        with Container(id="calendar-container"):
            with Horizontal(classes="calendar-top"):
                yield Select.from_values([month for month in calendar.month_name if month], value=self.selected_month, id="select-month")
                yield Select.from_values([self.today_year - 1, self.today_year, self.today_year + 1], value=self.today_year, id="select-year")
            with Container(id="calendar-labels"):
                yield Label("Sun", classes="title")
                yield Label("Mon", classes="title")
                yield Label("Tues", classes="title")
                yield Label("Wed", classes="title")
                yield Label("Thurs", classes="title")
                yield Label("Fri", classes="title")
                yield Label("Sat", classes="title")
            with Container(classes="calendar-days"):
                for day in self.days:
                    day_container = Container(classes="day-container", id=f"container-{day['date_string']}")
                    day_container.border_title = str(day["day"])
                    day_container.border_subtitle = f"${round(
                        (self.BASE_RATE_PER_HOUR * 12)
                        + (self.WEEKEND_RATE_PER_HOUR * 12 if day["is_weekend"] else 0)
                        )}"
                    with day_container:
                        yield Switch(value=day["is_working"], name=f"{day["date_string"]}")

    def on_mount(self) -> None:
        # Ensure current year, previous year, and next year's calendar is prebuilt into database.
        current_year = datetime.now().year
        for increment in (-1, 0, 1):
            if not self.db_manager.year_exists(current_year + increment):
                self.db_manager.insert_full_year(current_year + increment)
        self.refresh_calendar()

    def refresh_calendar(self) -> None:
        # Construct list of days to get based on current calendar view.
        calendar_week_list = Calendar()
        calendar_week_list.setfirstweekday(calendar.SUNDAY)
        calendar_week_list = calendar_week_list.monthdatescalendar(
            self.selected_year, list(calendar.month_name).index(self.selected_month)
        )
        calendar_days_list = []
        for week in calendar_week_list:
            for day in week:
                calendar_days_list.append(str(day))
        self.days = self.db_manager.get_days_data(calendar_days_list)

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "select-month":
            self.selected_month = event.select.value
        if event.select.id == "select-year":
            self.selected_year = event.select.value
        self.refresh_calendar()

    def on_switch_changed(self, event: Switch.Changed) -> None:
        # Send update to database.
        date_string = event.switch.name
        column = "is_working"
        new_value = event.switch.value
        self.db_manager.update_day_info(date_string, column, new_value)
        for day in self.days:
            if day["date_string"] == date_string:
                day["is_working"] = new_value

        # Update local values if week is overtime week.
        list_of_weeks = itertools.batched(self.days, 7)
        for week in list_of_weeks:
            days_working = [day for day in week if day["is_working"]]
            if len(days_working) >= 3:
                third_shift_day = days_working[2]
                # Get the position of the last day worked.
                index_third_shift = week.index(third_shift_day)
                overtime_potential_days = list(week[index_third_shift + 1:])
                if overtime_potential_days:
                    for day in overtime_potential_days:
                        container = self.query_one(f"#container-{day["date_string"]}")
                        container.border_subtitle = f"${round(
                            (self.BASE_RATE_PER_HOUR * 12)
                            + (self.WEEKEND_RATE_PER_HOUR * 12 if day["is_weekend"] else 0)
                            + (8 * 36.15)
                            )}"
            else:
                for day in week:
                    container = self.query_one(f"#container-{day["date_string"]}")
                    container.border_subtitle = f"${round(
                        (self.BASE_RATE_PER_HOUR * 12)
                        + (self.WEEKEND_RATE_PER_HOUR * 12 if day["is_weekend"] else 0)
                        )}"






          

class WorkScheduleScreen(DatabaseScreen):

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container():
            yield CalendarView()
        yield Footer()
        