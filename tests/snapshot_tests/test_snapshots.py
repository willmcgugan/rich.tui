from __future__ import annotations

from pathlib import Path

import pytest
from rich.panel import Panel
from rich.text import Text

from tests.snapshot_tests.language_snippets import SNIPPETS
from textual import events
from textual._on import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.command import SimpleCommand
from textual.containers import (
    Center,
    Container,
    Grid,
    Horizontal,
    Middle,
    Vertical,
    VerticalGroup,
    VerticalScroll,
    HorizontalGroup,
)
from textual.content import Content
from textual.pilot import Pilot
from textual.reactive import var
from textual.renderables.gradient import LinearGradient
from textual.screen import ModalScreen, Screen
from textual.widgets import (
    Button,
    Collapsible,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    Log,
    OptionList,
    Placeholder,
    ProgressBar,
    RadioSet,
    RichLog,
    Select,
    SelectionList,
    Static,
    Switch,
    Tab,
    Tabs,
    TextArea,
    TabbedContent,
    TabPane,
)
from textual.theme import Theme
from textual.widgets.text_area import BUILTIN_LANGUAGES, Selection, TextAreaTheme

# These paths should be relative to THIS directory.
WIDGET_EXAMPLES_DIR = Path("../../docs/examples/widgets")
LAYOUT_EXAMPLES_DIR = Path("../../docs/examples/guide/layout")
STYLES_EXAMPLES_DIR = Path("../../docs/examples/styles")
EXAMPLES_DIR = Path("../../examples")
SNAPSHOT_APPS_DIR = Path("./snapshot_apps")


# --- Layout related stuff ---


def test_grid_layout_basic(snap_compare):
    assert snap_compare(LAYOUT_EXAMPLES_DIR / "grid_layout1.py")


def test_grid_layout_basic_overflow(snap_compare):
    assert snap_compare(LAYOUT_EXAMPLES_DIR / "grid_layout2.py")


def test_grid_layout_gutter(snap_compare):
    assert snap_compare(LAYOUT_EXAMPLES_DIR / "grid_layout7_gutter.py")


def test_layers(snap_compare):
    assert snap_compare(LAYOUT_EXAMPLES_DIR / "layers.py")


def test_horizontal_layout(snap_compare):
    assert snap_compare(LAYOUT_EXAMPLES_DIR / "horizontal_layout.py")


def test_horizontal_layout_width_auto_dock(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "horizontal_auto_width.py")


def test_vertical_layout(snap_compare):
    assert snap_compare(LAYOUT_EXAMPLES_DIR / "vertical_layout.py")


def test_dock_layout_sidebar(snap_compare):
    assert snap_compare(LAYOUT_EXAMPLES_DIR / "dock_layout2_sidebar.py")


def test_layout_containers(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "layout_containers.py")


def test_alignment_containers(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "alignment_containers.py")


# --- Widgets - rendering and basic interactions ---
# Each widget should have a canonical example that is display in the docs.
# When adding a new widget, ideally we should also create a snapshot test
# from these examples which test rendering and simple interactions with it.


def test_switches(snap_compare):
    """Tests switches but also acts a regression test for using
    width: auto in a Horizontal layout context."""
    press = [
        "shift+tab",
        "enter",  # toggle off
        "shift+tab",
        "wait:20",
        "enter",  # toggle on
        "wait:20",
    ]
    assert snap_compare(WIDGET_EXAMPLES_DIR / "switch.py", press=press)


def test_input_and_focus(snap_compare):
    press = [
        *"Darren",  # Write "Darren"
        "tab",
        *"Burns",  # Focus second input, write "Burns"
    ]
    assert snap_compare(WIDGET_EXAMPLES_DIR / "input.py", press=press)


def test_input_validation(snap_compare):
    """Checking that invalid styling is applied. The snapshot app itself
    also adds styling for -valid which gives a green border."""
    press = [
        *"-2",  # -2 is invalid, so -invalid should be applied
        "tab",
        "3",  # This is valid, so -valid should be applied
        "tab",
        *"-2",
        # -2 is invalid, so -invalid should be applied (and :focus, since we stop here)
    ]
    assert snap_compare(SNAPSHOT_APPS_DIR / "input_validation.py", press=press)


def test_input_suggestions(snap_compare):
    async def run_before(pilot):
        pilot.app.query(Input).first().cursor_blink = False

    assert snap_compare(
        SNAPSHOT_APPS_DIR / "input_suggestions.py", press=["b"], run_before=run_before
    )


def test_input_setting_value(snap_compare):
    """Test that Inputs with different values are rendered correctly.

    The values of inputs should be (from top to bottom): "default", "set attribute in compose"
    , "" (empty), a placeholder of 'Placeholder, no value', and "set in on_mount".
    """

    class InputApp(App[None]):
        def compose(self) -> ComposeResult:
            yield Input(value="default")
            input2 = Input()
            input2.value = "set attribute in compose"
            yield input2
            yield Input()
            yield Input(placeholder="Placeholder, no value")
            yield Input(id="input3")

        def on_mount(self) -> None:
            input3 = self.query_one("#input3", Input)
            input3.value = "set in on_mount"

    assert snap_compare(InputApp())


def test_input_cursor(snap_compare):
    """The first input should say こんにちは.
    The second input should say こんにちは, with a cursor on the final character (double width).
    Note that this might render incorrectly in the SVG output - the letters may overlap.
    """

    class InputApp(App[None]):
        def compose(self) -> ComposeResult:
            yield Input(value="こんにちは")
            input = Input(value="こんにちは", select_on_focus=False)
            input.focus()
            input.action_cursor_left()
            yield input

    assert snap_compare(InputApp())


def test_input_scrolls_to_cursor(snap_compare):
    """The input widget should scroll the cursor into view when it moves,
    and this should account for different cell widths.

    Only the final two characters should be visible in the first input (ちは).
    They might be overlapping in the SVG output.

    In the second input, we should only see numbers 5-9 inclusive, plus the cursor.
    The number of cells to the right of the cursor should equal the number of cells
    to the left of the number '5'.
    """

    class InputScrollingApp(App[None]):
        CSS = "Input { width: 12; }"

        def compose(self) -> ComposeResult:
            yield Input(id="input1")
            yield Input(id="input2")

    assert snap_compare(
        InputScrollingApp(), press=[*"こんにちは", "tab", *"0123456789"]
    )


def test_input_initial_scroll(snap_compare):
    """When the input is smaller than its content, the start of the content should
    be visible, not the end."""

    class InputInitialScrollApp(App[None]):
        AUTO_FOCUS = None

        def compose(self) -> ComposeResult:
            yield Input(value="the quick brown fox jumps over the lazy dog")

    assert snap_compare(InputInitialScrollApp(), terminal_size=(20, 5))


def test_input_selection(snap_compare):
    """BCDEF should be visible, and DEF should be selected. The cursor should be
    sitting above 'D'."""

    class InputSelectionApp(App[None]):
        CSS = "Input { width: 12; }"

        def compose(self) -> ComposeResult:
            yield Input(id="input1")

    assert snap_compare(InputSelectionApp(), press=[*"ABCDEF", *("shift+left",) * 3])


def test_masked_input(snap_compare):
    async def run_before(pilot):
        pilot.app.query(Input).first().cursor_blink = False

    assert snap_compare(
        SNAPSHOT_APPS_DIR / "masked_input.py",
        press=["A", "B", "C", "0", "1", "-", "D", "E"],
        run_before=run_before,
    )


def test_buttons_render(snap_compare):
    # Testing button rendering. We press tab to focus the first button too.
    assert snap_compare(WIDGET_EXAMPLES_DIR / "button.py", press=["tab"])


def test_placeholder_render(snap_compare):
    # Testing the rendering of the multiple placeholder variants and labels.
    assert snap_compare(WIDGET_EXAMPLES_DIR / "placeholder.py")


def test_datatable_render(snap_compare):
    press = ["tab", "down", "down", "right", "up", "left"]
    assert snap_compare(WIDGET_EXAMPLES_DIR / "data_table.py", press=press)


def test_datatable_row_cursor_render(snap_compare):
    press = ["up", "left", "right", "down", "down"]
    assert snap_compare(SNAPSHOT_APPS_DIR / "data_table_row_cursor.py", press=press)


def test_datatable_column_cursor_render(snap_compare):
    press = ["left", "up", "down", "right", "right"]
    assert snap_compare(SNAPSHOT_APPS_DIR / "data_table_column_cursor.py", press=press)


def test_datatable_sort_multikey(snap_compare):
    press = ["down", "right", "s"]  # Also checks that sort doesn't move cursor.
    assert snap_compare(SNAPSHOT_APPS_DIR / "data_table_sort.py", press=press)


def test_datatable_remove_row(snap_compare):
    press = ["r"]
    assert snap_compare(SNAPSHOT_APPS_DIR / "data_table_remove_row.py", press=press)


def test_datatable_labels_and_fixed_data(snap_compare):
    # Ensure that we render correctly when there are fixed rows/cols and labels.
    assert snap_compare(SNAPSHOT_APPS_DIR / "data_table_row_labels.py")


def test_datatable_style_ordering(snap_compare):
    # Regression test for https://github.com/Textualize/textual/issues/2061
    assert snap_compare(SNAPSHOT_APPS_DIR / "data_table_style_order.py")


def test_datatable_add_column(snap_compare):
    # Checking adding columns after adding rows
    assert snap_compare(SNAPSHOT_APPS_DIR / "data_table_add_column.py")


def test_datatable_add_row_auto_height(snap_compare):
    # Check that rows added with auto height computation look right.
    assert snap_compare(SNAPSHOT_APPS_DIR / "data_table_add_row_auto_height.py")


def test_datatable_add_row_auto_height_sorted(snap_compare):
    # Check that rows added with auto height computation look right.
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "data_table_add_row_auto_height.py", press=["s"]
    )


def test_datatable_auto_height_future_updates(snap_compare):
    """https://github.com/Textualize/textual/issues/4928 meant that when height=None,
    in add_row, future updates to the table would be incorrect.

    In this test, every 2nd row is auto height and every other row is height 2.
    The table is cleared then fully repopulated with the same 4 rows. All 4 rows
    should be visible and rendered at heights 2, 1, 2, 1.
    """
    ROWS = [
        ("foo", "bar"),
        (1, "abc"),
        (2, "def"),
        (3, "ghi"),
        (4, "jkl"),
    ]

    class ExampleApp(App[None]):
        CSS = "DataTable { border: solid red; }"

        def compose(self) -> ComposeResult:
            yield DataTable()

        def on_mount(self) -> None:
            table = self.query_one(DataTable)
            table.add_columns(*ROWS[0])
            self.populate_table()

        def key_r(self) -> None:
            self.populate_table()

        def populate_table(self) -> None:
            table = self.query_one(DataTable)
            table.clear()
            for i, row in enumerate(ROWS[1:]):
                table.add_row(
                    *row,
                    height=None if i % 2 == 1 else 2,
                )

    assert snap_compare(ExampleApp(), press=["r"])


def test_datatable_cell_padding(snap_compare):
    # Check that horizontal cell padding is respected.
    assert snap_compare(SNAPSHOT_APPS_DIR / "data_table_cell_padding.py")


def test_datatable_change_cell_padding(snap_compare):
    # Check that horizontal cell padding is respected.
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "data_table_cell_padding.py", press=["a", "b"]
    )


def test_footer_render(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "footer.py")


def test_header_render(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "header.py")


def test_list_view(snap_compare):
    assert snap_compare(
        WIDGET_EXAMPLES_DIR / "list_view.py", press=["tab", "down", "down", "up"]
    )


def test_log_write_lines(snap_compare):
    assert snap_compare("snapshot_apps/log_write_lines.py")


def test_log_write(snap_compare):
    assert snap_compare("snapshot_apps/log_write.py")


def test_fr_units(snap_compare):
    assert snap_compare("snapshot_apps/fr_units.py")


def test_visibility(snap_compare):
    assert snap_compare("snapshot_apps/visibility.py")


def test_tree_example(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "tree.py")


def test_markdown_example(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "markdown.py")


def test_markdown_viewer_example(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "markdown_viewer.py")


def test_markdown_theme_switching(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "markdown_theme_switcher.py", press=["t"])


def test_markdown_dark_theme_override(snap_compare):
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "markdown_theme_switcher.py", press=["d", "wait:100"]
    )


def test_markdown_light_theme_override(snap_compare):
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "markdown_theme_switcher.py", press=["l", "t", "wait:100"]
    )


