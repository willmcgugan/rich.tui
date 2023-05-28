from __future__ import annotations

from textual.widgets import Static


class Tooltip(Static):
    DEFAULT_CSS = """
    Tooltip {
        margin: 1 2;
        padding: 1 2;
        background: $panel;
        width: auto;
        height: auto;
        overlay: screen;
        constrain: inflect;
        max-width: 40;
        display: none;

    }
    """
