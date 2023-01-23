from __future__ import annotations

from typing import TYPE_CHECKING, Awaitable, Callable, Type, TypeVar

import rich.repr
from rich.style import Style

from ._types import MessageTarget
from .geometry import Offset, Size
from .keys import _get_key_aliases, _get_key_display
from .message import Message

MouseEventT = TypeVar("MouseEventT", bound="MouseEvent")

if TYPE_CHECKING:
    from .timer import Timer as TimerClass
    from .timer import TimerCallback
    from .widget import Widget


@rich.repr.auto
class Event(Message):
    """The base class for all events."""

    def __rich_repr__(self) -> rich.repr.Result:
        yield from ()


@rich.repr.auto
class Callback(Event, bubble=False, verbose=True):
    def __init__(
        self, sender: MessageTarget, callback: Callable[[], Awaitable[None]]
    ) -> None:
        self.callback = callback
        super().__init__(sender)

    def __rich_repr__(self) -> rich.repr.Result:
        yield "callback", self.callback


class InvokeCallbacks(Event, bubble=False, verbose=True):
    """Sent after the Screen is updated"""


class ShutdownRequest(Event):
    pass


class Shutdown(Event):
    pass


class Load(Event, bubble=False):
    """
    Sent when the App is running but *before* the terminal is in application mode.

    Use this event to run any set up that doesn't require any visuals such as loading
    configuration and binding keys.


    """


class Idle(Event, bubble=False):
    """Sent when there are no more items in the message queue.

    This is a pseudo-event in that it is created by the Textual system and doesn't go
    through the usual message queue.

    """


class Action(Event):
    __slots__ = ["action"]

    def __init__(self, sender: MessageTarget, action: str) -> None:
        super().__init__(sender)
        self.action = action

    def __rich_repr__(self) -> rich.repr.Result:
        yield "action", self.action


class Resize(Event, bubble=False):
    """Sent when the app or widget has been resized.
    Args:
        sender: The sender of the event (the Screen).
        size: The new size of the Widget.
        virtual_size: The virtual size (scrollable size) of the Widget.
        container_size: The size of the Widget's container widget. Defaults to None.

    """

    __slots__ = ["size", "virtual_size", "container_size"]

    def __init__(
        self,
        sender: MessageTarget,
        size: Size,
        virtual_size: Size,
        container_size: Size | None = None,
    ) -> None:
        self.size = size
        self.virtual_size = virtual_size
        self.container_size = size if container_size is None else container_size
        super().__init__(sender)

    def can_replace(self, message: "Message") -> bool:
        return isinstance(message, Resize)

    def __rich_repr__(self) -> rich.repr.Result:
        yield "size", self.size
        yield "virtual_size", self.virtual_size
        yield "container_size", self.container_size, self.size


class Compose(Event, bubble=False, verbose=True):
    """Sent to a widget to request it to compose and mount children."""


class Mount(Event, bubble=False, verbose=False):
    """Sent when a widget is *mounted* and may receive messages."""


class Unmount(Mount, bubble=False, verbose=False):
    """Sent when a widget is unmounted and may not longer receive messages."""


class Show(Event, bubble=False):
    """Sent when a widget has become visible."""


class Hide(Event, bubble=False):
    """Sent when a widget has been hidden.

    A widget may be hidden by setting its `visible` flag to `False`, if it is no longer in a layout,
    or if it has been offset beyond the edges of the terminal.

    """


class Ready(Event, bubble=False):
    """Sent to the app when the DOM is ready."""


@rich.repr.auto
class MouseCapture(Event, bubble=False):
    """Sent when the mouse has been captured.

    When a mouse has been captured, all further mouse events will be sent to the capturing widget.


    Args:
        sender: The sender of the event, (in this case the app).
        mouse_position: The position of the mouse when captured.

    """

    def __init__(self, sender: MessageTarget, mouse_position: Offset) -> None:
        super().__init__(sender)
        self.mouse_position = mouse_position

    def __rich_repr__(self) -> rich.repr.Result:
        yield None, self.mouse_position


