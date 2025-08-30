from database_manager import DatabaseManager
from textual.screen import Screen

class DatabaseScreen(Screen):
    """
    Screen with access to a sqlite database via db_manager.
    """

    db_manager: DatabaseManager

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_manager = DatabaseManager()
