import pytest

from textual._etc import TimeToCompletion


def test_size() -> None:
    """The number of samples should respect the window size."""
    time_to_completion = TimeToCompletion(20, sample_window_size=10)
    for n in range(20):
        assert len(time_to_completion) == min(n, 10)
        time_to_completion.record(n, n)


def test_no_go_backwards() -> None:
    """It should not be possible to go backwards in time."""
    time_to_completion = TimeToCompletion(10)
    time_to_completion.record(2)
    with pytest.raises(ValueError):
        time_to_completion.record(1)


def test_no_go_past_end() -> None:
    """It should not be possible to go past the destination value."""
    with pytest.raises(ValueError):
        TimeToCompletion(1).record(2)


def test_estimate() -> None:
    """Test the time to completion calculation."""
    time_to_completion = TimeToCompletion(100)
    for n in range(10):
        time_to_completion.record(n, n)
    assert time_to_completion.estimated_time_to_complete == 91


def test_estimate_small_window() -> None:
    """Test the time to completion calculation."""
    time_to_completion = TimeToCompletion(100, sample_window_size=5)
    for n in range(10):
        time_to_completion.record(n, n)
    assert time_to_completion.estimated_time_to_complete == 91


def test_estimate_bigger_step() -> None:
    """Test the time to completion calculation."""
    time_to_completion = TimeToCompletion(100)
    for n in range(0, 10, 2):
        time_to_completion.record(n, n)
    assert time_to_completion.estimated_time_to_complete == 92


def test_estimate_no_samples() -> None:
    """Time to completion should be 0 of no samples exist."""
    assert TimeToCompletion(100).estimated_time_to_complete == 0
