import calendar
import itertools

from calendar import Calendar
from datetime import date, datetime, timedelta
from textual import log
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.reactive import Reactive, reactive
from textual.widget import Widget
from textual.widgets import (
    Button,
    Footer,
    Header,
    Label,
    Rule,
    Select,
    Switch
)

from .database import DatabaseManager, DatabaseScreen

PAY_DAYS_BY_MONTH = {
    1: {
        date(2025, 1, 14): (date(2024, 12, 22), date(2025, 1, 4)),
        date(2025, 1, 28): (date(2025, 1, 5), date(2025, 1, 18))
    },
    2: {
        date(2025, 2, 11): (date(2025, 1, 19), date(2025, 2, 1)),
        date(2025, 2, 25): (date(2025, 2, 2), date(2025, 2, 15))
    },
    3: {
        date(2025, 3, 11): (date(2025, 2, 16), date(2025, 3, 1)),
        date(2025, 3, 25): (date(2025, 3, 2), date(2025, 3, 15))
    },
    4: {
        date(2025, 4, 8): (date(2025, 3, 16), date(2025, 3, 29)),
        date(2025, 4, 22): (date(2025, 3, 30), date(2025, 4, 12))
    },
    5: {
        date(2025, 5, 6): (date(2025, 4, 13), date(2025, 4, 26)),
        date(2025, 5, 20): (date(2025, 4, 27), date(2025, 5, 10))
    },
    6: {
        date(2025, 6, 3): (date(2025, 5, 11), date(2025, 5, 24)),
        date(2025, 6, 17): (date(2025, 5, 25), date(2025, 6, 7))
    },
    7: {
        date(2025, 7, 1): (date(2025, 6, 8), date(2025, 6, 21)),
        date(2025, 7, 15): (date(2025, 6, 22), date(2025, 7, 5)),
        date(2025, 7, 29): (date(2025, 7, 6), date(2025, 7, 19))
    },
    8: {
        date(2025, 8, 12): (date(2025, 7, 20), date(2025, 8, 2)),
        date(2025, 8, 26): (date(2025, 8, 3), date(2025, 8, 16))
    },
    9: {
        date(2025, 9, 9): (date(2025, 8, 17), date(2025, 8, 30)),
        date(2025, 9, 23): (date(2025, 8, 31), date(2025, 9, 13))
    },
    10: {
        date(2025, 10, 7): (date(2025, 9, 14), date(2025, 9, 27)),
        date(2025, 10, 21): (date(2025, 9, 28), date(2025, 10, 11))
    },
    11: {
        date(2025, 11, 4): (date(2025, 10, 12), date(2025, 10, 25)),
        date(2025, 11, 18): (date(2025, 10, 26), date(2025, 11, 8))
    },
    12: {
        date(2025, 12, 2): (date(2025, 11, 9), date(2025, 11, 22)),
        date(2025, 12, 16): (date(2025, 11, 23), date(2025, 12, 6)),
        date(2025, 12, 30): (date(2025, 12, 7), date(2025, 12, 20))
    },
}


