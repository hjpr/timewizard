import sqlite3
import calendar
import json
from datetime import datetime
from rich.console import Console
from typing import List, Dict, Any, Optional, Tuple

console = Console()

class DatabaseManager:

    def __init__(self, db_path: str = "/db/calendar.db") -> None:
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None
        self._cursor: Optional[sqlite3.Cursor] = None
        self._connect()

    def _connect(self) -> None:
        """Connect to on-disk SQLite db."""
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path)
            self._connection.row_factory = sqlite3.Row
            self._cursor = self._connection.cursor()

    def close(self) -> None:
        """Close db connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
            self._cursor = None

    def _create_year_table(self, year: int) -> None:
        """
        Create calendar table for a specific year if it doesn't exist.
        Table name dynamically includes the year.
        """
        table_name = f"calendar_{year}"
        self._cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                month INTEGER NOT NULL UNIQUE, -- Month should be unique within a year table
                weeks TEXT NOT NULL
            )
        """)
        self._connection.commit()

    def build_year_calendar(self, year: int) -> dict:
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
            year_calendar[month] = self.build_month_calendar(year, month)

    @staticmethod
    def build_month_calendar(year: int, month: int) -> dict[int, list[dict[str, int | bool | datetime.date]]]:
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
        month_dict: dict[int, list[dict[str, int | str | bool | float | datetime.date]]] = {}
        calendar_instance = calendar.Calendar(firstweekday=calendar.SUNDAY)
        calendar_structure = calendar_instance.monthdatescalendar(year, month) # [1]

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
    
    def insert_full_year(self, year: int) -> None:
        """
        Writes full year data to year-specific table.
        """
        self._create_year_table(year)
        table_name = f"calendar_{year}"

        year_data = self.build_year_calendar(year)

        data_to_insert = []
        for month_num, month_weeks_data in year_data.items():
            serialized_weeks = json.dumps(month_weeks_data)
            data_to_insert.append(
                month_num, serialized_weeks
            )
        try:
            self._cursor.executemany(f"""
                INSERT OR IGNORE INTO {table_name} (month, weeks)
                VALUES (?, ?)

            """, data_to_insert)
            self._connection.commit()
        except sqlite3.OperationalError as e:
            console.log(f"Error creating table {table_name}: {e}")
        except Exception as e:
            console.log(f"Unexpected error while writing year data to db: {e}")

    def get_month_data(self, year: int, month: int) -> Optional[dict[int, list[dict[str, Any]]]]:
        """
        Retrieves month's calendar data from the database and deserializes it

        Args:
            year (int): year
            month (int): month (1-12)

        Returns:
            Optional[dict]: Dictionary representing the months calendar, or None 
                if month data is not found.
        """
        table_name = f"calendar_{year}"
        try:
            self._cursor.execute(f"""
                SELECT weeks FROM {table_name} WHERE month = ?
            """, [month])
            row = self._cursor.fetchone()
            if row:
                serialized_weeks = row["weeks"]
                return json.loads(serialized_weeks)
        except sqlite3.OperationalError as e:
            console.log(f"Error accessing table {table_name}: {e}")
        
    def write_month_data(self, year: int, month: int, month_data: dict[int, list[dict[str, Any]]]) -> bool:
        """
        Serializes the given month_data and writes back to database for specified year and month.

        Args:
            year (int): year.
            month (int): month (1-12).
            month_data (dict): Dictionary containing month calendar data after modifications.

        Returns:
            bool: True if update successful, otherwise False.
        """
        table_name = f"calendar_{year}"
        try:
            serialized_weeks = json.dumps(month_data)
            self._cursor.execute(f"""
                UPDATE {table_name}
                SET weeks = ?
                WHERE month = ?
            """, (serialized_weeks, month))
            self._connection.commit()
            if self._cursor.rowcount > 0:
                console.log(f"Updated {table_name} at month: {month}, year: {year}")
                return True
            else:
                return False
        except sqlite3.OperationalError as e:
            console.log(f"Error updating table {table_name}: {e}")
            return False
        except Exception as e:
            console.log(f"Unexpected error while writing month data to db: {e}")
