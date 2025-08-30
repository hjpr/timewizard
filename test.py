import calendar
import rich
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from rich.console import Console

console = Console()


def build_year_calendar(year: int) -> dict[int, dict[int, list[dict[str, Any]]]]:
    """
    Builds full year calendar structure for given year.

    Args:
    year (int): The year for the calendar

    Returns:
    dict: A dictionary where keys are month numbers (1-12)
        and values are a dict of week numbers
    """
    year_calendar = {}
    for month in range(1, 13):
        year_calendar[month] = build_month_calendar(year, month)
    return year_calendar


def build_month_calendar(year: int, month: int) -> dict[int, list[dict[str, Any]]]:
    """
    Builds a calendar structure for a given month and year,
    including day details and timestamps.

    Args:
    year (int): The year for the calendar.
    month (int): The month for the calendar (1-12).

    Returns:
    dict: A dictionary where keys are week numbers (1-indexed)
            and values are lists of dictionaries, each representing a day.
    """
    month_dict: dict[
        int, list[dict[str, int | str | bool | float | datetime.date]]
    ] = {}
    calendar_instance = calendar.Calendar(firstweekday=calendar.SUNDAY)
    calendar_structure = calendar_instance.monthdatescalendar(year, month)  # [1]

    for week_num, week_of_dates in enumerate(calendar_structure, start=1):
        full_week = []

        for index, date_obj in enumerate(week_of_dates):
            day_month = date_obj.month
            day_day = date_obj.day
            day_year = date_obj.year

            is_weekend = date_obj.weekday() in (5, 6)

            day_info = {
                "index": index,
                "year": day_year,
                "month": day_month,
                "day": day_day,
                "is_weekend": is_weekend,
                "is_working": False,
                "is_overtime": False,
                "date_string": str(date_obj),
            }
            full_week.append(day_info)

        month_dict[week_num] = full_week

    return month_dict


# Print a portion of the calendar data to see the structure
try:
    console.log(build_year_calendar(2024))
except:
    console.print_exception(show_locals=True)