@rich.repr.auto
class MouseRelease(Event, bubble=False):
    """Mouse has been released.

    Args:
        sender: The sender of the event, (in this case the app).
        mouse_position: The position of the mouse when released.
    """

    def __init__(self, sender: MessageTarget, mouse_position: Offset) -> None:
        super().__init__(sender)
        self.mouse_position = mouse_position

    def __rich_repr__(self) -> rich.repr.Result:
        yield None, self.mouse_position


class InputEvent(Event):
    """Base class for input events."""


@rich.repr.auto
class Key(InputEvent):
    """Sent when the user hits a key on the keyboard.

    Args:
        sender: The sender of the event (always the App).
        key: The key that was pressed.
        character: A printable character or ``None`` if it is not printable.

    Attributes:
        aliases: The aliases for the key, including the key itself.
    """

    __slots__ = ["key", "character", "aliases"]

    def __init__(self, sender: MessageTarget, key: str, character: str | None) -> None:
        super().__init__(sender)
        self.key = key
        self.character = (
            (key if len(key) == 1 else None) if character is None else character
        )
        self.aliases: list[str] = _get_key_aliases(key)

    def __rich_repr__(self) -> rich.repr.Result:
        yield "key", self.key
        yield "character", self.character
        yield "name", self.name
        yield "is_printable", self.is_printable
        yield "aliases", self.aliases, [self.key]

    @property
    def name(self) -> str:
        """Name of a key suitable for use as a Python identifier."""
        return _key_to_identifier(self.key).lower()

    @property
    def name_aliases(self) -> list[str]:
        """The corresponding name for every alias in `aliases` list."""
        return [_key_to_identifier(key) for key in self.aliases]

    @property
    def is_printable(self) -> bool:
        """Check if the key is printable (produces a unicode character).

        Returns:
            True if the key is printable.
        """
        return False if self.character is None else self.character.isprintable()


def _key_to_identifier(key: str) -> str:
    """Convert the key string to a name suitable for use as a Python identifier."""
    if len(key) == 1 and key.isupper():
        key = f"upper_{key.lower()}"
    return key.replace("+", "_").lower()


@rich.repr.auto
class MouseEvent(InputEvent, bubble=True):
    """Sent in response to a mouse event.

    Args:
        sender: The sender of the event.
        x: The relative x coordinate.
        y: The relative y coordinate.
        delta_x: Change in x since the last message.
        delta_y: Change in y since the last message.
        button: Indexed of the pressed button.
        shift: True if the shift key is pressed.
        meta: True if the meta key is pressed.
        ctrl: True if the ctrl key is pressed.
        screen_x: The absolute x coordinate.
        screen_y: The absolute y coordinate.
        style: The Rich Style under the mouse cursor.

    """

    __slots__ = [
        "x",
        "y",
        "delta_x",
        "delta_y",
        "button",
        "shift",
        "meta",
        "ctrl",
        "screen_x",
        "screen_y",
        "_style",
    ]

    def __init__(
        self,
        sender: MessageTarget,
        x: int,
        y: int,
        delta_x: int,
        delta_y: int,
        button: int,
        shift: bool,
        meta: bool,
        ctrl: bool,
        screen_x: int | None = None,
        screen_y: int | None = None,
        style: Style | None = None,
    ) -> None:
        super().__init__(sender)
        self.x = x
        self.y = y
        self.delta_x = delta_x
        self.delta_y = delta_y
        self.button = button
        self.shift = shift
        self.meta = meta
        self.ctrl = ctrl
        self.screen_x = x if screen_x is None else screen_x
        self.screen_y = y if screen_y is None else screen_y
        self._style = style or Style()

    @classmethod
    def from_event(cls: Type[MouseEventT], event: MouseEvent) -> MouseEventT:
        new_event = cls(
            event.sender,
            event.x,
            event.y,
            event.delta_x,
            event.delta_y,
            event.button,
            event.shift,
            event.meta,
            event.ctrl,
            event.screen_x,
            event.screen_y,
            event._style,
        )
        return new_event

    def __rich_repr__(self) -> rich.repr.Result:
        yield "x", self.x
        yield "y", self.y
        yield "delta_x", self.delta_x, 0
        yield "delta_y", self.delta_y, 0
        if self.screen_x != self.x:
            yield "screen_x", self.screen_x
        if self.screen_y != self.y:
            yield "screen_y", self.screen_y
        yield "button", self.button, 0
        yield "shift", self.shift, False
        yield "meta", self.meta, False
        yield "ctrl", self.ctrl, False

    @property
    def offset(self) -> Offset:
        """The mouse coordinate as an offset.

        Returns:
            Mouse coordinate.

        """
        return Offset(self.x, self.y)

    @property
    def screen_offset(self) -> Offset:
        """Mouse coordinate relative to the screen.

        Returns:
            Mouse coordinate.
        """
        return Offset(self.screen_x, self.screen_y)

    @property
    def delta(self) -> Offset:
        """Mouse coordinate delta (change since last event).

        Returns:
            Mouse coordinate.

        """
        return Offset(self.delta_x, self.delta_y)

    @property
    def style(self) -> Style:
        """The (Rich) Style under the cursor."""
        return self._style or Style()

    @style.setter
    def style(self, style: Style) -> None:
        self._style = style

    def get_content_offset(self, widget: Widget) -> Offset | None:
        """Get offset within a widget's content area, or None if offset is not in content (i.e. padding or border).

        Args:
            widget: Widget receiving the event.

        Returns:
            An offset where the origin is at the top left of the content area.
        """
        if self.screen_offset not in widget.content_region:
            return None
        return self.offset - widget.gutter.top_left

    def _apply_offset(self, x: int, y: int) -> MouseEvent:
        return self.__class__(
            self.sender,
            x=self.x + x,
            y=self.y + y,
            delta_x=self.delta_x,
            delta_y=self.delta_y,
            button=self.button,
            shift=self.shift,
            meta=self.meta,
            ctrl=self.ctrl,
            screen_x=self.screen_x,
            screen_y=self.screen_y,
            style=self.style,
        )


