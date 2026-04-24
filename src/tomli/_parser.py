# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2021 Taneli Hukkinen
# Licensed to PSF under a Contributor Agreement.

from __future__ import annotations

import sys
from types import MappingProxyType

from ._re import (
    RE_DATETIME,
    RE_LOCALTIME,
    RE_NUMBER,
    match_to_datetime,
    match_to_localtime,
    match_to_number,
)

TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import IO, Any, Final

    from ._types import Key, ParseFloat, Pos

# Inline tables/arrays are implemented using recursion. Pathologically
# nested documents cause pure Python to raise RecursionError (which is OK),
# but mypyc binary wheels will crash unrecoverably (not OK). According to
# mypyc docs this will be fixed in the future:
# https://mypyc.readthedocs.io/en/latest/differences_from_python.html#stack-overflows
# Before mypyc's fix is in, recursion needs to be limited by this library.
# Choosing `sys.getrecursionlimit()` as maximum inline table/array nesting
# level, as it allows more nesting than pure Python, but still seems a far
# lower number than where mypyc binaries crash.
MAX_INLINE_NESTING: Final = sys.getrecursionlimit()

# Pathologically excessive number of parts in a key runs into quadratic
# behavior (e.g. in Flags.is_).
# Even if keys aren't currently parsed using recursion, they name a
# recursive structure, so it makes sense to limit it using getrecursionlimit()
# and RecursionError.
MAX_KEY_PARTS: Final = sys.getrecursionlimit()

ASCII_CTRL: Final = frozenset(chr(i) for i in range(32)) | frozenset(chr(127))

# Neither of these sets include quotation mark or backslash. They are
# currently handled as separate cases in the parser functions.
ILLEGAL_BASIC_STR_CHARS: Final = ASCII_CTRL - frozenset("\t")
ILLEGAL_MULTILINE_BASIC_STR_CHARS: Final = ASCII_CTRL - frozenset("\t\n")

ILLEGAL_LITERAL_STR_CHARS: Final = ILLEGAL_BASIC_STR_CHARS
ILLEGAL_MULTILINE_LITERAL_STR_CHARS: Final = ILLEGAL_MULTILINE_BASIC_STR_CHARS

ILLEGAL_COMMENT_CHARS: Final = ILLEGAL_BASIC_STR_CHARS

TOML_WS: Final = frozenset(" \t")
TOML_WS_AND_NEWLINE: Final = TOML_WS | frozenset("\n")
BARE_KEY_CHARS: Final = frozenset(
    "abcdefghijklmnopqrstuvwxyz" "ABCDEFGHIJKLMNOPQRSTUVWXYZ" "0123456789" "-_"
)
KEY_INITIAL_CHARS: Final = BARE_KEY_CHARS | frozenset("\"'")
HEXDIGIT_CHARS: Final = frozenset("abcdef" "ABCDEF" "0123456789")

BASIC_STR_ESCAPE_REPLACEMENTS: Final = MappingProxyType(
    {
        "\\b": "\u0008",  # backspace
        "\\t": "\u0009",  # tab
        "\\n": "\u000a",  # linefeed
        "\\f": "\u000c",  # form feed
        "\\r": "\u000d",  # carriage return
        "\\e": "\u001b",  # escape
        '\\"': "\u0022",  # quote
        "\\\\": "\u005c",  # backslash
    }
)


class DEPRECATED_DEFAULT:
    """Sentinel to be used as default arg during deprecation
    period of TOMLDecodeError's free-form arguments."""


class TOMLDecodeError(ValueError):
    """An error raised if a document is not valid TOML.

    Adds the following attributes to ValueError:
    msg: The unformatted error message
    doc: The TOML document being parsed
    pos: The index of doc where parsing failed
    lineno: The line corresponding to pos
    colno: The column corresponding to pos
    """

    def __init__(
        self,
        msg: str | type[DEPRECATED_DEFAULT] = DEPRECATED_DEFAULT,
        doc: str | type[DEPRECATED_DEFAULT] = DEPRECATED_DEFAULT,
        pos: Pos | type[DEPRECATED_DEFAULT] = DEPRECATED_DEFAULT,
        *args: Any,
    ):
        if (
            args
            or not isinstance(msg, str)
            or not isinstance(doc, str)
            or not isinstance(pos, int)
        ):
            import warnings

            warnings.warn(
                "Free-form arguments for TOMLDecodeError are deprecated. "
                "Please set 'msg' (str), 'doc' (str) and 'pos' (int) arguments only.",
                DeprecationWarning,
                stacklevel=2,
            )
            if pos is not DEPRECATED_DEFAULT:
                args = pos, *args
            if doc is not DEPRECATED_DEFAULT:
                args = doc, *args
            if msg is not DEPRECATED_DEFAULT:
                args = msg, *args
            ValueError.__init__(self, *args)
            return

        lineno = doc.count("\n", 0, pos) + 1
        if lineno == 1:
            colno = pos + 1
        else:
            colno = pos - doc.rindex("\n", 0, pos)

        if pos >= len(doc):
            coord_repr = "end of document"
        else:
            coord_repr = f"line {lineno}, column {colno}"
        errmsg = f"{msg} (at {coord_repr})"
        ValueError.__init__(self, errmsg)

        self.msg = msg
        self.doc = doc
        self.pos = pos
        self.lineno = lineno
        self.colno = colno


