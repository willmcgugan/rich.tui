import pytest

from textual._document import Document
from textual.widgets import TextArea

TEXT = """I must not fear.
Fear is the mind-killer."""


def test_insert_text_no_newlines():
    document = Document()
    document.load_text(TEXT)
    document.insert_range((0, 1), (0, 1), " really")
    assert document._lines == [
        "I really must not fear.",
        "Fear is the mind-killer.",
    ]


def test_insert_text_empty_string():
    document = Document()
    document.load_text(TEXT)
    document.insert_range((0, 1), (0, 1), "")
    assert document._lines == ["I must not fear.", "Fear is the mind-killer."]


@pytest.mark.xfail(reason="undecided on behaviour")
def test_insert_text_invalid_column():
    # TODO - what is the correct behaviour here?
    #  right now it appends to the end of the line if the column is too large.
    document = Document()
    document.load_text(TEXT)
    document.insert_range((0, 999), (0, 999), " really")
    assert document._lines == ["I must not fear.", "Fear is the mind-killer."]


@pytest.mark.xfail(reason="undecided on behaviour")
def test_insert_text_invalid_row():
    # TODO - this raises an IndexError for list index out of range
    document = Document()
    document.load_text(TEXT)
    document.insert_range((999, 0), (999, 0), " really")
    assert document._lines == ["I must not fear.", "Fear is the mind-killer."]


def test_insert_text_range_newline_file_start():
    document = Document()
    document.load_text(TEXT)
    document.insert_range((0, 0), (0, 0), "\n")
    assert document._lines == ["", "I must not fear.", "Fear is the mind-killer."]


def test_insert_text_newline_splits_line():
    document = Document()
    document.load_text(TEXT)
    document.insert_range((0, 1), (0, 1), "\n")
    assert document._lines == ["I", " must not fear.", "Fear is the mind-killer."]


def test_insert_text_multiple_lines_ends_with_newline():
    document = Document()
    document.load_text(TEXT)
    document.insert_range((0, 1), (0, 1), "Hello,\nworld!\n")
    assert document._lines == [
        "IHello,",
        "world!",
        " must not fear.",
        "Fear is the mind-killer.",
    ]


def test_insert_text_multiple_lines_starts_with_newline():
    document = Document()
    document.load_text(TEXT)
    document.insert_range((0, 1), (0, 1), "\nHello,\nworld!\n")
    assert document._lines == [
        "I",
        "Hello,",
        "world!",
        " must not fear.",
        "Fear is the mind-killer.",
    ]


def test_insert_range_text_no_newlines():
    """Ensuring we can do a simple replacement of text."""
    document = Document()
    document.load_text(TEXT)
    document.insert_range((0, 2), (0, 6), "MUST")
    assert document._lines == [
        "I MUST not fear.",
        "Fear is the mind-killer.",
    ]