def test_checkbox_example(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "checkbox.py")


def test_radio_button_example(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "radio_button.py")


def test_radio_set_example(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "radio_set.py")


def test_radio_set_is_scrollable(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/5100"""

    class RadioSetApp(App):
        CSS = """
        RadioSet {
            height: 5;
        }
        """

        def compose(self) -> ComposeResult:
            yield RadioSet(*[(f"This is option #{n}") for n in range(10)])

    app = RadioSetApp()
    assert snap_compare(app, press=["up"])


def test_content_switcher_example_initial(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "content_switcher.py")


def test_content_switcher_example_switch(snap_compare):
    assert snap_compare(
        WIDGET_EXAMPLES_DIR / "content_switcher.py",
        press=["tab", "enter", "wait:500"],
        terminal_size=(50, 50),
    )


def test_tabbed_content(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "tabbed_content.py")


def test_tabbed_content_with_modified_tabs(snap_compare):
    # Tabs enabled and hidden.
    assert snap_compare(SNAPSHOT_APPS_DIR / "modified_tabs.py")


def test_tabbed_content_styling_not_leaking(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "tabbed_content_style_leak_test.py")


def test_option_list_strings(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "option_list_strings.py")


def test_option_list_options(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "option_list_options.py")


def test_option_list_tables(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "option_list_tables.py")


def test_option_list_build(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "option_list.py")


def test_option_list_replace_prompt_from_single_line_to_single_line(snap_compare):
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "option_list_multiline_options.py", press=["1"]
    )


def test_option_list_replace_prompt_from_single_line_to_two_lines(snap_compare):
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "option_list_multiline_options.py", press=["2"]
    )


def test_option_list_replace_prompt_from_two_lines_to_three_lines(snap_compare):
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "option_list_multiline_options.py", press=["3"]
    )


def test_option_list_scrolling_in_long_list(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "option_list_long.py", press=["up"])


def test_progress_bar_indeterminate(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "progress_bar_isolated_.py", press=["f"])


def test_progress_bar_indeterminate_styled(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "progress_bar_styled_.py", press=["f"])


def test_progress_bar_halfway(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "progress_bar_isolated_.py", press=["t"])


def test_progress_bar_halfway_styled(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "progress_bar_styled_.py", press=["t"])


def test_progress_bar_completed(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "progress_bar_isolated_.py", press=["u"])


def test_progress_bar_completed_styled(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "progress_bar_styled_.py", press=["u"])


def test_rule_horizontal_rules(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "horizontal_rules.py")


def test_rule_vertical_rules(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "vertical_rules.py")


def test_select(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "select_widget.py")


def test_selection_list_selected(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "selection_list_selected.py")


def test_selection_list_selections(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "selection_list_selections.py")


def test_selection_list_tuples(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "selection_list_tuples.py")


def test_select_expanded(snap_compare):
    assert snap_compare(
        WIDGET_EXAMPLES_DIR / "select_widget.py", press=["tab", "enter"]
    )


def test_select_from_values_expanded(snap_compare):
    assert snap_compare(
        WIDGET_EXAMPLES_DIR / "select_from_values_widget.py", press=["tab", "enter"]
    )


def test_select_expanded_changed(snap_compare):
    assert snap_compare(
        WIDGET_EXAMPLES_DIR / "select_widget.py",
        press=["tab", "enter", "down", "enter"],
    )


def test_select_no_blank_has_default_value(snap_compare):
    """Make sure that the first value is selected by default if allow_blank=False."""
    assert snap_compare(WIDGET_EXAMPLES_DIR / "select_widget_no_blank.py")


def test_select_set_options(snap_compare):
    assert snap_compare(
        WIDGET_EXAMPLES_DIR / "select_widget_no_blank.py",
        press=["s"],
    )


def test_select_type_to_search(snap_compare):
    """The select was expanded and the user typed "pi", which should match "Pigeon".

    The "Pigeon" option should be highlighted and scrolled into view.
    """

    class SelectTypeToSearch(App[None]):
        CSS = "SelectOverlay { height: 5; }"

        def compose(self) -> ComposeResult:
            values = [
                "Ostrich",
                "Penguin",
                "Duck",
                "Chicken",
                "Goose",
                "Pigeon",
                "Turkey",
            ]
            yield Select[str].from_values(values, type_to_search=True)

    async def run_before(pilot):
        await pilot.press("enter")  # Expand the select
        await pilot.press(*"pi")  # Search for "pi", which should match "Pigeon"

    assert snap_compare(SelectTypeToSearch(), run_before=run_before)


def test_sparkline_render(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "sparkline.py")


def test_sparkline_component_classes_colors(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "sparkline_colors.py")


def test_collapsible_render(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "collapsible.py")


def test_collapsible_collapsed(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "collapsible.py", press=["c"])


def test_collapsible_expanded(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "collapsible.py", press=["e"])


def test_collapsible_nested(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "collapsible_nested.py")


def test_collapsible_custom_symbol(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "collapsible_custom_symbol.py")


def test_directory_tree_reloading(snap_compare, tmp_path):
    async def run_before(pilot):
        await pilot.app.setup(tmp_path)
        await pilot.press(
            "down", "e", "e", "down", "down", "down", "down", "e", "down", "d", "r"
        )

    assert snap_compare(
        SNAPSHOT_APPS_DIR / "directory_tree_reload.py",
        run_before=run_before,
    )


# --- CSS properties ---
# We have a canonical example for each CSS property that is shown in their docs.
# If any of these change, something has likely broken, so snapshot each of them.

PATHS = [
    path.name
    for path in (Path(__file__).parent / STYLES_EXAMPLES_DIR).iterdir()
    if path.suffix == ".py"
]


@pytest.mark.parametrize("file_name", PATHS)
def test_css_property(file_name, snap_compare):
    path_to_app = STYLES_EXAMPLES_DIR / file_name
    assert snap_compare(path_to_app)


def test_viewport_height_and_width_properties(snap_compare):
    path_to_app = SNAPSHOT_APPS_DIR / "viewport_units.py"
    assert snap_compare(path_to_app)


def test_multiple_css(snap_compare):
    # Interaction between multiple CSS files and app-level/classvar CSS
    assert snap_compare("snapshot_apps/multiple_css/multiple_css.py")


def test_order_independence(snap_compare):
    assert snap_compare("snapshot_apps/layer_order_independence.py")


def test_order_independence_toggle(snap_compare):
    assert snap_compare("snapshot_apps/layer_order_independence.py", press="t")


def test_columns_height(snap_compare):
    # Interaction with height auto, and relative heights to make columns
    assert snap_compare("snapshot_apps/columns_height.py")


def test_offsets(snap_compare):
    """Test offsets of containers"""
    assert snap_compare("snapshot_apps/offsets.py")


def test_nested_auto_heights(snap_compare):
    """Test refreshing widget within a auto sized container"""
    assert snap_compare("snapshot_apps/nested_auto_heights.py", press=["1", "2"])


def test_programmatic_scrollbar_gutter_change(snap_compare):
    """Regression test for #1607 https://github.com/Textualize/textual/issues/1607

    See also tests/css/test_programmatic_style_changes.py for other related regression tests.
    """
    assert snap_compare(
        "snapshot_apps/programmatic_scrollbar_gutter_change.py", press=["s"]
    )


# --- Other ---


def test_key_display(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "key_display.py")


def test_label_widths(snap_compare):
    """Test renderable widths are calculate correctly."""
    assert snap_compare(SNAPSHOT_APPS_DIR / "label_widths.py")


def test_border_alpha(snap_compare):
    """Test setting a border alpha."""
    assert snap_compare(SNAPSHOT_APPS_DIR / "border_alpha.py")


def test_auto_width_input(snap_compare):
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "auto_width_input.py", press=["tab", *"Hello"]
    )


def test_screen_switch(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "screen_switch.py", press=["a", "b"])


def test_disabled_widgets(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "disable_widgets.py")


def test_focus_component_class(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "focus_component_class.py", press=["tab"])


def test_line_api_scrollbars(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "line_api_scrollbars.py")


def test_remove_with_auto_height(snap_compare):
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "remove_auto.py", press=["a", "a", "a", "d", "d"]
    )


def test_auto_table(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "auto-table.py", terminal_size=(120, 40))


def test_table_markup(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "table_markup.py")


def test_richlog_max_lines(snap_compare):
    assert snap_compare("snapshot_apps/richlog_max_lines.py", press=[*"abcde"])


def test_richlog_scroll(snap_compare):
    """Ensure `RichLog.auto_scroll` causes the log to scroll to the end when new content is written."""
    assert snap_compare(SNAPSHOT_APPS_DIR / "richlog_scroll.py")


def test_richlog_width(snap_compare):
    """Check that the width of RichLog is respected, even when it's not visible."""
    assert snap_compare(SNAPSHOT_APPS_DIR / "richlog_width.py", press=["p"])


def test_richlog_min_width(snap_compare):
    """The available space of this RichLog is less than the minimum width, so written
    content should be rendered at `min_width`. This snapshot should show the renderable
    clipping at the right edge, as there's not enough space to satisfy the minimum width.
    """

    class RichLogMinWidth20(App[None]):
        def compose(self) -> ComposeResult:
            rich_log = RichLog(min_width=20)
            text = Text("0123456789", style="on red", justify="right")
            rich_log.write(text)
            yield rich_log

    assert snap_compare(RichLogMinWidth20(), terminal_size=(20, 6))


def test_richlog_deferred_render_no_expand(snap_compare):
    """Check we can write to a RichLog before its size is known i.e. in `compose`."""

    class RichLogNoExpand(App[None]):
        def compose(self) -> ComposeResult:
            rich_log = RichLog(min_width=10)
            text = Text("0123456789", style="on red", justify="right")
            # Perform the write in compose - it'll be deferred until the size is known
            rich_log.write(text)
            yield rich_log

    assert snap_compare(RichLogNoExpand(), terminal_size=(20, 6))


def test_richlog_deferred_render_expand(snap_compare):
    """Check we can write to a RichLog before its size is known i.e. in `compose`.

    The renderable should expand to fill full the width of the RichLog.
    """

    class RichLogExpand(App[None]):
        def compose(self) -> ComposeResult:
            rich_log = RichLog(min_width=10)
            text = Text("0123456789", style="on red", justify="right")
            # Perform the write in compose - it'll be deferred until the size is known
            rich_log.write(text, expand=True)
            yield rich_log

    assert snap_compare(RichLogExpand(), terminal_size=(20, 6))


def test_richlog_markup(snap_compare):
    """Check that Rich markup is rendered in RichLog when markup=True."""

    class RichLogWidth(App[None]):
        def compose(self) -> ComposeResult:
            rich_log = RichLog(min_width=10, markup=True)
            rich_log.write("[black on red u]black text on red, underlined")
            rich_log.write("normal text, no markup")
            yield rich_log

    assert snap_compare(RichLogWidth(), terminal_size=(42, 6))


def test_richlog_shrink(snap_compare):
    """Ensure that when shrink=True, the renderable shrinks to fit the width of the RichLog."""

    class RichLogShrink(App[None]):
        CSS = "RichLog { width: 20; background: red;}"

        def compose(self) -> ComposeResult:
            rich_log = RichLog(min_width=4)
            panel = Panel("lorem ipsum dolor sit amet lorem ipsum dolor sit amet")
            rich_log.write(panel)
            yield rich_log

    assert snap_compare(RichLogShrink(), terminal_size=(24, 6))


def test_richlog_write_at_specific_width(snap_compare):
    """Ensure we can write renderables at a specific width.
    `min_width` should be respected, but `width` should override.

    The green label at the bottom should be equal in width to the bottom
    renderable (equal to min_width).
    """

    class RichLogWriteAtSpecificWidth(App[None]):
        CSS = """
        RichLog { width: 1fr; height: auto; }
        #width-marker { background: green; width: 50; }
        """

        def compose(self) -> ComposeResult:
            rich_log = RichLog(min_width=50)
            rich_log.write(Panel("width=20", style="black on red"), width=20)
            rich_log.write(Panel("width=40", style="black on red"), width=40)
            rich_log.write(Panel("width=60", style="black on red"), width=60)
            rich_log.write(Panel("width=120", style="black on red"), width=120)
            rich_log.write(
                Panel("width=None (fallback to min_width)", style="black on red")
            )
            yield rich_log
            width_marker = Label(
                f"this label is width 50 (same as min_width)", id="width-marker"
            )
            yield width_marker

    assert snap_compare(RichLogWriteAtSpecificWidth())


def test_richlog_highlight(snap_compare):
    """Check that RichLog.highlight correctly highlights with the ReprHighlighter.

    Also ensures that interaction between CSS and highlighting is as expected -
    non-highlighted text should have the CSS styles applied, but highlighted text
    should ignore the CSS (and use the highlights returned from the highlighter).
    """

    class RichLogHighlight(App[None]):
        # Add some CSS to check interaction with highlighting.
        CSS = """
        RichLog { color: red; background: dodgerblue 40%; }
        """

        def compose(self) -> ComposeResult:
            rich_log = RichLog(highlight=True)
            rich_log.write("Foo('bar', x=1, y=[1, 2, 3])")
            yield rich_log

    assert snap_compare(RichLogHighlight(), terminal_size=(30, 3))


def test_tabs_invalidate(snap_compare):
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "tabs_invalidate.py",
        press=["tab", "right"],
    )