def load(__fp: IO[bytes], *, parse_float: ParseFloat = float) -> dict[str, Any]:
    """Parse TOML from a binary file object."""
    pass


def loads(__s: str, *, parse_float: ParseFloat = float) -> dict[str, Any]:
    """Parse TOML from a string."""
    pass


class Flags:
    """Flags that map to parsed keys/namespaces."""

    # Marks an immutable namespace (inline array or inline table).
    FROZEN: Final = 0
    # Marks a nest that has been explicitly created and can no longer
    # be opened using the "[table]" syntax.
    EXPLICIT_NEST: Final = 1

    def __init__(self) -> None:
        self._flags: dict[str, dict[Any, Any]] = {}
        self._pending_flags: set[tuple[Key, int]] = set()

    def add_pending(self, key: Key, flag: int) -> None:
        pass

    def finalize_pending(self) -> None:
        pass

    def unset_all(self, key: Key) -> None:
        pass

    def set(self, key: Key, flag: int, *, recursive: bool) -> None:  # noqa: A003
        pass

    def is_(self, key: Key, flag: int) -> bool:
        pass


class NestedDict:
    def __init__(self) -> None:
        # The parsed content of the TOML document
        self.dict: dict[str, Any] = {}

    def get_or_create_nest(
        self,
        key: Key,
        *,
        access_lists: bool = True,
    ) -> dict[str, Any]:
        pass

    def append_nest_to_list(self, key: Key) -> None:
        pass


class Output:
    def __init__(self) -> None:
        self.data = NestedDict()
        self.flags = Flags()


def skip_chars(src: str, pos: Pos, chars: Iterable[str]) -> Pos:
    pass


def skip_until(
    src: str,
    pos: Pos,
    expect: str,
    *,
    error_on: frozenset[str],
    error_on_eof: bool,
) -> Pos:
    pass


def skip_comment(src: str, pos: Pos) -> Pos:
    pass


def skip_comments_and_array_ws(src: str, pos: Pos) -> Pos:
    pass


def create_dict_rule(src: str, pos: Pos, out: Output) -> tuple[Pos, Key]:
    pass


def create_list_rule(src: str, pos: Pos, out: Output) -> tuple[Pos, Key]:
    pass


def key_value_rule(
    src: str, pos: Pos, out: Output, header: Key, parse_float: ParseFloat
) -> Pos:
    pass


def parse_key_value_pair(
    src: str, pos: Pos, parse_float: ParseFloat, nest_lvl: int
) -> tuple[Pos, Key, Any]:
    pass


def parse_key(src: str, pos: Pos) -> tuple[Pos, Key]:
    pass


def parse_key_part(src: str, pos: Pos) -> tuple[Pos, str]:
    pass


def parse_one_line_basic_str(src: str, pos: Pos) -> tuple[Pos, str]:
    pass


def parse_array(
    src: str, pos: Pos, parse_float: ParseFloat, nest_lvl: int
) -> tuple[Pos, list[Any]]:
    pass


def parse_inline_table(
    src: str, pos: Pos, parse_float: ParseFloat, nest_lvl: int
) -> tuple[Pos, dict[str, Any]]:
    pass


def parse_basic_str_escape(
    src: str, pos: Pos, *, multiline: bool = False
) -> tuple[Pos, str]:
    pass


def parse_basic_str_escape_multiline(src: str, pos: Pos) -> tuple[Pos, str]:
    pass


def parse_hex_char(src: str, pos: Pos, hex_len: int) -> tuple[Pos, str]:
    pass


def parse_literal_str(src: str, pos: Pos) -> tuple[Pos, str]:
    pass


def parse_multiline_str(src: str, pos: Pos, *, literal: bool) -> tuple[Pos, str]:
    pass


def parse_basic_str(src: str, pos: Pos, *, multiline: bool) -> tuple[Pos, str]:
    pass


def parse_value(
    src: str, pos: Pos, parse_float: ParseFloat, nest_lvl: int
) -> tuple[Pos, Any]:
    pass


def is_unicode_scalar_value(codepoint: int) -> bool:
    pass


def make_safe_parse_float(parse_float: ParseFloat) -> ParseFloat:
    """A decorator to make `parse_float` safe.

    `parse_float` must not return dicts or lists, because these types
    would be mixed with parsed TOML tables and arrays, thus confusing
    the parser. The returned decorated callable raises `ValueError`
    instead of returning illegal types.
    """
    pass
