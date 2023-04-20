from __future__ import annotations

import sys

from ..constants import DEVTOOLS_PORT
from ._run import exec_command, run_app

try:
    import click
except ImportError:
    print("Please install 'textual[dev]' to use the 'textual' command")
    sys.exit(1)

from importlib_metadata import version

from textual._import_app import AppFail, import_app
from textual.pilot import Pilot


@click.group()
@click.version_option(version("textual"))
def run():
    pass


@run.command(help="Run the Textual Devtools console.")
@click.option(
    "--port",
    "port",
    type=int,
    default=None,
    metavar="PORT",
    help=f"Port to use for the development mode console. Defaults to {DEVTOOLS_PORT}.",
)
@click.option("-v", "verbose", help="Enable verbose logs.", is_flag=True)
@click.option("-x", "--exclude", "exclude", help="Exclude log group(s)", multiple=True)
def console(port: int | None, verbose: bool, exclude: list[str]) -> None:
    """Launch the textual console."""
    import os

    from rich.console import Console

    from textual.devtools.server import _run_devtools

    console = Console()
    console.clear()
    console.show_cursor(False)
    try:
        _run_devtools(verbose=verbose, exclude=exclude, port=port)
    finally:
        console.show_cursor(True)


def _pre_run_warnings() -> None:
    """Look for and report any issues with the environment.

    This is the right place to add code that looks at the terminal, or other
    environmental issues, and if a problem is seen it should be printed so
    the developer can see it easily.
    """
    import os
    import platform

    from rich.console import Console
    from rich.panel import Panel

    console = Console()

    # Add any test/warning pair here. The list contains a tuple where the
    # first item is `True` if a problem situation is detected, and the
    # second item is a message to show the user on exit from `textual run`.
    warnings = [
        (
            (
                platform.system() == "Darwin"
                and os.environ.get("TERM_PROGRAM") == "Apple_Terminal"
            ),
            "The default terminal app on macOS is limited to 256 colors. See our FAQ for more details:\n\n"
            "https://github.com/Textualize/textual/blob/main/FAQ.md#why-doesn't-textual-look-good-on-macos",
        )
    ]

    for concerning, concern in warnings:
        if concerning:
            console.print(
                Panel.fit(
                    f"⚠️  {concern}", style="yellow", border_style="red", padding=(1, 2)
                )
            )


@run.command(
    "run",
    context_settings={
        "ignore_unknown_options": True,
    },
)
@click.argument("import_name", metavar="FILE or FILE:APP")
@click.option("--dev", "dev", help="Enable development mode.", is_flag=True)
@click.option(
    "--port",
    "port",
    type=int,
    default=None,
    metavar="PORT",
    help=f"Port to use for the development mode console. Defaults to {DEVTOOLS_PORT}.",
)
@click.option(
    "--press", "press", default=None, help="Comma separated keys to simulate press."
)
@click.option(
    "--screenshot",
    type=int,
    default=None,
    metavar="DELAY",
    help="Take screenshot after DELAY seconds.",
)
@click.option(
    "-c",
    "--command",
    "command",
    type=bool,
    default=False,
    help="Run as command rather that a file / module",
    is_flag=True,
)
@click.option(
    "-r",
    "--show-return",
    "show_return",
    type=bool,
    default=False,
    help="Show any return value on exit",
    is_flag=True,
)
def _run_app(
    import_name: str,
    dev: bool,
    port: int | None,
    press: str | None,
    screenshot: int | None,
    command: bool = False,
    show_return: bool = False,
) -> None:
    """Run a Textual app.

    The code to run may be given as a path (ending with .py) or as a Python
    import, which will load the code and run an app called "app". You may optionally
    add a colon plus the class or class instance you want to run.

    Here are some examples:

        textual run foo.py

        textual run foo.py:MyApp

        textual run module.foo

        textual run module.foo:MyApp

    If you are running a file and want to pass command line arguments, wrap the filename and arguments
    in quotes:

        textual run "foo.py arg --option"

    If your Textual app isn't easily accessible via a script or import, you can add the -c switch

        textual run -c "textual colors"
    """

    import os

    from textual.features import parse_features

    environment = dict(os.environ)

    features = set(parse_features(environment.get("TEXTUAL", "")))
    if dev:
        features.add("debug")
        features.add("devtools")

    environment["TEXTUAL"] = ",".join(sorted(features))
    if port is not None:
        environment["TEXTUAL_DEVTOOLS_PORT"] = str(port)
    if press is not None:
        environment["TEXTUAL_PRESS"] = str(press)
    if screenshot is not None:
        environment["TEXTUAL_SCREENSHOT"] = str(screenshot)
    environment["TEXTUAL_SHOW_RETURN"] = "1" if show_return else "0"

    _pre_run_warnings()

    if command:
        exec_command(import_name, environment)
    else:
        run_app(import_name, environment)


@run.command("borders")
def borders():
    """Explore the border styles available in Textual."""
    from textual.cli.previews import borders

    borders.app.run()


@run.command("easing")
def easing():
    """Explore the animation easing functions available in Textual."""
    from textual.cli.previews import easing

    easing.app.run()


@run.command("colors")
def colors():
    """Explore the design system."""
    from textual.cli.previews import colors

    colors.app.run()


@run.command("keys")
def keys():
    """Show key events."""
    from textual.cli.previews import keys

    keys.app.run()


@run.command("diagnose")
def run_diagnose():
    """Print information about the Textual environment"""
    from textual.cli.tools.diagnose import diagnose

    diagnose()