@rich.repr.auto
class MouseMove(MouseEvent, bubble=False, verbose=True):
    """Sent when the mouse cursor moves."""


@rich.repr.auto
class MouseDown(MouseEvent, bubble=True, verbose=True):
    pass


@rich.repr.auto
class MouseUp(MouseEvent, bubble=True, verbose=True):
    pass


@rich.repr.auto
class MouseScrollDown(MouseEvent, bubble=True):
    pass


@rich.repr.auto
class MouseScrollUp(MouseEvent, bubble=True):
    pass


class Click(MouseEvent, bubble=True):
    pass


@rich.repr.auto
class Timer(Event, bubble=False, verbose=True):
    __slots__ = ["time", "count", "callback"]

    def __init__(
        self,
        sender: MessageTarget,
        timer: "TimerClass",
        time: float,
        count: int = 0,
        callback: TimerCallback | None = None,
    ) -> None:
        super().__init__(sender)
        self.timer = timer
        self.time = time
        self.count = count
        self.callback = callback

    def __rich_repr__(self) -> rich.repr.Result:
        yield self.timer.name
        yield "count", self.count


class Enter(Event, bubble=False, verbose=True):
    pass


class Leave(Event, bubble=False, verbose=True):
    pass


class Focus(Event, bubble=False):
    pass


class Blur(Event, bubble=False):
    pass


class DescendantFocus(Event, bubble=True, verbose=True):
    pass


class DescendantBlur(Event, bubble=True, verbose=True):
    pass


@rich.repr.auto
class Paste(Event, bubble=True):
    """Event containing text that was pasted into the Textual application.
    This event will only appear when running in a terminal emulator that supports
    bracketed paste mode. Textual will enable bracketed pastes when an app starts,
    and disable it when the app shuts down.

    Args:
        sender: The sender of the event, (in this case the app).
        text: The text that has been pasted.
    """

    def __init__(self, sender: MessageTarget, text: str) -> None:
        super().__init__(sender)
        self.text = text

    def __rich_repr__(self) -> rich.repr.Result:
        yield "text", self.text


class ScreenResume(Event, bubble=False):
    pass


class ScreenSuspend(Event, bubble=False):
    pass
