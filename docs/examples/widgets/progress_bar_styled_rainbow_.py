from textual.app import App, ComposeResult
from textual.containers import Center, Middle
from textual.timer import Timer
from textual.widgets import Footer, ProgressBar


class StyledExtProgressBar(App[None]):
    BINDINGS = [
        ("s", "start", "Start"),
    ]
    CSS_PATH = "progress_bar_styled_rainbow.css"

    progress_timer: Timer
    """Timer to simulate progress happening."""

    def compose(self) -> ComposeResult:
        with Center():
            with Middle():
                yield ProgressBar(color_scheme="rainbow")
        yield Footer()

    def on_mount(self) -> None:
        """Set up a timer to simulate progess happening."""
        self.progress_timer = self.set_interval(1 / 10, self.make_progress, pause=True)

    def make_progress(self) -> None:
        """Called automatically to advance the progress bar."""
        self.query_one(ProgressBar).advance(1)

    def action_start(self) -> None:
        """Start the progress tracking."""
        self.query_one(ProgressBar).update(total=100)
        self.progress_timer.resume()

    def key_1(self) -> None:
        self._action_common_keypress(10)

    def key_5(self) -> None:
        self._action_common_keypress(50)

    def key_9(self) -> None:
        self._action_common_keypress(90)

    def _action_common_keypress(self, progress: int) -> None:
        # Freeze time for the indeterminate progress bar.
        self.query_one(ProgressBar).query_one("#eta")._get_elapsed_time = lambda: 0
        self.query_one(ProgressBar).update(total=100, progress=progress)
        self.progress_timer.pause()

if __name__ == "__main__":
    app = StyledExtProgressBar()
    app.run()