def test_scrollbar_thumb_height(snap_compare):
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "scrollbar_thumb_height.py",
    )


def test_pilot_resize_terminal(snap_compare):
    async def run_before(pilot):
        await pilot.resize_terminal(35, 20)
        await pilot.resize_terminal(20, 10)

    assert snap_compare(
        SNAPSHOT_APPS_DIR / "pilot_resize_terminal.py",
        run_before=run_before,
        terminal_size=(80, 25),
    )


def test_css_hot_reloading(snap_compare, monkeypatch):
    """Regression test for https://github.com/Textualize/textual/issues/2063."""

    monkeypatch.setenv(
        "TEXTUAL", "debug"
    )  # This will make sure we create a file monitor.

    async def run_before(pilot):
        css_file = pilot.app.CSS_PATH
        with open(css_file, "w") as f:
            f.write("/* This file is purposefully empty. */\n")  # Clear all the CSS.
        await pilot.app._on_css_change()

    assert snap_compare(
        SNAPSHOT_APPS_DIR / "hot_reloading_app.py", run_before=run_before
    )


def test_css_hot_reloading_on_screen(snap_compare, monkeypatch):
    """Regression test for https://github.com/Textualize/textual/issues/3454."""

    monkeypatch.setenv(
        "TEXTUAL", "debug"
    )  # This will make sure we create a file monitor.

    async def run_before(pilot):
        css_file = pilot.app.screen.CSS_PATH
        with open(css_file, "w") as f:
            f.write("/* This file is purposefully empty. */\n")  # Clear all the CSS.
        await pilot.app._on_css_change()

    assert snap_compare(
        SNAPSHOT_APPS_DIR / "hot_reloading_app_with_screen_css.py",
        run_before=run_before,
    )


def test_datatable_hot_reloading(snap_compare, monkeypatch):
    """Regression test for https://github.com/Textualize/textual/issues/3312."""

    monkeypatch.setenv(
        "TEXTUAL", "debug"
    )  # This will make sure we create a file monitor.

    async def run_before(pilot):
        css_file = pilot.app.CSS_PATH
        with open(css_file, "w") as f:
            f.write("/* This file is purposefully empty. */\n")  # Clear all the CSS.
        await pilot.app._on_css_change()

    assert snap_compare(
        SNAPSHOT_APPS_DIR / "datatable_hot_reloading.py", run_before=run_before
    )


def test_markdown_component_classes_reloading(snap_compare, monkeypatch):
    """Tests all markdown component classes reload correctly.

    See https://github.com/Textualize/textual/issues/3464."""

    monkeypatch.setenv(
        "TEXTUAL", "debug"
    )  # This will make sure we create a file monitor.

    async def run_before(pilot):
        css_file = pilot.app.CSS_PATH
        with open(css_file, "w") as f:
            f.write("/* This file is purposefully empty. */\n")  # Clear all the CSS.
        await pilot.app._on_css_change()

    assert snap_compare(
        SNAPSHOT_APPS_DIR / "markdown_component_classes_reloading.py",
        run_before=run_before,
    )


def test_markdown_space_squashing(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "markdown_whitespace.py")


def test_layer_fix(snap_compare):
    # Check https://github.com/Textualize/textual/issues/1358
    assert snap_compare(SNAPSHOT_APPS_DIR / "layer_fix.py", press=["d"])


def test_modal_dialog_bindings_input(snap_compare):
    # Check https://github.com/Textualize/textual/issues/2194
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "modal_screen_bindings.py",
        press=["enter", "h", "!", "left", "i", "tab"],
    )


def test_modal_dialog_bindings(snap_compare):
    # Check https://github.com/Textualize/textual/issues/2194
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "modal_screen_bindings.py",
        press=["enter", "tab", "h", "i", "tab", "enter"],
    )


def test_dock_scroll(snap_compare):
    # https://github.com/Textualize/textual/issues/2188
    assert snap_compare(SNAPSHOT_APPS_DIR / "dock_scroll.py", terminal_size=(80, 25))


def test_dock_scroll2(snap_compare):
    # https://github.com/Textualize/textual/issues/2525
    assert snap_compare(SNAPSHOT_APPS_DIR / "dock_scroll2.py", terminal_size=(80, 25))


def test_dock_scroll_off_by_one(snap_compare):
    # https://github.com/Textualize/textual/issues/2525
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "dock_scroll_off_by_one.py",
        terminal_size=(80, 25),
    )


def test_dock_none(snap_compare):
    """Checking that `dock:none` works in CSS and Python.
    The label should appear at the top here, since we've undocked both
    the header and footer.
    """

    class DockNone(App[None]):
        CSS = "Header { dock: none; }"

        def compose(self) -> ComposeResult:
            yield Label("Hello")
            yield Header()
            footer = Footer()
            footer.styles.dock = "none"
            yield footer

    assert snap_compare(DockNone(), terminal_size=(30, 5))


def test_scroll_to(snap_compare):
    # https://github.com/Textualize/textual/issues/2525
    assert snap_compare(SNAPSHOT_APPS_DIR / "scroll_to.py", terminal_size=(80, 25))


def test_auto_fr(snap_compare):
    # https://github.com/Textualize/textual/issues/2220
    assert snap_compare(SNAPSHOT_APPS_DIR / "auto_fr.py", terminal_size=(80, 25))


def test_fr_margins(snap_compare):
    # https://github.com/Textualize/textual/issues/2220
    assert snap_compare(SNAPSHOT_APPS_DIR / "fr_margins.py", terminal_size=(80, 25))


def test_scroll_visible(snap_compare):
    # https://github.com/Textualize/textual/issues/2181
    assert snap_compare(SNAPSHOT_APPS_DIR / "scroll_visible.py", press=["t"])


def test_scroll_to_center(snap_compare):
    # READ THIS IF THIS TEST FAILS:
    # While https://github.com/Textualize/textual/issues/2254 is open, the snapshot
    # this is being compared against is INCORRECT.
    # The correct output for this snapshot test would show a couple of containers
    # scrolled so that the red string >>bullseye<< is centered on the screen.
    # When this snapshot "breaks" because #2254 is fixed, this snapshot can be updated.
    assert snap_compare(SNAPSHOT_APPS_DIR / "scroll_to_center.py", press=["s"])


def test_quickly_change_tabs(snap_compare):
    # https://github.com/Textualize/textual/issues/2229
    assert snap_compare(SNAPSHOT_APPS_DIR / "quickly_change_tabs.py", press=["p"])


def test_fr_unit_with_min(snap_compare):
    # https://github.com/Textualize/textual/issues/2378
    assert snap_compare(SNAPSHOT_APPS_DIR / "fr_with_min.py")


def test_select_rebuild(snap_compare):
    # https://github.com/Textualize/textual/issues/2557
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "select_rebuild.py",
        press=["space", "escape", "tab", "enter", "tab", "space"],
    )


def test_blur_on_disabled(snap_compare):
    # https://github.com/Textualize/textual/issues/2641
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "blur_on_disabled.py",
        press=[*"foo", "f3", *"this should not appear"],
    )


def test_tooltips_in_compound_widgets(snap_compare):
    # https://github.com/Textualize/textual/issues/2641
    async def run_before(pilot) -> None:
        await pilot.pause()
        await pilot.hover("ProgressBar")
        await pilot.pause(0.4)
        await pilot.pause()

    assert snap_compare(SNAPSHOT_APPS_DIR / "tooltips.py", run_before=run_before)


def test_command_palette(snap_compare) -> None:
    async def run_before(pilot) -> None:
        # await pilot.press("ctrl+backslash")
        pilot.app.screen.query_one(Input).cursor_blink = False
        await pilot.press("A")
        await pilot.app.screen.workers.wait_for_complete()

    assert snap_compare(SNAPSHOT_APPS_DIR / "command_palette.py", run_before=run_before)


def test_command_palette_discovery(snap_compare) -> None:
    async def run_before(pilot) -> None:
        pilot.app.screen.query_one(Input).cursor_blink = False
        await pilot.app.screen.workers.wait_for_complete()

    assert snap_compare(
        SNAPSHOT_APPS_DIR / "command_palette_discovery.py", run_before=run_before
    )


# --- textual-dev library preview tests ---


def test_textual_dev_border_preview(snap_compare):
    async def run_before(pilot):
        buttons = pilot.app.query(Button)
        for button in buttons:
            button.active_effect_duration = 0

    assert snap_compare(
        SNAPSHOT_APPS_DIR / "dev_previews_border.py",
        press=["enter"],
        run_before=run_before,
    )


def test_textual_dev_colors_preview(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "dev_previews_color.py")


def test_textual_dev_easing_preview(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "dev_previews_easing.py")


def test_textual_dev_keys_preview(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "dev_previews_keys.py", press=["a", "b"])


def test_notifications_example(snap_compare) -> None:
    assert snap_compare(WIDGET_EXAMPLES_DIR / "toast.py")


def test_notifications_through_screens(snap_compare) -> None:
    assert snap_compare(SNAPSHOT_APPS_DIR / "notification_through_screens.py")


def test_notifications_through_modes(snap_compare) -> None:
    assert snap_compare(SNAPSHOT_APPS_DIR / "notification_through_modes.py")


def test_notification_with_inline_link(snap_compare) -> None:
    # https://github.com/Textualize/textual/issues/3530
    assert snap_compare(SNAPSHOT_APPS_DIR / "notification_with_inline_link.py")


def test_notification_with_inline_link_hover(snap_compare) -> None:
    # https://github.com/Textualize/textual/issues/3530
    async def run_before(pilot) -> None:
        await pilot.pause()
        await pilot.hover("Toast", offset=(8, 1))

    assert snap_compare(
        SNAPSHOT_APPS_DIR / "notification_with_inline_link.py",
        run_before=run_before,
    )


def test_print_capture(snap_compare) -> None:
    assert snap_compare(SNAPSHOT_APPS_DIR / "capture_print.py")


def test_text_log_blank_write(snap_compare) -> None:
    assert snap_compare(SNAPSHOT_APPS_DIR / "text_log_blank_write.py")


def test_nested_fr(snap_compare) -> None:
    # https://github.com/Textualize/textual/pull/3059
    assert snap_compare(SNAPSHOT_APPS_DIR / "nested_fr.py")


@pytest.mark.syntax
@pytest.mark.parametrize("language", BUILTIN_LANGUAGES)
def test_text_area_language_rendering(language, snap_compare):
    # This test will fail if we're missing a snapshot test for a valid
    # language. We should have a snapshot test for each language we support
    # as the syntax highlighting will be completely different for each of them.

    snippet = SNIPPETS.get(language)

    def setup_language(pilot) -> None:
        text_area = pilot.app.query_one(TextArea)
        text_area.load_text(snippet)
        text_area.language = language

    assert snap_compare(
        SNAPSHOT_APPS_DIR / "text_area.py",
        run_before=setup_language,
        terminal_size=(80, snippet.count("\n") + 4),
    )


@pytest.mark.parametrize(
    "selection",
    [
        Selection((0, 0), (2, 8)),
        Selection((1, 0), (0, 0)),
        Selection((5, 2), (0, 0)),
        Selection((0, 0), (4, 20)),
        Selection.cursor((1, 0)),
        Selection.cursor((2, 6)),
    ],
)
def test_text_area_selection_rendering(snap_compare, selection):
    text = """I am a line.

I am another line.

I am the final line."""

    def setup_selection(pilot):
        text_area = pilot.app.query_one(TextArea)
        text_area.load_text(text)
        text_area.show_line_numbers = False
        text_area.selection = selection

    assert snap_compare(
        SNAPSHOT_APPS_DIR / "text_area.py",
        run_before=setup_selection,
        terminal_size=(30, text.count("\n") + 4),
    )


