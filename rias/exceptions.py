"""\
Rias Custom Exceptions
======================

Author: XA <xa@mes3.dev>
Created on: Sunday, June 23 2024
Last updated on: Sunday, July 07 2024

This module defines custom exception classes for the Rias framework.
These exceptions are used throughout the Rias framework to handle
various error conditions in a consistent and meaningful way.
"""

from __future__ import annotations

import os
import sys
import types
import typing as t

from rias.utils.functional import bold

_TB_GRADIENT: tuple[int, ...] = 216, 214, 209, 208, 210, 204, 203, 202, 196


def _enumerate_frames(
    frames: list[str],
) -> t.Generator[tuple[int, str], None, None]:
    """Enumerate traceback frames with gradient indexing.

    :param frames: List of traceback frames (strings).
    :return: Generator yielding index and frame string.
    """
    stop = len(_TB_GRADIENT) - 1
    if (count := len(frames)) == 1:
        yield stop, frames[0]
        return
    step = stop // (count - 1)
    for idx, frame in zip(range(count), frames):
        yield step * idx, frame


show: t.Callable[[str], int] = sys.stderr.write


def exception_hook(
    exctype: type[BaseException],
    value: BaseException,
    traceback: types.TracebackType | None,
) -> None:
    """Exception hook to format and display traceback information with
    color gradients.

    This function replaces the default `sys.excepthook` with a custom
    one that provides more visually appealing and informative traceback
    information, including color gradients for each traceback level and
    bold formatting for the exception type and message.

    :param exctype: The exception type.
    :param value: The exception instance that was raised.
    :param traceback: The traceback object, containing the call stack
        at the point where the exception was raised.
    """
    padding: int = 0
    frames: list[str] = []
    show("Traceback:\n")
    # Iterate through the traceback linked list to gather frame details.
    # Note that, we're skipping the frames which are not actual files,
    # for example, <string>, <module>, etc.
    while traceback:
        if (filename := traceback.tb_frame.f_code.co_filename).startswith("<"):
            traceback = traceback.tb_next
            continue
        module = os.path.relpath(filename.rsplit(".", -1)[0]).replace("/", ".")
        if (name := traceback.tb_frame.f_code.co_qualname) in (
            "<module>",
            "<lambda>",
        ):
            name = ""
        frames.append(
            (
                "\N{box drawings light up and right}"
                "\N{box drawings light left}"
                f'At "{filename}:{traceback.tb_lineno}" '
                f"in {module}{f'.{name}' if name else ''}\n"
            )
        )
        traceback = traceback.tb_next
    for idx, frame in _enumerate_frames(frames):
        show(f"{'  ' * padding}\x1b[38;5;{_TB_GRADIENT[idx]}m{frame}\x1b[0m")
        padding += 1
    show(f"{bold(f'{exctype.__name__}: {value}')}\n")


sys.excepthook = exception_hook


class RiasException(Exception):
    """Base class for all exceptions raised by the Rias framework."""

    pass


class RiasEnvironmentError(RiasException):
    """Rias' environment is incorrectly configured."""

    pass
