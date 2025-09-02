from textual import log
from textual.app import App, ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen, Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Label,
)
from screens.finances import FinancesScreen
from screens.monthly_summary import MonthlySummaryScreen
from screens.projects import ProjectsScreen
from screens.work_schedule import WorkScheduleScreen

class QuitScreen(ModalScreen):
    """Screen with a dialog to quit."""

    def compose(self) -> ComposeResult:
        yield Grid(
            Label("Are you sure you want to quit?", id="question"),
            Button("Quit", variant="error", id="quit"),
            Button("Cancel", variant="primary", id="cancel"),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit":
            self.app.exit()
        else:
            self.app.pop_screen()


class MainScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()


class TimeWizardApp(App):
    BINDINGS = [
        ("escape", "switch_mode_or_quit", "Back"),
        ("w", "switch_mode('work_schedule')", "Work Schedule"),
        ("f", "switch_mode('finances')", "Finances"),
        ("p", "switch_mode('projects')", "Projects"),
        ("m", "switch_mode('monthly_summary')", "Monthly Summary"),
    ]
    CSS_PATH = [
        "tcss/finances.tcss",
        "tcss/monthly_summary.tcss",
        "tcss/projects.tcss",
        "tcss/work_schedule.tcss",
    ]
    MODES = {
        "main": MainScreen,
        "work_schedule": WorkScheduleScreen,
        "finances": FinancesScreen,
        "projects": ProjectsScreen,
        "monthly_summary": MonthlySummaryScreen,
    }

    def action_switch_mode_or_quit(self) -> None:
        """If user on the main screen, exit, else go back to main screen."""
        if self.current_mode == "main":
            self.app.push_screen(QuitScreen())
        else:
            self.switch_mode("main")

    def on_mount(self) -> None:
        self.theme = "catppuccin-mocha"
        self.title = "TIMEWIZARD"
        self.sub_title = "Yer an' adult Harry!"
        self.switch_mode("main")


if __name__ == "__main__":
    app = TimeWizardApp()
    app.run()
