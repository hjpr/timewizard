import sqlite3
import calendar
import json
import datetime
import time
import rich
from datetime import timedelta
from rich.console import Console
from typing import List, Dict, Any, Optional, Tuple

console = Console()

class DatabaseManager:

    def __init__(self, db_path: str = "db/calendar.db") -> None:
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

    def create_year_table(self, year: int) -> None:
        """
        Create calendar table for a specific year if it doesn't exist.
        Table name dynamically includes the year.
        """
        table_name = f"calendar"
        self._cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                date_string TEXT PRIMARY KEY NOT NULL,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                day INTEGER NOT NULL,
                is_weekend BOOL NOT NULL,
                is_working BOOL NOT NULL,
                is_overtime BOOL NOT NULL
            )
        """)
        self._connection.commit()

    def build_year_calendar(self, year: int) -> dict[str, str | int | bool]:
        """
        Builds full year calendar structure for given year.

        Args:
        year (int): The year for the calendar

        Returns: 
        dict: A dictionary where keys are month numbers (1-12)
            and values are a dict of week numbers
        """
        date_list = []
        start_date = datetime.date(year, 1, 1)
        end_date = datetime.date(year, 12, 31)

        current_date: datetime.datetime = start_date
        while current_date <= end_date:
            day_data = {
                "date_string": str(current_date),
                "year": current_date.year,
                "month": current_date.month,
                "day": current_date.day,
                "is_weekend": bool(current_date.weekday() >= 5),
                "is_working": False,
                "is_overtime": False
            }
            date_list.append(day_data)
            current_date += timedelta(days=1)
        return date_list
    
    def year_exists(self, year: int) -> bool:
        """
        Checks if table is present and contains a day entry for given year.
        """
        table_name = f"calendar"

        self._cursor.execute(f"""
            SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';
        """)
        if not self._cursor.fetchone():
            return False
        
        self._cursor.execute(f"""
            SELECT date_string FROM calendar WHERE date_string = ?
        """, [f"{year}-01-01"])
        if not self._cursor.fetchone():
            return False
        
        return True
        
    def insert_full_year(self, year: int) -> None:
        """
        Writes full year data to year-specific table.
        """
        self.create_year_table(year)
        year_data = self.build_year_calendar(year)

        try:
            self._cursor.executemany(f"""
                INSERT INTO calendar (
                    date_string, year, month, day, is_weekend, is_working, is_overtime
                ) VALUES (:date_string, :year, :month, :day, :is_weekend, :is_working, :is_overtime)
                ON CONFLICT (date_string) DO NOTHING
            """, year_data)
            self._connection.commit()
        except sqlite3.OperationalError as e:
            console.log(f"Error creating year {year}: {e}")
        except Exception as e:
            console.log(f"Unexpected error while writing year data to db: {e}")

    def get_days_data(self, dates: list[str]) -> Optional[dict[str, str | int | bool]]:
        try:
            days_data = []
            for date in dates:   
                self._cursor.execute(f"""
                    SELECT * FROM calendar WHERE date_string = ?
                """, (date,))
                row = self._cursor.fetchone()
                if row:
                    column_names = [description[0] for description in self._cursor.description]
                    day_dict = dict(zip(column_names, row))
                    days_data.append(day_dict)
            return days_data
            
        except Exception as e:
            console.log(f"Unable to retrieve {date} from table calendar: {str(e)}")

    def update_day_info(self, date_string: str, column: str, value: str | int | bool) -> None:
        try:
            self._cursor.execute(f"""
                UPDATE calendar SET {column} = ? WHERE date_string = ?
            """, (value, date_string))
            self._connection.commit()
        except Exception:
            console.print_exception()


if __name__ == "__main__":
    # Initialize timers
    start_time = time.perf_counter()
    last_checkpoint_time = start_time

    # --- Section 1: Initialization ---
    console.log("[bold yellow]Initializing database...[/bold yellow]")
    db_manager: DatabaseManager = DatabaseManager()
    
    current_time = time.perf_counter()
    elapsed_ms = (current_time - last_checkpoint_time) * 1000
    console.log(f"[cyan]Initialization complete. (+{elapsed_ms:.2f}ms)[/cyan]")
    last_checkpoint_time = current_time # Update checkpoint

    # --- Section 2: Table Creation ---
    console.log("[bold yellow]Creating tables...[/bold yellow]")
    db_manager.create_year_table(2025)

    current_time = time.perf_counter()
    elapsed_ms = (current_time - last_checkpoint_time) * 1000
    console.log(f"[cyan]Table creation complete. (+{elapsed_ms:.2f}ms)[/cyan]")
    last_checkpoint_time = current_time # Update checkpoint

    # --- Section 3: Data Insertion (Conditional) ---
    if not db_manager.year_exists(2025):
        console.log("[bold yellow]No data in table, inserting year data...[/bold yellow]")
        db_manager.insert_full_year(2025)
        
        current_time = time.perf_counter()
        elapsed_ms = (current_time - last_checkpoint_time) * 1000
        console.log(f"[cyan]Data insertion complete. (+{elapsed_ms:.2f}ms)[/cyan]")
        last_checkpoint_time = current_time # Update checkpoint

    assert db_manager.year_exists(2025)
    console.log("[bold yellow]Table populated with year data properly...[/bold yellow]")

    # --- Section 4: Data Retrieval ---
    console.log("[bold yellow]Retrieving a few dates...[/bold yellow]")
    days_data = db_manager.get_days_data(["2025-01-02", "2025-01-03"])
    
    current_time = time.perf_counter()
    elapsed_ms = (current_time - last_checkpoint_time) * 1000
    console.log(f"[cyan]Data retrieval complete. (+{elapsed_ms:.2f}ms)[/cyan]")
    last_checkpoint_time = current_time # Update checkpoint
    
    assert days_data[0]["date_string"] == "2025-01-02"
    assert days_data[1]["date_string"] == "2025-01-03"

    # --- Final Summary ---
    total_elapsed_ms = (time.perf_counter() - start_time) * 1000
    console.log(f"\n[bold green]Database tests passed![/bold green]")
    console.log(f"[bold green]Total execution time: {total_elapsed_ms:.2f}ms[/bold green]")