def test_text_area_read_only_cursor_rendering(snap_compare):
    def setup_selection(pilot):
        text_area = pilot.app.query_one(TextArea)
        text_area.theme = "css"
        text_area.text = "Hello, world!"
        text_area.read_only = True

    assert snap_compare(
        SNAPSHOT_APPS_DIR / "text_area.py",
        run_before=setup_selection,
        terminal_size=(30, 5),
    )


@pytest.mark.syntax
@pytest.mark.parametrize(
    "theme_name", [theme.name for theme in TextAreaTheme.builtin_themes()]
)
def test_text_area_themes(snap_compare, theme_name):
    """Each theme should have its own snapshot with at least some Python
    to check that the rendering is sensible. This also ensures that theme
    switching results in the display changing correctly."""
    text = """\
def hello(name):
    x = 123
    while not False:
        print("hello " + name)
        continue
"""

    def setup_theme(pilot):
        text_area = pilot.app.query_one(TextArea)
        text_area.load_text(text)
        text_area.language = "python"
        text_area.selection = Selection((0, 1), (1, 9))
        text_area.theme = theme_name

    assert snap_compare(
        SNAPSHOT_APPS_DIR / "text_area.py",
        run_before=setup_theme,
        terminal_size=(48, text.count("\n") + 4),
    )


def test_text_area_alternate_screen(snap_compare):
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "text_area_alternate_screen.py", terminal_size=(48, 10)
    )


@pytest.mark.syntax
def test_text_area_wrapping_and_folding(snap_compare):
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "text_area_wrapping.py", terminal_size=(20, 26)
    )


def test_text_area_line_number_start(snap_compare):
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "text_area_line_number_start.py", terminal_size=(32, 8)
    )


def test_digits(snap_compare) -> None:
    assert snap_compare(SNAPSHOT_APPS_DIR / "digits.py")


def test_auto_grid(snap_compare) -> None:
    assert snap_compare(SNAPSHOT_APPS_DIR / "auto_grid.py")


def test_auto_grid_default_height(snap_compare) -> None:
    assert snap_compare(SNAPSHOT_APPS_DIR / "auto_grid_default_height.py", press=["g"])


def test_scoped_css(snap_compare) -> None:
    assert snap_compare(SNAPSHOT_APPS_DIR / "scoped_css.py")


def test_unscoped_css(snap_compare) -> None:
    assert snap_compare(SNAPSHOT_APPS_DIR / "unscoped_css.py")


def test_big_buttons(snap_compare) -> None:
    assert snap_compare(SNAPSHOT_APPS_DIR / "big_button.py")


def test_keyline(snap_compare) -> None:
    assert snap_compare(SNAPSHOT_APPS_DIR / "keyline.py")


def test_button_outline(snap_compare):
    """Outline style rendered incorrectly when applied to a `Button` widget.

    Regression test for https://github.com/Textualize/textual/issues/3628
    """
    assert snap_compare(SNAPSHOT_APPS_DIR / "button_outline.py")


def test_notifications_loading_overlap_order(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/3677.

    This tests that notifications stay on top of loading indicators and it also
    tests that loading a widget will remove its scrollbars.
    """
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "notifications_above_loading.py", terminal_size=(80, 20)
    )


def test_missing_vertical_scroll(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/3687"""
    assert snap_compare(SNAPSHOT_APPS_DIR / "missing_vertical_scroll.py")


def test_vertical_min_height(snap_compare):
    """Test vertical min height takes border into account."""
    assert snap_compare(SNAPSHOT_APPS_DIR / "vertical_min_height.py")


def test_vertical_max_height(snap_compare):
    """Test vertical max height takes border into account."""
    assert snap_compare(SNAPSHOT_APPS_DIR / "vertical_max_height.py")


def test_max_height_100(snap_compare):
    """Test a datatable with max height 100%."""
    assert snap_compare(SNAPSHOT_APPS_DIR / "max_height_100.py")


def test_loading_indicator(snap_compare):
    """Test loading indicator."""
    # https://github.com/Textualize/textual/pull/3816
    assert snap_compare(SNAPSHOT_APPS_DIR / "loading.py", press=["space"])


def test_loading_indicator_disables_widget(snap_compare):
    """Test loading indicator disabled widget."""
    # https://github.com/Textualize/textual/pull/3816
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "loading.py", press=["space", "down", "down", "space"]
    )


def test_mount_style_fix(snap_compare):
    """Regression test for broken style update on mount."""
    # https://github.com/Textualize/textual/issues/3858
    assert snap_compare(SNAPSHOT_APPS_DIR / "mount_style_fix.py")


def test_zero_scrollbar_size(snap_compare):
    """Regression test for missing content with 0 sized scrollbars"""
    # https://github.com/Textualize/textual/issues/3886
    assert snap_compare(SNAPSHOT_APPS_DIR / "zero_scrollbar_size.py")


def test_tree_clearing_and_expansion(snap_compare):
    """Test the Tree.root.is_expanded state after a Tree.clear"""
    # https://github.com/Textualize/textual/issues/3557
    assert snap_compare(SNAPSHOT_APPS_DIR / "tree_clearing.py")


def test_nested_specificity(snap_compare):
    """Test specificity of nested rules is working."""
    # https://github.com/Textualize/textual/issues/3961
    assert snap_compare(SNAPSHOT_APPS_DIR / "nested_specificity.py")


def test_tab_rename(snap_compare):
    """Test setting a new label for a tab amongst a TabbedContent."""
    assert snap_compare(SNAPSHOT_APPS_DIR / "tab_rename.py")


def test_input_percentage_width(snap_compare):
    """Check percentage widths work correctly."""
    # https://github.com/Textualize/textual/issues/3721
    assert snap_compare(SNAPSHOT_APPS_DIR / "input_percentage_width.py")


def test_recompose(snap_compare):
    """Check recompose works."""
    # https://github.com/Textualize/textual/pull/4206
    assert snap_compare(SNAPSHOT_APPS_DIR / "recompose.py")


@pytest.mark.parametrize("theme", ["textual-dark", "textual-light"])
def test_ansi_color_mapping(snap_compare, theme):
    """Test how ANSI colors in Rich renderables are mapped to hex colors."""

    def setup(pilot):
        pilot.app.theme = theme

    assert snap_compare(SNAPSHOT_APPS_DIR / "ansi_mapping.py", run_before=setup)


def test_pretty_grid_gutter_interaction(snap_compare):
    """Regression test for https://github.com/Textualize/textual/pull/4219."""
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "pretty_grid_gutter_interaction.py", terminal_size=(81, 7)
    )


def test_sort_children(snap_compare):
    """Test sort_children method."""
    assert snap_compare(SNAPSHOT_APPS_DIR / "sort_children.py", terminal_size=(80, 25))


def test_app_blur(snap_compare):
    """Test Styling after receiving an AppBlur message."""

    async def run_before(pilot) -> None:
        await pilot.pause()  # Allow the AppBlur message to get processed.

    assert snap_compare(SNAPSHOT_APPS_DIR / "app_blur.py", run_before=run_before)


def test_placeholder_disabled(snap_compare):
    """Test placeholder with diabled set to True."""
    assert snap_compare(SNAPSHOT_APPS_DIR / "placeholder_disabled.py")


def test_listview_index(snap_compare):
    """Tests that ListView scrolls correctly after updating its index."""
    assert snap_compare(SNAPSHOT_APPS_DIR / "listview_index.py")


def test_button_widths(snap_compare):
    """Test that button widths expand auto containers as expected."""
    # https://github.com/Textualize/textual/issues/4024
    assert snap_compare(SNAPSHOT_APPS_DIR / "button_widths.py")


def test_welcome(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "welcome_widget.py")


# --- Example apps ---
# We skip the code browser because the length of the scrollbar in the tree depends on
# the number of files and folders we have locally and that typically differs from the
# pristine setting in which CI runs.


def test_example_calculator(snap_compare):
    """Test the calculator example."""
    assert snap_compare(EXAMPLES_DIR / "calculator.py")


def test_example_color_command(snap_compare):
    """Test the color_command example."""
    assert snap_compare(
        EXAMPLES_DIR / "color_command.py",
        press=[App.COMMAND_PALETTE_BINDING, "r", "e", "d", "enter"],
    )


def test_example_dictionary(snap_compare):
    """Test the dictionary example (basic layout test)."""

    async def run_before(pilot):
        pilot.app.query(Input).first().cursor_blink = False

    assert snap_compare(EXAMPLES_DIR / "dictionary.py", run_before=run_before)


def test_example_five_by_five(snap_compare):
    """Test the five_by_five example."""
    assert snap_compare(EXAMPLES_DIR / "five_by_five.py")


def test_example_json_tree(snap_compare):
    """Test the json_tree example."""
    assert snap_compare(
        EXAMPLES_DIR / "json_tree.py",
        press=["a", "down", "enter", "down", "down", "enter"],
    )


def test_example_markdown(snap_compare):
    """Test the markdown example."""
    assert snap_compare(EXAMPLES_DIR / "markdown.py")


def test_example_merlin(snap_compare):
    """Test the merlin example."""
    on_switches = {2, 3, 5, 8}

    async def run_before(pilot):
        pilot.app.query_one("Timer").running = False  # This will freeze the clock.
        for switch in pilot.app.query("LabelSwitch"):
            switch.query_one("Switch").value = switch.switch_no in on_switches
        await pilot.pause()

    assert snap_compare(EXAMPLES_DIR / "merlin.py", run_before=run_before)


def test_example_pride(snap_compare):
    """Test the pride example."""
    assert snap_compare(EXAMPLES_DIR / "pride.py")


def test_button_with_console_markup(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/4328"""
    assert snap_compare(SNAPSHOT_APPS_DIR / "button_markup.py")


def test_width_100(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/4360"""
    assert snap_compare(SNAPSHOT_APPS_DIR / "width_100.py")


def test_button_with_multiline_label(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "button_multiline_label.py")


def test_margin_multiple(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "margin_multiple.py")


def test_dynamic_bindings(snap_compare):
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "dynamic_bindings.py", press=["a", "b", "c"]
    )


def test_grid_gutter(snap_compare):
    # https://github.com/Textualize/textual/issues/4522
    assert snap_compare(SNAPSHOT_APPS_DIR / "grid_gutter.py")


def test_multi_keys(snap_compare):
    # https://github.com/Textualize/textual/issues/4542
    assert snap_compare(SNAPSHOT_APPS_DIR / "multi_keys.py")


def test_data_table_in_tabs(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "data_table_tabs.py")


def test_auto_tab_active(snap_compare):
    # https://github.com/Textualize/textual/issues/4593
    assert snap_compare(SNAPSHOT_APPS_DIR / "auto_tab_active.py", press=["space"])


def test_hatch(snap_compare):
    """Test hatch styles."""
    assert snap_compare(SNAPSHOT_APPS_DIR / "hatch.py")


def test_rules(snap_compare):
    """Test rules."""
    assert snap_compare(SNAPSHOT_APPS_DIR / "rules.py")


def test_grid_auto(snap_compare):
    """Test grid with keyline and auto-dimension."""
    # https://github.com/Textualize/textual/issues/4678
    assert snap_compare(SNAPSHOT_APPS_DIR / "grid_auto.py")


def test_footer_compact(snap_compare):
    """Test Footer in the compact style"""
    assert snap_compare(SNAPSHOT_APPS_DIR / "footer_toggle_compact.py")


def test_footer_compact_with_hover(snap_compare):
    """Test Footer in the compact style when the mouse is hovering over a keybinding"""

    async def run_before(pilot) -> None:
        await pilot.hover("Footer", offset=(0, 0))

    assert snap_compare(
        SNAPSHOT_APPS_DIR / "footer_toggle_compact.py", run_before=run_before
    )


def test_footer_standard_after_reactive_change(snap_compare):
    """Test Footer in the standard style after `compact` reactive change"""
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "footer_toggle_compact.py", press=["ctrl+t"]
    )


def test_footer_standard_with_hover(snap_compare):
    """Test Footer in the standard style when the mouse is hovering over a keybinding"""

    async def run_before(pilot) -> None:
        await pilot.press("ctrl+t")
        await pilot.hover("Footer", offset=(0, 0))

    assert snap_compare(
        SNAPSHOT_APPS_DIR / "footer_toggle_compact.py", run_before=run_before
    )