class CalendarView(Widget):

    db_manager: DatabaseManager = DatabaseManager()
    days: Reactive[list[dict[str, str | int | bool]]] = reactive([], recompose=True)
    biweekly_pay_days: Reactive[dict[str, int]] = reactive({})
    monthly_pay: Reactive[int] = reactive(0)
    job: dict = {}
    today: datetime = datetime.today().date()
    selected_month: str = calendar.month_name[today.month]
    selected_month_int: int = today.month
    selected_year: int = today.year

    primary_color: str
    primary_color_muted: str
    secondary_color: str
    secondary_color_muted: str


    def compose(self) -> ComposeResult:
        with VerticalScroll(id="calendar-window"):
            with Container(id="calendar-container"):
                with Horizontal(classes="calendar-top"):
                    yield Select.from_values([month for month in calendar.month_name if month], value=self.selected_month, id="select-month")
                    yield Select.from_values([self.today.year - 1, self.today.year, self.today.year + 1], value=self.selected_year, id="select-year")
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
                            day_container.styles.border = ("round", self.app.get_css_variables().get("primary")) if day["date_string"] == str(self.today) else ("round", self.app.get_css_variables().get("secondary-muted"))
                            day_container.border_subtitle = f"${round(day["worth"])}"
                            with day_container:
                                yield Switch(
                                    value=day["is_working"],
                                    name=f"{day["date_string"]}",
                                    classes=f"{"switch-on" if day ["is_working"] else ""}"
                                    
                                )
                with Horizontal(id="quick-pay-summary"):
                    for date, amount in self.biweekly_pay_days.items():
                        with Container(classes="pay-week"):
                            label = Label(
                                f"Pay {date[5:]}",
                                id=f"payday-{date}"
                            )
                            label.styles.background = self.app.get_css_variables().get("secondary-muted")
                            yield label
                            yield Label(
                                f"Net: ${round(amount)}",
                                id=f"pay-{date}")
                            yield Label(
                                f"Taxed: ${round(amount - (amount * .31))}",
                                id=f"taxed-{date}"
                            )
                    with Container(classes="pay-week"):
                        label = Label("Total")
                        label.styles.background = self.app.get_css_variables().get("secondary-muted")
                        yield label
                        yield Label(
                            f"Month: ${round(self.monthly_pay)}",
                            id="monthly-pay"
                        )
                        yield Label(
                            f"Taxed: ${round(self.monthly_pay - (self.monthly_pay * .31))}",
                            id="monthly-pay-taxed"
                        )

    def on_mount(self) -> None:
        """Runs list of functions when mounting the widget."""
        self.primary_color = self.app.get_css_variables().get("primary")
        self.primary_color_muted = self.app.get_css_variables().get("primary-muted")
        self.secondary_color = self.app.get_css_variables().get("secondary")
        self.secondary_color_muted = self.app.get_css_variables().get("secondary-muted")

        # Ensure current year, previous year, and next year's calendar is prebuilt into database.
        current_year = datetime.now().year
        for increment in (-1, 0, 1):
            if not self.db_manager.year_exists(current_year + increment):
                self.db_manager.insert_year(current_year + increment)

        self.refresh_calendar()
        self.job = self.db_manager.get_job("unc_nursing") # Job data for pay rates
        self.calculate_pay_day_pay()

    def on_select_changed(self, event: Select.Changed) -> None:
        """fires when any select menu is set."""
        if event.select.id == "select-month":
            self.selected_month = event.select.value
            self.selected_month_int = list(calendar.month_name).index(self.selected_month)
        if event.select.id == "select-year":
            self.selected_year = event.select.value

        self.refresh_calendar()
        self.refresh_pay_subtitle()
        self.calculate_pay_day_pay()

    def on_switch_changed(self, event: Switch.Changed) -> None:
        """Fires when any switch is actuated."""
        if event.value:
            event.switch.add_class("switch-on")
        else:
            event.switch.remove_class("switch-on")

        date_string = event.switch.name
        column = "is_working"
        new_value = event.switch.value
        # Update is_working column in the db
        self.db_manager.update_day(date_string, column, new_value)
        for day in self.days:
            if day["date_string"] == date_string:
                day["is_working"] = new_value

        self.refresh_pay_subtitle()
        self.calculate_pay_day_pay()

    def watch_biweekly_pay_days(self) -> None:
        """Fires when biweekly pay gets newly set."""
        for week_str, amount in self.biweekly_pay_days.items():
            try:
                label = self.query_one(f"#payday-{week_str}", Label)
                label.update(f"Pay {week_str[5:]}")
                label = self.query_one(f"#pay-{week_str}", Label)
                label.update(f"Net: ${round(amount)}")
                label = self.query_one(f"#taxed-{week_str}", Label)
                label.update(f"Actual: ${round(amount - (amount * .24))}")
            except Exception:
                # This can happen if the widget hasn't been mounted yet, so we can safely ignore it.
                pass

    def watch_monthly_pay(self) -> None:
        """Fires when monthly pay gets newly set."""
        try:
            label = self.query_one("#monthly-pay", Label)
            label.update(f"Month: ${round(self.monthly_pay)}")
            label = self.query_one("#monthly-pay-taxed", Label)
            label.update(f"Taxed: ${round(self.monthly_pay - (self.monthly_pay * .24))}")
        except Exception:
            # This can happen if the widget hasn't been mounted yet, so we can safely ignore it.
            pass
                    
    def calculate_pay_day_pay(self) -> None:
        """
        Calculates the total earnings per pay period including OT, as well as monthly totals. Also accounts
        for taxes. Can tweak the biweekly pay with percentages to track ADP more closely.
        """
        biweekly_pay_days = {}
        total_monthly_pay = 0
        pay_days = PAY_DAYS_BY_MONTH[self.selected_month_int]
        pay_day_ranges: dict[str, list[dict[str, str | int | bool]]] = {}

        # For each payday in a month, build a list of days to retrieve under that payday
        for pay_day_datetime, pay_day_start_end in pay_days.items():
            date_list = []
            start_date = pay_day_start_end[0]
            end_date = pay_day_start_end[1]
            current_date = start_date
            while current_date <= end_date:
                date_list.append(str(current_date))
                current_date += timedelta(days=1)
            pay_day_ranges[str(pay_day_datetime)] = self.db_manager.get_days(date_list)
        
        # For each pay day, calc the biweekly amount including overtime
        for pay_day, list_of_days in pay_day_ranges.items():
            biweekly_pay = 0
            list_of_weeks = [list_of_days[0:7], list_of_days[7:14]]

            for week in list_of_weeks:
                days_working = [day for day in week if day["is_working"]]
                total_weekly_pay = 0
                total_hours_worked = len(days_working) * 12
                
                # Add up our base amounts.
                for day in days_working:
                    total_weekly_pay += day["worth"]

                # Add in overtime.
                if total_hours_worked >= 40:
                    overtime_hours = total_hours_worked % 40
                    total_weekly_pay += ((self.job["overtime_rate"] - self.job["hourly_rate"]) * overtime_hours)
                
                # Add week to biweekly total.
                biweekly_pay += total_weekly_pay
            
            # Add biweekly data back to our instance var.
            biweekly_pay_days[pay_day] = biweekly_pay + (biweekly_pay * 0.06) # To correct by 6-8% observed error
            total_monthly_pay += biweekly_pay

        self.biweekly_pay_days = biweekly_pay_days
        self.monthly_pay = total_monthly_pay

    def refresh_calendar(self) -> None:
        """
        Rebuilds each month based on selected_year and selected_month_int by pulling the days from the
        database and setting them to self.days.
        """
        calendar_week_list = Calendar()
        calendar_week_list.setfirstweekday(calendar.SUNDAY)
        calendar_week_list = calendar_week_list.monthdatescalendar(
            self.selected_year, self.selected_month_int
        )
        calendar_days_list = []
        for week in calendar_week_list:
            for day in week:
                calendar_days_list.append(str(day))
        self.days = self.db_manager.get_days(calendar_days_list)    

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
                    try:
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
                    except Exception:
                        # Between unmounts, can't find node so let it pass
                        pass
            else:
                try:
                    # Reset pay values for entire week to clear previous changes
                    for day in week:
                        container = self.query_one(f"#container-{day["date_string"]}")
                        container.border_subtitle = f"${round(day["worth"])}"
                except Exception:
                    # Between unmounts, can't find node so let it pass
                    pass


class WorkScheduleScreen(DatabaseScreen):

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container():
            yield CalendarView()
        yield Footer()
        