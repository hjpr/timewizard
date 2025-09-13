import sqlite3
import datetime
import time
from datetime import timedelta
from rich.console import Console
from typing import Optional

console = Console()

class DatabaseManager:

    DEFAULT_JOB_NAME = "unc_nursing"

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

    def create_expenses_table(self) -> None:
        """
        Create expenses table.
        Columns:
            id: int
            daily: bool
            weekly: bool
            biweekly: bool
            monthly: bool
            day: int
            amount: float
            name: str
        """
        table_name = "expenses"
        self._cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY ASC,
            daily BOOL NOT NULL,
            weekly BOOL NOT NULL,
            biweekly BOOL NOT NULL,
            monthly BOOL NOT NULL,
            day INTEGER,
            amount REAL NOT NULL,
            name TEXT NOT NULL,
            )         
        """
        )
        self._connection.commit()

    def create_jobs_table(self) -> None:
        """
        Create jobs table.
        """
        table_name = "jobs"
        self._cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY ASC,
            job_name TEXT NOT NULL UNIQUE,
            hourly_rate REAL NOT NULL,
            overtime_rate REAL NOT NULL,
            weekend_rate REAL NOT NULL,
            night_rate REAL NOT NULL,
            critical_rate REAL NOT NULL
            )
        """)
        self._connection.commit()

    def create_year_table(self) -> None:
        """
        Create calendar table.
        """
        table_name = "calendar"
        self._cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                date_string TEXT PRIMARY KEY NOT NULL,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                day INTEGER NOT NULL,
                is_weekend BOOL NOT NULL,
                is_working BOOL NOT NULL,
                is_overtime BOOL NOT NULL,
                worth FLOAT NOT NULL
            )
        """)
        self._connection.commit()
    
    def get_days(self, dates: list[str]) -> Optional[list[dict[str, str | int | float | bool]]]:
        """
        Given a list of dates, returns list of dicts where dicts are days.
        Columns:
            date_string: str
            year: int
            month: int
            day: int
            is_weekend: bool
            is_working: bool
            is_overtime: bool
            worth: float
        """
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
        except Exception:
            console.print_exception()

    def get_job(self, job_name: str) -> Optional[sqlite3.Row]:
        """
        Given a job name, returns row object.
        Columns:
            id: int
            job_name: str
            hourly_rate: float
            overtime_rate: float
            weekend_rate: float
            night_rate: float
            critical_rate: float
        """
        try:
            self._cursor.execute(f"""
                SELECT * FROM jobs WHERE job_name = ?
            """, (job_name,))
            row = self._cursor.fetchone()
            return row
        except Exception:
            console.print_exception()

    def insert_job(
            self,
            job_name: str,
            hourly_rate: float,
            overtime_rate: float,
            weekend_rate: float,
            night_rate: float,
            critical_rate: float
        ) -> None:
        try:
            self._cursor.execute(f"""
                INSERT INTO jobs (
                    job_name, hourly_rate, overtime_rate, weekend_rate, night_rate, critical_rate
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT (job_name) DO NOTHING
            """, (job_name, hourly_rate, overtime_rate, weekend_rate, night_rate, critical_rate))
            self._connection.commit()
        except Exception:
            console.print_exception()

    def insert_year(self, year: int) -> None:
        """
        Writes year data to table for calendar use.
        """
        date_list = []
        start_date = datetime.date(year, 1, 1)
        end_date = datetime.date(year, 12, 31)
        job = self.get_job(self.DEFAULT_JOB_NAME)

        current_date: datetime.datetime = start_date
        while current_date <= end_date:
            is_weekend = bool(current_date.weekday() >= 5)
            day_data = {
                "date_string": str(current_date),
                "year": current_date.year,
                "month": current_date.month,
                "day": current_date.day,
                "is_weekend": is_weekend,
                "is_working": False,
                "is_overtime": False,
                "worth": (job["hourly_rate"] * 12) + ((job["weekend_rate"] * 12) if is_weekend else 0)
            }
            date_list.append(day_data)
            current_date += timedelta(days=1)

        try:
            self._cursor.executemany(f"""
                INSERT INTO calendar (
                    date_string, year, month, day, is_weekend, is_working, is_overtime, worth
                ) VALUES (:date_string, :year, :month, :day, :is_weekend, :is_working, :is_overtime, :worth)
                ON CONFLICT (date_string) DO NOTHING
            """, date_list)
            self._connection.commit()
        except Exception:
            console.print_exception()

    def update_day(self, date_string: str, column: str, value: str | int | bool) -> None:
        try:
            self._cursor.execute(f"""
                UPDATE calendar SET {column} = ? WHERE date_string = ?
            """, (value, date_string))
            self._connection.commit()
        except Exception:
            console.print_exception()

    def update_job(self, job_name: str, column: str, value: str | float) -> None:
        try:
            self._cursor.execute(f"""
            UPDATE jobs SET {column} = ? WHERE job_name = ?
        """, (value, job_name))
        except Exception:
            console.print_exception()

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
    db_manager.create_jobs_table()
    db_manager.create_year_table()

    current_time = time.perf_counter()
    elapsed_ms = (current_time - last_checkpoint_time) * 1000
    console.log(f"[cyan]Table creation complete. (+{elapsed_ms:.2f}ms)[/cyan]")
    last_checkpoint_time = current_time # Update checkpoint

    # --- Section 3: Data Insertion (Conditional) ---
    if not db_manager.year_exists(2025):
        console.log("[bold yellow]No data in table, inserting year data...[/bold yellow]")
        db_manager.insert_year(2025)
    assert db_manager.year_exists(2025)
    console.log("[bold yellow]Table populated with year data properly...[/bold yellow]")

    if not db_manager.get_job("unc_nursing"):
        console.log("[bold yellow]No data in table, inserting job data...[/bold yellow]")
        db_manager.insert_job(
            "unc_nursing", 54.50, 90.65, 10.00, 5.00, 15.00
        )
    assert db_manager.get_job("unc_nursing")
    console.log("[bold yellow]Table populated with jobs data properly...[/bold yellow]")

    current_time = time.perf_counter()
    elapsed_ms = (current_time - last_checkpoint_time) * 1000
    console.log(f"[cyan]Data insertion complete. (+{elapsed_ms:.2f}ms)[/cyan]")
    last_checkpoint_time = current_time # Update checkpoint

    # --- Section 4: Data Retrieval ---
    console.log("[bold yellow]Retrieving a few dates...[/bold yellow]")
    days_data = db_manager.get_days(["2025-01-02", "2025-01-03"])
    
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