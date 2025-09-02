import calendar
import itertools

from calendar import Calendar
from datetime import datetime
from textual import log
from textual.app import ComposeResult
from textual.color import Color
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

class CalendarView(Widget):

    db_manager: DatabaseManager = DatabaseManager()
    days: Reactive[list[dict[str, str | int | bool]]] = reactive([], recompose=True)
    working_days_by_week: Reactive[dict[str, list[dict]]] = reactive({}, recompose=True)
    pay_by_week: Reactive[dict[str, int]] = reactive({}, repaint=True)
    job: dict = {}
    today: datetime = datetime.today().date()
    today_month: int = today.month
    today_year: int = today.year
    selected_month: str = calendar.month_name[today_month]
    selected_month_int: int = today_month
    selected_year: int = today_year
    week_1: str = ""

    def compose(self):
        with VerticalScroll(id="calendar-window"):
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
                list_of_weeks = itertools.batched(self.days, 7)
                for week in list_of_weeks:
                    with Container(classes="calendar-weeks"):
                        for day in week:
                            day_container = Container(classes="day-container", id=f"container-{day['date_string']}")
                            day_container.border_title = str(day["day"])
                            day_container.border_subtitle = f"${round(day["worth"])}"
                            with day_container:
                                yield Switch(value=day["is_working"], name=f"{day["date_string"]}")
                with Horizontal(id="quick-pay-summary"):
                    for index,_ in enumerate(itertools.batched(self.days, 7), start=1):
                        with Container(classes="pay-week"):
                            yield Label(f"Week {index}")
                            yield Label(
                                f"${self.pay_by_week.get(f"week-{index}-pay", "")}",
                                id=f"week-{index}-pay")
                    with Container(classes="pay-week"):
                        yield Label("Total")
                        yield Label(
                            f"${self.pay_by_week.get(f"total-pay", "UNDEFINED")}",
                            id=f"total-pay")

    def on_mount(self) -> None:
        # Ensure current year, previous year, and next year's calendar is prebuilt into database.
        current_year = datetime.now().year
        for increment in (-1, 0, 1):
            if not self.db_manager.year_exists(current_year + increment):
                self.db_manager.insert_year(current_year + increment)

        # Pull calendar data into instance and recompose.
        self.refresh_calendar()

        # Set working days by week.
        list_of_weeks = itertools.batched(self.days, 7)
        for index, week in enumerate(list_of_weeks, start=1):
            days_working = [day for day in week if day["is_working"]]
            self.working_days_by_week[f"week-{index}"] = days_working
        
        # Pull job data into instance.
        self.job = self.db_manager.get_job("unc_nursing")

        # Calculate weekly pay from working days.
        self.calculate_weekly_pay()


    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle select changed events."""
        if event.select.id == "select-month":
            self.selected_month = event.select.value
        if event.select.id == "select-year":
            self.selected_year = event.select.value

        self.refresh_calendar()

        # Add days working by week so we can do calcs for total week income.
        list_of_weeks = itertools.batched(self.days, 7)
        for index, week in enumerate(list_of_weeks, start=1):
            days_working = [day for day in week if day["is_working"]]
            self.working_days_by_week[f"week-{index}"] = days_working

        self.refresh_pay_subtitle()
        self.calculate_weekly_pay()

    def on_switch_changed(self, event: Switch.Changed) -> None:
        """Handle switch changed events."""
        date_string = event.switch.name
        column = "is_working"
        new_value = event.switch.value

        # Update the db, local state, and rewrite the subtitles for pay/OT.
        self.db_manager.update_day(date_string, column, new_value)
        for day in self.days:
            if day["date_string"] == date_string:
                day["is_working"] = new_value
        
        # Add days working by week so we can do calcs for total week income.
        list_of_weeks = itertools.batched(self.days, 7)
        for index, week in enumerate(list_of_weeks, start=1):
            days_working = [day for day in week if day["is_working"]]
            self.working_days_by_week[f"week-{index}"] = days_working

        self.refresh_pay_subtitle()
        self.calculate_weekly_pay()

    def watch_pay_by_week(self, new_pay: dict[str, int]) -> None:
            """Called when the pay_by_week reactive is updated."""
            for week_id, pay_value in new_pay.items():
                try:
                    label = self.query_one(f"#{week_id}", Label)
                    label.update(f"${round(pay_value)}")
                except Exception:
                    # This can happen if the widget hasn't been mounted yet, so we can safely ignore it.
                    pass

    def calculate_weekly_pay(self) -> None:
        total_monthly_pay = 0
        new_pay_by_week = {}
        for week_name, days_working in self.working_days_by_week.items():
            total_weekly_pay = 0
            total_hours_worked = len(days_working) * 12

            # Add up our base amounts.
            for day in days_working:
                total_weekly_pay += day["worth"]

            # Add in overtime.
            if total_hours_worked >= 40:
                overtime_hours = total_hours_worked % 40
                total_weekly_pay += ((self.job["overtime_rate"] - self.job["hourly_rate"]) * overtime_hours)

            # Add back to instance dict.
            new_pay_by_week[f"{week_name}-pay"] = total_weekly_pay

        # Add all our weeks for a total monthly amount
        for _, amount in new_pay_by_week.items():
            total_monthly_pay += amount
        new_pay_by_week["total-pay"] = total_monthly_pay

        # Round everything for a neater look
        rounded_pay_dict = {key: round(value) for key, value in new_pay_by_week.items()}
        self.pay_by_week = rounded_pay_dict
                    
    def refresh_pay_subtitle(self) -> None:
        """Update subtitle pay values if week is overtime week."""
        list_of_weeks = itertools.batched(self.days, 7)
        for index, week in enumerate(list_of_weeks, start=1):
            days_working = [day for day in week if day["is_working"]]

            if len(days_working) >= 3:
                third_shift_day = days_working[2]
                # Get the position of the last day worked.
                index_third_shift = week.index(third_shift_day)
                overtime_potential_days = list(week[index_third_shift + 1:])
                if overtime_potential_days:
                    for index, day in enumerate(overtime_potential_days, start=1):
                        # First day is 4 hours of regular and 8 hours ot.
                        if index == 1:
                            container = self.query_one(f"#container-{day["date_string"]}")
                            container.border_subtitle = f"${round(
                                day["worth"]
                                + ((self.job["overtime_rate"] - self.job["hourly_rate"]) * 8)
                            )}"
                        # Days past the first day are full 12 hours ot.
                        else:
                            container = self.query_one(f"#container-{day["date_string"]}")
                            container.border_subtitle = f"${round(
                                day["worth"]
                                + ((self.job["overtime_rate"] - self.job["hourly_rate"]) * 12)
                            )}"
            else:
                # Reset pay values for entire week to clear previous changes
                for day in week:
                    try:
                        container = self.query_one(f"#container-{day["date_string"]}")
                        container.border_subtitle = f"${round(day["worth"])}"
                    except Exception:
                        # Between unmounts, can't find node so let it pass
                        pass
                    
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
        self.days = self.db_manager.get_days(calendar_days_list)


class WorkScheduleScreen(DatabaseScreen):

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container():
            yield CalendarView()
        yield Footer()
        