def test_footer_classic_styling(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/4557"""
    assert snap_compare(SNAPSHOT_APPS_DIR / "footer_classic_styling.py")


def test_option_list_scrolling_with_multiline_options(snap_compare):
    # https://github.com/Textualize/textual/issues/4705
    assert snap_compare(WIDGET_EXAMPLES_DIR / "option_list_tables.py", press=["up"])


def test_bindings_screen_overrides_show(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/4382"""
    assert snap_compare(SNAPSHOT_APPS_DIR / "bindings_screen_overrides_show.py")


def test_scroll_visible_with_margin(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/2181"""
    assert snap_compare(SNAPSHOT_APPS_DIR / "scroll_visible_margin.py", press=["x"])


def test_programmatic_disable_button(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/3130"""

    async def run_before(pilot: Pilot) -> None:
        await pilot.hover("#disable-btn")
        await pilot.press("space")

    assert snap_compare(
        SNAPSHOT_APPS_DIR / "programmatic_disable_button.py", run_before=run_before
    )


def test_toggle_style_order(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/3421"""
    assert snap_compare(SNAPSHOT_APPS_DIR / "toggle_style_order.py")


def test_component_text_opacity(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/3413"""
    assert snap_compare(SNAPSHOT_APPS_DIR / "component_text_opacity.py")


def test_progress_gradient(snap_compare):
    """Test gradient parameter on ProgressBar"""
    assert snap_compare(SNAPSHOT_APPS_DIR / "progress_gradient.py")


def test_recompose_in_mount(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/4799"""
    assert snap_compare(SNAPSHOT_APPS_DIR / "recompose_on_mount.py")


def test_enter_or_leave(snap_compare) -> None:
    async def run_before(pilot: Pilot):
        await pilot.hover("#foo")

    assert snap_compare(SNAPSHOT_APPS_DIR / "enter_or_leave.py", run_before=run_before)


def test_remove_tab_no_animation(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/4814"""
    assert snap_compare(SNAPSHOT_APPS_DIR / "remove_tab.py", press=["space"])


def test_auto_height_scrollbar(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/4778"""
    assert snap_compare(SNAPSHOT_APPS_DIR / "data_table_auto_height.py")


def test_bind_override(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/4755"""
    assert snap_compare(SNAPSHOT_APPS_DIR / "bind_override.py")


def test_command_palette_dismiss_escape(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/4856"""

    async def run_before(pilot: Pilot):
        await pilot.press(App.COMMAND_PALETTE_BINDING)
        await pilot.pause()
        await pilot.press("escape")

    assert snap_compare(
        SNAPSHOT_APPS_DIR / "command_palette_dismiss.py", run_before=run_before
    )


def test_command_palette_dismiss_escape_no_results(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/4856"""

    async def run_before(pilot: Pilot):
        await pilot.press(App.COMMAND_PALETTE_BINDING)
        await pilot.pause()
        await pilot.press(*"foo")
        await pilot.app.workers.wait_for_complete()
        await pilot.press("escape")

    assert snap_compare(
        SNAPSHOT_APPS_DIR / "command_palette_dismiss.py", run_before=run_before
    )


def test_command_palette_key_change(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/4887"""
    assert snap_compare(SNAPSHOT_APPS_DIR / "command_palette_key.py")


def test_split(snap_compare):
    """Test split rule."""
    assert snap_compare(SNAPSHOT_APPS_DIR / "split.py", terminal_size=(100, 30))


def test_system_commands(snap_compare):
    """The system commands should appear in the command palette."""

    class SimpleApp(App):
        def compose(self) -> ComposeResult:
            input = Input()
            input.cursor_blink = False
            yield input

    app = SimpleApp()
    app.animation_level = "none"
    assert snap_compare(
        app,
        terminal_size=(100, 30),
        press=["ctrl+p"],
    )


def test_help_panel(snap_compare):
    """Test help panel."""

    class HelpPanelApp(App):
        def compose(self) -> ComposeResult:
            yield Input()

    async def run_before(pilot: Pilot):
        pilot.app.query(Input).first().cursor_blink = False
        await pilot.press(App.COMMAND_PALETTE_BINDING)
        await pilot.pause()
        await pilot.press(*"keys")
        await pilot.press("enter")
        await pilot.app.workers.wait_for_complete()

    assert snap_compare(HelpPanelApp(), terminal_size=(100, 30), run_before=run_before)


def test_scroll_page_down(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/4914"""
    # Should show 25 at the top
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "scroll_page.py", press=["pagedown"], terminal_size=(80, 25)
    )


def test_maximize(snap_compare):
    """Check that maximize isolates a single widget."""

    class MaximizeApp(App):
        BINDINGS = [("m", "screen.maximize", "maximize focused widget")]

        def compose(self) -> ComposeResult:
            yield Button("Hello")
            yield Button("World")
            yield Footer()

    assert snap_compare(MaximizeApp(), press=["m"])


def test_maximize_container(snap_compare):
    """Check maximizing a widget in a maximizeable container, maximizes the container."""

    class FormContainer(Vertical):
        ALLOW_MAXIMIZE = True
        DEFAULT_CSS = """
        FormContainer {
            width: 50%;
            border: blue;            
        }
        """

    class MaximizeApp(App):
        BINDINGS = [("m", "screen.maximize", "maximize focused widget")]

        def compose(self) -> ComposeResult:
            with FormContainer():
                yield Button("Hello")
                yield Button("World")
            yield Footer()

    assert snap_compare(MaximizeApp(), press=["m"])


def test_check_consume_keys(snap_compare):
    """Check that when an Input is focused it hides printable keys from the footer."""

    class MyApp(App):
        BINDINGS = [
            Binding(key="q", action="quit", description="Quit the app"),
            Binding(
                key="question_mark",
                action="help",
                description="Show help screen",
                key_display="?",
            ),
            Binding(key="delete", action="delete", description="Delete the thing"),
            Binding(key="j", action="down", description="Scroll down", show=False),
        ]

        def compose(self) -> ComposeResult:
            yield Input(placeholder="First Name")
            yield Input(placeholder="Last Name")
            yield Switch()
            yield Footer()

    assert snap_compare(MyApp())


def test_escape_to_minimize(snap_compare):
    """Check escape minimizes. Regression test for https://github.com/Textualize/textual/issues/4939"""

    TEXT = """\
    def hello(name):
        print("hello" + name)

    def goodbye(name):
        print("goodbye" + name)
    """

    class TextAreaExample(App):
        BINDINGS = [("ctrl+m", "screen.maximize")]
        CSS = """
        Screen {
            align: center middle;
        }

        #code-container {
            width: 20;
            height: 10;
        }
        """

        def compose(self) -> ComposeResult:
            with Vertical(id="code-container"):
                text_area = TextArea.code_editor(TEXT)
                text_area.cursor_blink = False
                yield text_area

    # ctrl+m to maximize, escape should minimize
    assert snap_compare(TextAreaExample(), press=["ctrl+m", "escape"])


def test_escape_to_minimize_disabled(snap_compare):
    """Set escape to minimize disabled by app"""

    TEXT = """\
    def hello(name):
        print("hello" + name)

    def goodbye(name):
        print("goodbye" + name)
    """

    class TextAreaExample(App):
        # Disables escape to minimize
        ESCAPE_TO_MINIMIZE = False
        BINDINGS = [("ctrl+m", "screen.maximize")]
        CSS = """
        Screen {
            align: center middle;
        }

        #code-container {
            width: 20;
            height: 10;
        }
        """

        def compose(self) -> ComposeResult:
            with Vertical(id="code-container"):
                text_area = TextArea.code_editor(TEXT)
                text_area.cursor_blink = False
                yield text_area

    # ctrl+m to maximize, escape should *not* minimize
    assert snap_compare(TextAreaExample(), press=["ctrl+m", "escape"])


def test_escape_to_minimize_screen_override(snap_compare):
    """Test escape to minimize can be overridden by the screen"""

    TEXT = """\
    def hello(name):
        print("hello" + name)

    def goodbye(name):
        print("goodbye" + name)
    """

    class TestScreen(Screen):
        # Disabled on the screen
        ESCAPE_TO_MINIMIZE = True

        def compose(self) -> ComposeResult:
            with Vertical(id="code-container"):
                text_area = TextArea.code_editor(TEXT)
                text_area.cursor_blink = False
                yield text_area

    class TextAreaExample(App):
        # Enabled on app
        ESCAPE_TO_MINIMIZE = False
        BINDINGS = [("ctrl+m", "screen.maximize")]
        CSS = """
        Screen {
            align: center middle;
        }

        #code-container {
            width: 20;
            height: 10;
        }
        """

        def compose(self) -> ComposeResult:
            yield Label("You are looking at the default screen")

        def on_mount(self) -> None:
            self.push_screen(TestScreen())

    # ctrl+m to maximize, escape *should* minimize
    assert snap_compare(TextAreaExample(), press=["ctrl+m", "escape"])


def test_app_focus_style(snap_compare):
    """Test that app blur style can be selected."""

    class FocusApp(App):
        CSS = """
        Label {
            padding: 1 2;
            margin: 1 2;
            background: $panel;
            border: $primary;
        }
        App:focus {
            .blurred {
                visibility: hidden;
            }
        }

        App:blur {
            .focussed {
                visibility: hidden;
            }
        }

        """

        def compose(self) -> ComposeResult:
            yield Label("BLURRED", classes="blurred")
            yield Label("FOCUSED", classes="focussed")

    async def run_before(pilot: Pilot) -> None:
        pilot.app.post_message(events.AppBlur())
        await pilot.pause()

    assert snap_compare(FocusApp(), run_before=run_before)


def test_ansi(snap_compare):
    """Test ANSI colors."""
    # It is actually impossible to tell from the SVG that ANSI colors were actually used
    # This snapshot test exists as a canary to check if ansi_colors have broken

    class ANSIApp(App):
        CSS = """
        Label {
            background: ansi_blue;
            border: solid ansi_white;
        }
        """

        def compose(self) -> ComposeResult:
            yield Label("[ansi_red]Red[/] [ansi_magenta]Magenta[/]")

    app = ANSIApp(ansi_color=True)
    assert snap_compare(app)


def test_ansi_command_palette(snap_compare):
    """Test command palette on top of ANSI colors."""

    class CommandPaletteApp(App[None]):
        SUSPENDED_SCREEN_CLASS = "-screen-suspended"
        CSS = """
        Label {
            width: 1fr;
        }
        """

        def compose(self) -> ComposeResult:
            yield Label("[ansi_red]Red[/] [ansi_magenta]Magenta[/] " * 200)

        def on_mount(self) -> None:
            self.action_command_palette()

    app = CommandPaletteApp(ansi_color=True)
    assert snap_compare(app)


def test_disabled(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/5028"""

    class DisabledApp(App[None]):
        CSS = """
        Log {
            height: 4;
        }
        RichLog {
            height: 4;
        }
        DataTable {
            height: 4;
        }
        OptionList {
            height: 4;
        }
        SelectionList {
            height: 4;
        }
        """

        def compose(self) -> ComposeResult:
            yield Label("Labels don't have a disabled state", disabled=True)
            yield Log(disabled=True)
            yield RichLog(disabled=True)
            yield DataTable(disabled=True)
            yield OptionList("you", "can't", "select", "me", disabled=True)
            yield SelectionList(("Simple SelectionList", "", False), disabled=True)

        def on_mount(self) -> None:
            self.query_one(Log).write("I am disabled")
            self.query_one(RichLog).write("I am disabled")
            self.query_one(DataTable).add_columns("Foo", "Bar")
            self.query_one(DataTable).add_row("Also", "disabled")

    app = DisabledApp()
    assert snap_compare(app)


def test_keymap_bindings_display_footer_and_help_panel(snap_compare):
    """Bindings overridden by the Keymap are shown as expected in the Footer
    and help panel. Testing that the keys work as expected is done elsewhere.

    Footer should show bindings `k` to Increment, and `down` to Decrement.

    Key panel should show bindings `k, plus` to increment,
    and `down, minus, j` to decrement.

    """

    class Counter(App[None]):
        BINDINGS = [
            Binding(
                key="i,up",
                action="increment",
                description="Increment",
                id="app.increment",
            ),
            Binding(
                key="d,down",
                action="decrement",
                description="Decrement",
                id="app.decrement",
            ),
        ]

        def compose(self) -> ComposeResult:
            yield Label("Counter")
            yield Footer()

        def on_mount(self) -> None:
            self.action_show_help_panel()
            self.set_keymap(
                {
                    "app.increment": "k,plus",
                    "app.decrement": "down,minus,j",
                }
            )

    assert snap_compare(Counter())


def test_keymap_bindings_key_display(snap_compare):
    """If a default binding in `BINDINGS` has a key_display, it should be reset
    when that binding is overridden by a Keymap.

    The key_display should be taken from `App.get_key_display`, so in this case
    it should be "THIS IS CORRECT" in the Footer and help panel, not "INCORRECT".
    """

    class MyApp(App[None]):
        BINDINGS = [
            Binding(
                key="i,up",
                action="increment",
                description="Increment",
                id="app.increment",
                key_display="INCORRECT",
            ),
        ]

        def compose(self) -> ComposeResult:
            yield Label("Check the footer and help panel")
            yield Footer()

        def on_mount(self) -> None:
            self.action_show_help_panel()
            self.set_keymap({"app.increment": "k,plus,j,l"})

        def get_key_display(self, binding: Binding) -> str:
            if binding.id == "app.increment":
                return "correct"
            return super().get_key_display(binding)

    assert snap_compare(MyApp())


def test_missing_new_widgets(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/5024"""

    class MRE(App):
        BINDINGS = [("z", "toggle_console", "Console")]
        CSS = """
        RichLog { border-top: dashed blue; height: 6; }
        .hidden { display: none; }
        """

        def compose(self):
            yield VerticalScroll()
            yield ProgressBar(
                classes="hidden"
            )  # removing or displaying this widget prevents the bug
            yield Footer()  # clicking "Console" in the footer prevents the bug
            yield RichLog(classes="hidden")

        def on_ready(self) -> None:
            self.query_one(RichLog).write("\n".join(f"line #{i}" for i in range(5)))

        def action_toggle_console(self) -> None:
            self.query_one(RichLog).toggle_class("hidden")

    app = MRE()
    assert snap_compare(app, press=["space", "space", "z"])


def test_pop_until_active(snap_compare):
    """End result should be screen showing 'BASE'"""

    class BaseScreen(Screen):
        def compose(self) -> ComposeResult:
            yield Label("BASE")

    class FooScreen(Screen):
        def compose(self) -> ComposeResult:
            yield Label("Foo")

    class BarScreen(Screen):
        BINDINGS = [("b", "app.make_base_active")]

        def compose(self) -> ComposeResult:
            yield Label("Bar")

    class PopApp(App):
        SCREENS = {"base": BaseScreen}

        async def on_mount(self) -> None:
            # Push base
            await self.push_screen("base")
            # Push two screens
            await self.push_screen(FooScreen())
            await self.push_screen(BarScreen())

        def action_make_base_active(self) -> None:
            self.get_screen("base").pop_until_active()

    app = PopApp()
    # App will push three screens
    # Pressing "b" will call pop_until_active, and pop two screens
    # End result should be screen showing "BASE"
    assert snap_compare(app, press=["b"])


def test_updates_with_auto_refresh(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/5056

    After hiding and unhiding the RichLog, you should be able to see 1.5 fully rendered placeholder widgets.
    Prior to this fix, the bottom portion of the screen did not
    refresh after the RichLog was hidden/unhidden while in the presence of the auto-refreshing ProgressBar widget.
    """

    class MRE(App):
        BINDINGS = [
            ("z", "toggle_widget('RichLog')", "Console"),
        ]
        CSS = """
        Placeholder { height: 15; }
        RichLog { height: 6; }
        .hidden { display: none; }
        """

        def compose(self):
            with VerticalScroll():
                for i in range(10):
                    yield Placeholder()
            yield ProgressBar(classes="hidden")
            yield RichLog(classes="hidden")

        def on_ready(self) -> None:
            self.query_one(RichLog).write("\n".join(f"line #{i}" for i in range(5)))

        def action_toggle_widget(self, widget_type: str) -> None:
            self.query_one(widget_type).toggle_class("hidden")

    app = MRE()
    assert snap_compare(app, press=["z", "z"])


def test_push_screen_on_mount(snap_compare):
    """Test pushing (modal) screen immediately on mount, which was not refreshing the base screen.

    Should show a panel partially obscuring Hello World text

    """

    class QuitScreen(ModalScreen[None]):
        """Screen with a dialog to quit."""

        DEFAULT_CSS = """
        QuitScreen {
            align: center middle;
        }

        #dialog {
            grid-size: 2;
            grid-gutter: 1 2;
            grid-rows: 1fr 3;
            padding: 0 1;
            width: 60;
            height: 11;
            border: thick $primary 80%;
            background: $surface;
        }

        #question {
            column-span: 2;
            height: 1fr;
            width: 1fr;
            content-align: center middle;
        }

        Button {
            width: 100%;
        }
        """

        def compose(self) -> ComposeResult:
            yield Grid(
                Label("Are you sure you want to quit?", id="question"), id="dialog"
            )

    class MyApp(App[None]):
        def compose(self) -> ComposeResult:
            s = "Hello World Foo Bar Baz"
            yield Middle(Center(Static(s)))

        def on_mount(self) -> None:
            self.push_screen(QuitScreen())

    app = MyApp()

    assert snap_compare(app)


def test_transparent_background(snap_compare):
    """Check that a transparent background defers to render().

    This should display a colorful gradient, filling the screen.
    """

    COLORS = [
        "#881177",
        "#aa3355",
        "#cc6666",
        "#ee9944",
        "#eedd00",
        "#99dd55",
        "#44dd88",
        "#22ccbb",
        "#00bbcc",
        "#0099cc",
        "#3366bb",
        "#663399",
    ]

    class TransparentApp(App):
        CSS = """
        Screen {
            background: transparent;
        }
        """

        def render(self) -> LinearGradient:
            """Renders a gradient, when the background is transparent."""
            stops = [(i / (len(COLORS) - 1), c) for i, c in enumerate(COLORS)]
            return LinearGradient(30.0, stops)

    app = TransparentApp()
    assert snap_compare(app)


def test_maximize_allow(snap_compare):
    """Check that App.ALLOW_IN_MAXIMIZED_VIEW is the default.

    If working this should show a header, some text, a focused button, and more text.

    """

    class MaximizeApp(App):
        ALLOW_IN_MAXIMIZED_VIEW = "Header"
        BINDINGS = [("m", "screen.maximize", "maximize focused widget")]

        def compose(self) -> ComposeResult:
            yield Label(
                "Above", classes="-textual-system"
            )  # Allowed in maximize view because it has class -textual-system
            yield Header()  # Allowed because it matches ALLOW_IN_MAXIMIZED_VIEW
            yield Button("Hello")  # Allowed because it is the maximized widget
            yield Label(
                "Below", classes="-textual-system"
            )  # Allowed because it has class -textual-system
            yield Button("World")  # Not allowed
            yield Footer()  # Not allowed

    assert snap_compare(MaximizeApp(), press=["m"])


def test_background_tint(snap_compare):
    """Test background tint with alpha."""

    # The screen background is dark blue
    # The vertical is 20% white
    # With no background tint, the verticals will be a light blue
    # With a 100% tint, the vertical should be 20% red plus the blue (i.e. purple)

    # tl;dr you should see 4 bars, blue at the top, purple at the bottom, and two shades in between

    class BackgroundTintApp(App):
        CSS = """
        Screen {
            background: rgb(0,0,100)
        }
        Vertical {
            background: rgba(255,255,255,0.2);
        }
        #tint1 { background-tint: rgb(255,0,0) 0%; }
        #tint2 { background-tint: rgb(255,0,0) 33%; }
        #tint3 { background-tint: rgb(255,0,0) 66%; }
        #tint4 { background-tint: rgb(255,0,0) 100% }
        """

        def compose(self) -> ComposeResult:
            with Vertical(id="tint1"):
                yield Label("0%")
            with Vertical(id="tint2"):
                yield Label("33%")
            with Vertical(id="tint3"):
                yield Label("66%")
            with Vertical(id="tint4"):
                yield Label("100%")

    assert snap_compare(BackgroundTintApp())


def test_fr_and_margin(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/5116"""

    # Check margins can be independently applied to widgets with fr unites

    class FRApp(App):
        CSS = """
        #first-container {
            background: green;
            height: auto;
        }

        #second-container {
            margin: 2;
            background: red;
            height: auto;
        }

        #third-container {
            margin: 4;
            background: blue;
            height: auto;
        }
        """

        def compose(self) -> ComposeResult:
            with Container(id="first-container"):
                yield Label("No margin - should extend to left and right")

            with Container(id="second-container"):
                yield Label("A margin of 2, should be 2 cells around the text")

            with Container(id="third-container"):
                yield Label("A margin of 4, should be 4 cells around the text")

    assert snap_compare(FRApp())


def test_pseudo_classes(snap_compare):
    """Test pseudo classes added in https://github.com/Textualize/textual/pull/5139

    You should see 6 bars, with alternating green and red backgrounds.

    The first bar should have a red border.

    The last bar should have a green border.

    """

    class PSApp(App):
        CSS = """
        Label { width: 1fr; height: 1fr; }
        Label:first-of-type { border:heavy red; }
        Label:last-of-type { border:heavy green; }
        Label:odd {background: $success 20%; }
        Label:even {background: $error 20%; }
        """

        def compose(self) -> ComposeResult:
            for item_number in range(5):
                yield Label(f"Item {item_number+1}")

        def on_mount(self) -> None:
            # Mounting a new widget should updated previous widgets, as the last of type has changed
            self.mount(Label("HELLO"))

    assert snap_compare(PSApp())


def test_split_segments_infinite_loop(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/5151

    Should be a bare-bones text editor containing "x"

    """
    assert snap_compare(SNAPSHOT_APPS_DIR / "split_segments.py")


@pytest.mark.parametrize("theme_name", ["nord", "gruvbox"])
def test_themes(snap_compare, theme_name):
    """Test setting different themes and custom theme variables.

    The colors from the theme should be clear, and the text-style of the label
    should be bold italic, since that's set in the custom theme variable.
    """

    class ThemeApp(App[None]):
        CSS = """
        Screen {
            align: center middle;
        }
        
        Label {
            background: $panel;
            color: $text;
            padding: 1 2;
            border: wide $primary;
            text-style: $theme-label-style;
        }
        """

        def get_theme_variable_defaults(self) -> dict[str, str]:
            """Define a custom theme variable."""
            return {"theme-label-style": "bold italic", "unused": "red"}

        def compose(self) -> ComposeResult:
            yield Label(f"{theme_name.title()} Theme")

        def on_mount(self) -> None:
            self.theme = theme_name

    assert snap_compare(ThemeApp())


def test_custom_theme_with_variables(snap_compare):
    """Test creating and using a custom theme with variables that get overridden.

    After the overrides from the theme, the background should be blue, the text should be white, the border should be yellow,
    the style should be bold italic, and the label should be cyan.
    """

    class ThemeApp(App[None]):
        CSS = """
        Screen {
            align: center middle;
        }
        
        Label {
            background: $custom-background;
            color: $custom-text;
            border: wide $custom-border;
            padding: 1 2;
            text-style: $custom-style;
            text-align: center;
            width: auto;
        }
        """

        def compose(self) -> ComposeResult:
            yield Label("Custom Theme")

        def get_theme_variable_defaults(self) -> dict[str, str]:
            """Override theme variables."""
            return {
                "custom-text": "cyan",
                "custom-style": "bold italic",
                "custom-border": "red",
                "custom-background": "#0000ff 50%",
            }

        def on_mount(self) -> None:
            custom_theme = Theme(
                name="my-custom",
                primary="magenta",
                background="black",
                variables={
                    "custom-background": "#ff0000 20%",
                    "custom-text": "white",
                    "custom-border": "yellow",
                    "custom-style": "bold",
                },
            )
            self.register_theme(custom_theme)
            self.theme = "my-custom"

    assert snap_compare(ThemeApp())


def test_app_search_commands_opens_and_displays_search_list(snap_compare):
    """Test the App.search_commands method for displaying a list of commands."""

    class SearchApp(App[None]):
        def compose(self) -> ComposeResult:
            yield Label("Search Commands")

        async def on_mount(self) -> None:
            def callback():
                """Dummy no-op callback."""

            commands = [("foo", callback), ("bar", callback), ("baz", callback)]
            await self.search_commands(commands)

    async def run_before(pilot: Pilot) -> None:
        await pilot.press("b")

    assert snap_compare(SearchApp(), run_before=run_before)


def test_help_panel_key_display_not_duplicated(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/5037"""

    class HelpPanelApp(App):
        BINDINGS = [
            Binding("b,e,l", "bell", "Ring the bell", key_display="foo"),
        ]

        def compose(self) -> ComposeResult:
            yield Footer()

    async def run_before(pilot: Pilot):
        pilot.app.action_show_help_panel()

    app = HelpPanelApp()
    assert snap_compare(app, run_before=run_before)


def test_tabs_remove_tab_updates_highlighting(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/5218"""

    class TabsApp(App):
        BINDINGS = [("r", "remove_foo", "Remove foo")]

        def compose(self) -> ComposeResult:
            yield Tabs(
                Tab("foo", id="foo"),
                Tab("bar", id="bar"),
                active="bar",
            )
            yield Footer()

        def action_remove_foo(self) -> None:
            tabs = self.query_one(Tabs)
            tabs.remove_tab("foo")

    app = TabsApp()
    assert snap_compare(app, press="r")


def test_theme_variables_available_in_code(snap_compare):
    """Test that theme variables are available in code."""

    class ThemeVariablesApp(App):
        def compose(self) -> ComposeResult:
            yield Label("Hello")

        def on_mount(self) -> None:
            variables = self.theme_variables
            label = self.query_one(Label)
            label.update(f"$text-primary = {variables['text-primary']}")
            label.styles.background = variables["primary-muted"]
            label.styles.color = variables["text-primary"]

    assert snap_compare(ThemeVariablesApp())


def test_dock_offset(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/5261
    You should see 10 labels, 0 thru 9, in a diagonal line starting at the top left.
    """

    class OffsetBugApp(App):
        CSS = """
        .label {
            dock: top;
            color: $text-success;
            background: $success-muted;
        }
        """

        def compose(self) -> ComposeResult:
            # I'd expect this to draw a diagonal line of labels, but it places them all at the top left.
            for i in range(10):
                label = Label(str(i), classes="label")
                label.styles.offset = (i, i)
                yield label

    assert snap_compare(OffsetBugApp())


def test_select_overlay_constrain(snap_compare):
    """Check that the constrain logic on Select is working.
    You should see the select overlay in full, anchored to the bottom of the screen."""

    class OApp(App):
        CSS = """
        Label {
            height: 16;
            background: blue;
            border: tall white;
        }
        """

        def compose(self) -> ComposeResult:
            yield Label("Padding (ignore)")
            yield Select.from_values(["Foo", "bar", "baz"] * 10)

    async def run_before(pilot: Pilot) -> None:
        await pilot.pause()
        await pilot.click(Select)

    assert snap_compare(OApp(), run_before=run_before)


def test_position_absolute(snap_compare):
    """Check position: absolute works as expected.
    You should see three staggered labels at the top-left, and three staggered relative labels in the center.
    The relative labels will have an additional line between them.
    """

    class AbsoluteApp(App):
        CSS = """
        Screen {        
            align: center middle;

            .absolute {
                position: absolute;
            }

            .relative {
                position: relative;
            }

            .offset1 {
                offset: 1 1;
            }
            .offset2 {
                offset: 2 2;                
            }
            .offset3 {
                offset: 3 3;
            }
        }

        """

        def compose(self) -> ComposeResult:
            yield Label("Absolute 1", classes="absolute offset1")
            yield Label("Absolute 2", classes="absolute offset2")
            yield Label("Absolute 3", classes="absolute offset3")

            yield Label("Relative 1", classes="relative offset1")
            yield Label("Relative 2", classes="relative offset2")
            yield Label("Relative 3", classes="relative offset3")

    assert snap_compare(AbsoluteApp())


def test_grid_offset(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/5279
    You should see 6 boxes arranged in a 3x2 grid. The 6th should be offset 10 lines down.
    """

    class GridOffsetApp(App):
        CSS = """
        Screen {
            layout: grid;
            grid-size: 3 2;
        }

        .box {
            height: 100%;
            border: solid green;
        }

        #six {   
            offset: 0 10;
            background: blue;
        }
        """

        def compose(self) -> ComposeResult:
            yield Static("One", classes="box")
            yield Static("Two", classes="box")
            yield Static("Three", classes="box")
            yield Static("Four", classes="box")
            yield Static("Five", classes="box")
            yield Static("Six", classes="box", id="six")

    assert snap_compare(GridOffsetApp())


# Figure out why this test is flakey
@pytest.mark.skip("This test is flakey (why)?")
def test_select_width_auto(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/5280"
    The overlay has a width of auto, so the first (widest) option should not wrap."""

    class TallSelectApp(App[None]):
        CSS = """
            Screen {
                align: center middle;

                & > Select {
                    width: 50;

                    & > SelectOverlay {
                        max-height: 100vh;
                        width: auto;
                    }
                }
            }
        """

        def compose(self) -> ComposeResult:
            yield Select(
                [("Extra long option here", 100)]
                + [(f"Option {idx + 1}", idx) for idx in range(100)],
                value=100,
            )

    async def run_before(pilot: Pilot) -> None:
        await pilot.pause()
        await pilot.click("Select")

    assert snap_compare(TallSelectApp(), run_before=run_before)


def test_markup_command_list(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/5276
    You should see a command list, with console markup applied to the action name and help text.
    """

    class MyApp(App):
        def on_mount(self) -> None:
            self.search_commands(
                [
                    SimpleCommand(
                        "Hello [u ansi_green]World",
                        lambda: None,
                        "Help [u ansi_red]text",
                    )
                ]
            )

    assert snap_compare(MyApp())


# TODO: Why is this flakey?
@pytest.mark.skip("Flakey on Windows")
def test_app_resize_order(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/5284
    You should see a placeholder with text "BAR", focused and scrolled down so it fills the screen.
    """

    class FocusPlaceholder(Placeholder, can_focus=True):
        pass

    class NarrowScreen(Screen):
        AUTO_FOCUS = "#bar"

        def compose(self) -> ComposeResult:
            yield FocusPlaceholder("FOO", id="foo")
            yield FocusPlaceholder("BAR", id="bar")

    class SCApp(App):
        CSS = """
        Placeholder:focus {
            border: heavy white;
        }
        #foo {
            height: 24;
        }
        #bar {
            height: 1fr;
        }

        .narrow #bar {
            height: 100%;
        }

        """

        def on_mount(self) -> None:
            self.push_screen(NarrowScreen())

        def on_resize(self) -> None:
            self.add_class("narrow")

    async def run_before(pilot: Pilot):
        await pilot.pause()
        await pilot.wait_for_animation()
        await pilot.pause()

    assert snap_compare(SCApp(), run_before=run_before)


def test_add_remove_tabs(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/5215
    You should see a TabbedContent with three panes, entitled 'tab-2', 'New tab' and 'New tab'
    """

    class ExampleApp(App):
        BINDINGS = [
            ("r", "remove_pane", "Remove first pane"),
            ("a", "add_pane", "Add pane"),
        ]

        def compose(self) -> ComposeResult:
            with TabbedContent(initial="tab-2"):
                with TabPane("tab-1"):
                    yield Label("tab-1")
                with TabPane("tab-2"):
                    yield Label("tab-2")
            yield Footer()

        def action_remove_pane(self) -> None:
            tabbed_content = self.query_one(TabbedContent)
            tabbed_content.remove_pane("tab-1")

        def action_add_pane(self) -> None:
            tabbed_content = self.query_one(TabbedContent)
            new_pane = TabPane("New tab", Label("new"))
            tabbed_content.add_pane(new_pane)

    assert snap_compare(ExampleApp(), press=["a", "r", "a"])


def test_click_expand(snap_compare):
    """Should show an expanded select with 15 highlighted."""

    class SelectApp(App):
        def compose(self) -> ComposeResult:
            yield Select.from_values(
                range(20),
                value=15,
            )

    async def run_before(pilot: Pilot) -> None:
        await pilot.pause()
        await pilot.click(Select)

    assert snap_compare(SelectApp(), run_before=run_before)


def test_disable_command_palette(snap_compare):
    """Test command palette may be disabled by check_action.
    You should see a footer with an enabled binding, and the command palette binding greyed out.
    """

    class FooterApp(App):
        BINDINGS = [("b", "bell", "Bell")]

        def compose(self) -> ComposeResult:
            yield Footer()

        def check_action(
            self, action: str, parameters: tuple[object, ...]
        ) -> bool | None:
            if action == "command_palette":
                return None
            return True

    assert snap_compare(FooterApp())


def test_selection_list_wrap(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/5326"""

    class SelectionListApp(App):
        def compose(self) -> ComposeResult:
            yield SelectionList(("Hello World " * 100, 0))

    assert snap_compare(SelectionListApp())


def test_border_tab(snap_compare):
    """Test tab border style. You should see a border with a left align tab
    at the top and a right aligned tab at the bottom."""

    class TabApp(App):
        CSS = """
        Screen {
            align: center middle;
        }
        Label {
            border: tab $border;
            padding: 2 4;
            border-title-align: left;
        }
        """

        def compose(self) -> ComposeResult:
            label = Label("Hello, World")
            label.border_title = "Tab Border"
            label.border_subtitle = ":-)"
            yield label

    assert snap_compare(TabApp())


def test_dock_align(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/5345
    You should see a blue panel aligned to the top right of the screen, with a centered button.
    """

    class MainContainer(Static):
        def compose(self):
            yield Sidebar()

    # ~~~~ Sidebar widget ~~~~
    class Sidebar(Static):
        def compose(self):
            yield StartButtons()

    # ~~~~ the two buttons inside the sidebar ~~~~
    class StartButtons(Static):
        def compose(self):
            yield Button("Start", variant="primary", id="start")
            yield Button("Stop", variant="error", id="stop")

    # ~~~~ main ~~~~
    class Test1(App):
        CSS = """

        Screen {
            layout: horizontal;
        }

        MainContainer {    
            width: 100%;
            height: 100%;
            background: red;
            layout: horizontal;
        }


        Sidebar {
            width: 40;
            background: blue;
            border: double green;
            layout: vertical;

        /* seems to be a weird interaction between these two */
        /*    V V V V    */
            dock: right;
            align-horizontal: center;

        }

        StartButtons {
            max-width: 18.5;
            height: 5;
            background: $boost;
            padding: 1;
            layout: horizontal;
        }
        #start {
            dock: left;
        }
        #stop {
            dock: left;
        }


"""

        def compose(self):
            yield MainContainer()

    assert snap_compare(Test1())


def test_auto_parent_with_alignment(snap_compare):
    class Sidebar(Vertical):
        DEFAULT_CSS = """
        Sidebar {
            dock: right;  # Not strictly required to replicate the issue
            width: auto;
            height: auto;
            background: blue;
            align-vertical: bottom;

            #contents {
                width: auto;
                height: auto;
                background: red;
                border: white;
            }        
        }
        """

        def compose(self) -> ComposeResult:
            with Vertical(id="contents"):
                yield Button("Start")
                yield Button("Stop")

    class FloatSidebarApp(App):
        CSS = """
        Screen {
            layers: base sidebar;
        }
        """

        def compose(self) -> ComposeResult:
            yield Sidebar()

    assert snap_compare(FloatSidebarApp())


def test_select_refocus(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/5416

    The original bug was that the call to focus had no apparent effect as the Select
    was re-focusing itself after the Changed message was processed.

    You should see a list view with three items, where the second one is in focus.

    """
    opts = ["foo", "bar", "zoo"]

    class MyListItem(ListItem):
        def __init__(self, opts: list[str]) -> None:
            self.opts = opts
            self.lab = Label("Hello!")
            self.sel = Select(options=[(opt, opt) for opt in self.opts])
            super().__init__()

        def compose(self):
            with HorizontalGroup():
                yield self.lab
                yield self.sel

        def on_select_changed(self, event: Select.Changed):
            self.app.query_one(MyListView).focus()

    class MyListView(ListView):
        def compose(self):
            yield MyListItem(opts)
            yield MyListItem(opts)
            yield MyListItem(opts)

        def on_list_view_selected(self, event: ListView.Selected):
            event.item.sel.focus()
            event.item.sel.expanded = True

    class TUI(App):
        def compose(self):
            with Container():
                yield MyListView()

    assert snap_compare(TUI(), press=["down", "enter", "down", "down", "enter"])


def test_widgets_in_grid(snap_compare):
    """You should see a 3x3 grid of labels where the text is wrapped, and there is no superfluous space."""
    TEXT = """I must not fear.
Fear is the mind-killer.
Fear is the little-death that brings total obliteration.
I will face my fear.
I will permit it to pass over me and through me.
And when it has gone past, I will turn the inner eye to see its path.
Where the fear has gone there will be nothing. Only I will remain."""

    class MyApp(App):
        CSS = """
        VerticalGroup {
            layout: grid;
            grid-size: 3 3;
            grid-columns: 1fr;
            grid-rows: auto;
            height: auto;
            background: blue;
        }
        Label {        
            border: heavy red;
            text-align: left;
        }
        """

        def compose(self) -> ComposeResult:
            with VerticalGroup():
                for n in range(9):
                    label = Label(TEXT, id=f"label{n}")
                    label.border_title = str(n)
                    yield label

    assert snap_compare(MyApp(), terminal_size=(100, 50))


def test_arbitrary_selection(snap_compare):
    """You should see 3x3 labels with different text alignments.

    Text selection should start from somewhere in the first label, and
    end somewhere in the right label.

    """

    async def run_before(pilot: Pilot) -> None:
        await pilot.pause()
        await pilot.mouse_down(pilot.app.query_one("#first"), offset=(10, 10))
        await pilot.mouse_up(pilot.app.query_one("#last"), offset=(10, 10))
        await pilot.pause()

    assert snap_compare(
        SNAPSHOT_APPS_DIR / "text_selection.py",
        terminal_size=(175, 50),
        run_before=run_before,
    )


def test_collapsible_datatable(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/5407

    You should see two collapsibles, where the first is expanded.
    In the expanded coillapsible, you should see a DataTable filling the space,
    with all borders and both scrollbars visible.
    """

    class MyApp(App):
        CSS = """
        DataTable {
        
        }
        """

        def compose(self) -> ComposeResult:
            yield Collapsible(DataTable(id="t1"), id="c1", collapsed=False)
            yield Collapsible(Label("hello"), id="c2")

        def on_mount(self) -> None:
            self.query_one("#c1", Collapsible).styles.max_height = "50%"
            self.query_one("#c2", Collapsible).styles.max_height = "50%"

            t1 = self.query_one("#t1", DataTable)
            t1.styles.border = "heavy", "black"
            t1.add_column("A")
            for number in range(1, 100):
                t1.add_row(str(number) + " " * 200)

    assert snap_compare(MyApp())


def test_scrollbar_background_with_opacity(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/5458
    The scrollbar background should match the background of the widget."""

    class ScrollbarOpacityApp(App):
        CSS = """
        Screen {
            align: center middle;
        }

        VerticalScroll {
            width: 50%;
            height: 50%;
            background: blue 10%;
            scrollbar-background: blue 10%;
            scrollbar-color: cyan;
            scrollbar-size-vertical: 10;
        }
        """

        def compose(self) -> ComposeResult:
            with VerticalScroll():
                yield Static("\n".join(f"This is some text {n}" for n in range(100)))

    assert snap_compare(ScrollbarOpacityApp())


def test_static_markup(snap_compare):
    """Check that markup may be disabled.

    You should see 3 labels.

    This first label contains an invalid style, and should have tags removed.
    The second label should have the word "markup" emboldened.
    The third label has markup disabled, and should show tags without styles.
    """

    class LabelApp(App):
        def compose(self) -> ComposeResult:
            yield Label("There should be no [foo]tags or style[/foo]")
            yield Label("This allows [bold]markup[/bold]")
            yield Label("This does not allow [bold]markup[/bold]", markup=False)

    assert snap_compare(LabelApp())


def test_arbitrary_selection_double_cell(snap_compare):
    """Check that selection understands double width cells.

    You should see a smiley face followed by 'Hello World!', where Hello is highlighted.
    """

    class LApp(App):
        def compose(self) -> ComposeResult:
            yield Label("😃Hello World!")

    async def run_before(pilot: Pilot) -> None:
        await pilot.pause()
        await pilot.mouse_down(Label, offset=(2, 0))
        await pilot.mouse_up(Label, offset=(7, 0))
        await pilot.pause()

    assert snap_compare(LApp(), run_before=run_before)


def test_markup(snap_compare):
    """Check markup rendering, text in test should match the markup."""
    assert snap_compare(SNAPSHOT_APPS_DIR / "markup.py")


def test_no_wrap(snap_compare):
    """Test no wrap. You should see exactly two lines. The first is cropped, the second is
    cropped with an ellipsis symbol."""

    TEXT = """I must not fear. Fear is the mind-killer. Fear is the little-death that brings total obliteration. I will face my fear."""

    class NoWrapApp(App):
        CSS = """
        Label {
            max-width: 100vw;
            text-wrap: nowrap;
        }
        #label2 {
            text-overflow: ellipsis;
        }
        """

        def compose(self) -> ComposeResult:
            yield Label(TEXT, id="label1")
            yield Label(TEXT, id="label2")

    assert snap_compare(NoWrapApp())


def test_overflow(snap_compare):
    """Test overflow. You should see three labels across 4 lines. The first with overflow clip,
    the second with overflow ellipsis, and the last with overflow fold."""

    TEXT = "FOO " + "FOOBARBAZ" * 100

    class OverflowApp(App):
        CSS = """
        Label {
            max-width: 100vw;            
        }
        #label1 {
            # Overflow will be cropped
            text-overflow: clip;
            background: blue 20%;
        }
        #label2 {
            # Like clip, but last character will be an ellipsis
            text-overflow: ellipsis;
            background: green 20%;
        }
        #label3 {
            # Overflow will fold on to subsequence lines
            text-overflow: fold;
            background: red 20%;
        }
        """

        def compose(self) -> ComposeResult:
            yield Label(TEXT, id="label1")
            yield Label(TEXT, id="label2")
            yield Label(TEXT, id="label3")

    assert snap_compare(OverflowApp())


def test_empty_option_list(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/5489

    You should see an OptionList with no options, resulting in a small square at the top left.

    """

    class OptionListAutoCrash(App[None]):

        CSS = """
        OptionList {
            width: auto;
        }
        """

        def compose(self) -> ComposeResult:
            yield OptionList()

    assert snap_compare(OptionListAutoCrash())


def test_focus_within_transparent(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/5488

    You should see the right 50% in yellow, with a yellow OptionList and a black TextArea
    """

    class Panel(Vertical, can_focus=True):
        pass

    class FocusWithinTransparentApp(App[None]):

        CSS = """
        Screen {
            layout: horizontal;
        }

        Input {
            width: 1fr;
            height: 1fr;
        }

        Panel {
            padding: 5 10;
            background: red;
            &:focus, &:focus-within {
                background: yellow;
            }

            OptionList, OptionList:focus {
                height: 1fr;
                background: transparent;
            }
        }
        """

        def compose(self) -> ComposeResult:
            yield Input(placeholder="This is here to escape to")
            with Panel():
                yield OptionList(*["This is an option" for _ in range(30)])
                yield Input(placeholder="Escape out via here for the bug")

    assert snap_compare(FocusWithinTransparentApp(), press=["tab"])


def test_option_list_wrapping(snap_compare):
    """You should see a 40 cell wide Option list with a single line, ending in an ellipsis."""

    class OLApp(App):
        CSS = """
        OptionList { 
            width: 40;
            text-wrap: nowrap;
            text-overflow: ellipsis;
        }
        """

        def compose(self) -> ComposeResult:
            yield OptionList(
                "This is a very long option that is too wide to fit within the space provided and will overflow."
            )

    assert snap_compare(OLApp())


def test_add_separator(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/5431

    You should see a button on the left. On the right an option list with Option 1, separator, Option 3

    """

    class FocusTest(App[None]):

        CSS = """
        OptionList {
            height: 1fr;
        }
        """

        counter: var[int] = var(0)

        def compose(self) -> ComposeResult:
            with Horizontal():
                yield Button("Add")
                yield OptionList()

        @on(Button.Pressed)
        def add_more_stuff(self) -> None:
            self.counter += 1
            self.query_one(OptionList).add_option(
                (f"This is option {self.counter}" if self.counter % 2 else None)
            )

    async def run_before(pilot: Pilot) -> None:
        await pilot.pause()
        for _ in range(3):
            await pilot.click(Button)
            await pilot.pause(0.4)

    assert snap_compare(FocusTest(), run_before=run_before)


def test_visual_tooltip(snap_compare):
    """Test Visuals such as Content work in tooltips.

    You should see a tooltip under a label.
    The tooltip should have the word "Tooltip" highlighted in the accent color.

    """

    class TooltipApp(App[None]):
        TOOLTIP_DELAY = 0.4

        def compose(self) -> ComposeResult:
            progress_bar = Label("Hello, World")
            progress_bar.tooltip = Content.from_markup(
                "Hello, [bold $accent]Tooltip[/]!"
            )
            yield progress_bar

    async def run_before(pilot: Pilot) -> None:
        await pilot.pause()
        await pilot.hover(Label)
        await pilot.pause(0.4)
        await pilot.pause()

    assert snap_compare(TooltipApp(), run_before=run_before)


def test_auto_rich_log_width(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/5472

    You should see a tabbed content with a single line of text in the middle of the page.

    """

    class MinimalApp(App):
        """A minimal Textual app demonstrating the RichLog border issue."""

        CSS = """
        TabbedContent {
            height: 100%;
        }

        #title-container {
            align: center middle;
        }

        #title-rich-log {
            overflow-y: auto;
            background: black 0%;
            background: blue;
            width: auto;
            height: auto;
            /* When removing the border, the whole thing is gone? */
            # border: solid green 0%;
        }
        """

        def compose(self) -> ComposeResult:
            """Create child widgets for the app."""
            with TabbedContent():
                with TabPane("Title Slide", id="title-slide-tab"):
                    yield Container(RichLog(id="title-rich-log"), id="title-container")

        def on_mount(self) -> None:
            """Add some text to the RichLogs."""
            title_rich_log = self.query_one("#title-rich-log", RichLog)
            title_rich_log.write("This is the Title Slide RichLog")

    assert snap_compare(MinimalApp())


def test_auto_in_auto(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/5550

    You should see a table, with a bar at the bottom.

    The bottom bar should have some text right aligned, and two centered buttons in the center of
    the remaining space.

    """

    class MyApp(App):

        CSS = """

            MyApp {
                align: center middle;
                #datatable {
                    height: 1fr;
                }

                Horizontal {
                    height: auto;

                }

                #button_row {
                    align: center middle;
                }

                Button {
                    margin: 1;
                    height: auto;
                }

                #last_updated {
                    dock: right;
                    offset: 0 2;
                }

                Label {

                    height: auto;
                }
            }
        """

        def compose(self) -> ComposeResult:
            """
            Create the user interface
            """

            self.last_updated = Label(f"Last Updated: NOW", id="last_updated")

            yield Header()
            yield Vertical(
                DataTable(id="datatable"),
                Horizontal(
                    Button("OK", variant="primary", id="ok"),
                    Button("Cancel", variant="error", id="cancel"),
                    self.last_updated,
                    id="button_row",
                ),
                id="main_tab",
            )

        def on_mount(self) -> None:
            rows = [
                (
                    "Name",
                    "Occupation",
                    "Country",
                ),
                (
                    "Mike",
                    "Python Wrangler",
                    "USA",
                ),
                (
                    "Bill",
                    "Engineer",
                    "UK",
                ),
                ("Dee", "Manager", "Germany"),
            ]
            table = self.query_one(DataTable)
            table.clear(columns=True)
            table.add_columns(*rows[0])
            table.add_rows(rows[1:])

    assert snap_compare(MyApp())


def test_panel_border_title_colors(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/5548

    You should see four labels with panel type borders. The border title colors
    should match the description in the label."""

    class BorderTitleApp(App):
        CSS = """
        Label {
            border: panel red;
            width: 40;
            margin: 1;
        }

        .with-border-title-color {
            border-title-color: yellow;
        }

        .with-border-title-background {
            border-title-background: green;
        }
        """

        def compose(self) -> ComposeResult:
            yield Label(
                "with default",
            )
            yield Label(
                "with yellow color",
                classes="with-border-title-color",
            )
            yield Label(
                "with green background",
                classes="with-border-title-background",
            )
            yield Label(
                "with yellow color and green background",
                classes="with-border-title-background with-border-title-color",
            )

        def on_mount(self) -> None:
            for label in self.query(Label):
                label.border_title = "Border title"

    assert snap_compare(BorderTitleApp())
