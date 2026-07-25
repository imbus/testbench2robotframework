"""Renders the execution comment of a TestBench keyword.

A TestBench keyword usually maps to a Robot Framework user keyword, which can
be composed of further keywords. This module renders that whole structure as
ONE flat table so that the comment stays usable when it is exported to PDF or
pasted into Word:

- no nested tables, no rowspan, no CSS classes, no <details>, no JavaScript
- nesting is expressed by indentation with '&nbsp;' only
- rounded status pills are decoration: a renderer that ignores 'border-radius'
  shows rectangular badges and loses no information

Rules of the layout:
- every keyword is one row: status, name in bold, arguments behind it, duration
- the log messages of a keyword are rows of their own below it, in the order
  Robot recorded them, so a message stays between the sub keywords it happened
  between. Keywords that have sub keywords can have own messages as well.
- a structural limit folds keywords away, never their log messages
"""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum

from robot.result import Keyword, Message

INDENT = "&nbsp;" * 4
LINE_COLOR = "#e4e9ec"
GROUP_LINE_COLOR = "#b0bec5"
GROUP_BACKGROUND = "#f7f9fa"
MONOSPACE = "font-family: Consolas, Menlo, monospace;"
# Sferyx ignores 'font-family' in a style attribute but renders <tt> monospace.
MONO_OPEN = f"<tt style='{MONOSPACE}'>"
MONO_CLOSE = "</tt>"
TABLE_STYLE = (
    "border-collapse: collapse; width: 100%; border: 0; "
    "font-family: Segoe UI, Helvetica, Arial, sans-serif; font-size: 12px;"
)
# Sferyx draws table lines only from these attributes; a browser overrides them
# with the style above and with 'border: 0' on every cell, so it keeps showing
# just the horizontal separators.
TABLE_ATTRIBUTES = "border='1' cellspacing='0' cellpadding='4' width='100%'"
HEADERS = ("Status", "Level", "Step / Message", "Duration", "Time")

# Per column, in the order of HEADERS. The viewer may show the table in a
# container that is too narrow to scroll (the maximised modal of iTORX), and
# then the browser shrinks every column until it fits: 'Duration' wraps into
# 'Dur atio n' and a timestamp into three lines. So the narrow columns refuse to
# wrap and keep a minimum width, while 'Step / Message' takes the rest and may
# break long words - a keyword argument can be a path without a single space.
COLUMN_STYLE = (
    "white-space: nowrap; ",
    "white-space: nowrap; ",
    "width: 100%; word-wrap: break-word; overflow-wrap: anywhere; ",
    "white-space: nowrap; min-width: 66px; text-align: right; ",
    "white-space: nowrap; min-width: 88px; ",
)

# Machine readable anchors, in the order of HEADERS. Other tools read these
# comments back - the TestBench AI service takes the failure message out of the
# 'text' cell of the row whose data-tb-level is FAIL - and an attribute survives
# a restyling of the table, unlike a regular expression over the formatting.
CELL_ATTRIBUTE = (
    " data-tb-role='status'",
    " data-tb-role='level'",
    " data-tb-role='text'",
    "",
    "",
)

LOG_LEVEL_ORDER = {"TRACE": 0, "DEBUG": 1, "INFO": 2, "WARN": 3, "ERROR": 4, "FAIL": 4}
DEFAULT_LOG_LEVEL_ORDER = 2


class PillColor(Enum):
    """Colours of the status pills.

    Derived from the Robot Framework log (robot/htmldata/rebot/common.css), but
    toned down: as a large filled pill the saturated original colours read as an
    alarm even on a passing step.
    """

    PASSED = ("#1f8a4c", "#fff")
    FAILED = ("#c62828", "#fff")
    WARNING = ("#b98900", "#fff")
    MUTED = ("#eceff1", "#37474f")
    QUIET = ("#eceff1", "#78909c")

    def __init__(self, background: str, foreground: str) -> None:
        self.background = background
        self.foreground = foreground

    def pill(self, label: str, *, rounded: bool = True) -> str:
        """A status pill.

        The Sferyx editor of the TestBench Java client ignores 'padding',
        'margin', 'border-radius' and 'letter-spacing' on an inline element, but
        honours 'background-color'. So the breathing room is baked into the text
        with '&nbsp;' and the radius is left as decoration for browsers.
        """
        radius = "border-radius: 9px; " if rounded else ""
        return (
            f"<span style='{radius}background-color: {self.background}; "
            f"color: {self.foreground}; padding: 1px 4px; font-size: 11px; "
            f"font-weight: bold; white-space: nowrap;'>&nbsp;{label}&nbsp;</span>"
        )


PILL_COLOR_BY_LABEL = {
    "PASS": PillColor.PASSED,
    "FAIL": PillColor.FAILED,
    "ERROR": PillColor.FAILED,
    "SKIP": PillColor.WARNING,
    "WARN": PillColor.WARNING,
    "INFO": PillColor.MUTED,
    "DEBUG": PillColor.QUIET,
    "TRACE": PillColor.QUIET,
    "NOT RUN": PillColor.QUIET,
    "NOT SET": PillColor.QUIET,
}


def render_pill(label: str, *, rounded: bool = True) -> str:
    if not label:
        return ""
    return PILL_COLOR_BY_LABEL.get(label, PillColor.MUTED).pill(label, rounded=rounded)


def is_message(item) -> bool:
    return isinstance(item, Message)


def is_iteration(item) -> bool:
    return "ITERATION" in str(getattr(item, "type", "")) and hasattr(item, "assign")


def full_name_of(keyword: Keyword) -> str:
    """Library-qualified keyword name.

    'full_name' only exists since Robot Framework 7.0; before that the name is
    split into 'libname' and 'kwname'.
    """
    full_name = getattr(keyword, "full_name", None)
    if full_name:
        return str(full_name)
    name = getattr(keyword, "kwname", None) or keyword.name or ""
    library = getattr(keyword, "libname", None)
    return f"{library}.{name}" if library else str(name)


def as_datetime(timestamp) -> datetime | None:
    """Robot Framework stores timestamps as strings before 7.0 and as datetime since."""
    if not timestamp:
        return None
    if isinstance(timestamp, datetime):
        return timestamp
    try:
        # Robot Framework < 7 records local time without a zone, so naive is right.
        return datetime.strptime(str(timestamp), "%Y%m%d %H:%M:%S.%f")  # noqa: DTZ007
    except ValueError:
        return None


def clock_time(timestamp) -> str:
    moment = as_datetime(timestamp)
    return moment.strftime("%H:%M:%S.%f")[:-3] if moment else ""


def iso_time(timestamp) -> str:
    moment = as_datetime(timestamp)
    return moment.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] if moment else str(timestamp or "")


def keyword_title(keyword: Keyword) -> str:
    """Name in bold, assignment in front of it, arguments behind it."""
    title = f"<b>{full_name_of(keyword)}</b>"
    if keyword.assign:
        title = f"{', '.join(keyword.assign)} = {title}"
    if keyword.args:
        title += "&nbsp;&nbsp;" + "&nbsp;&nbsp;".join(str(argument) for argument in keyword.args)
    return title


def structure_title(item) -> str:
    """Title of a keyword, a control structure or a loop iteration."""
    if isinstance(item, Keyword):
        return keyword_title(item)
    if is_iteration(item):
        assignments = ", ".join(f"{name} = {value}" for name, value in item.assign.items())
        return f"<b>{assignments}</b>" if assignments else f"<b>{item.type}</b>"
    text = str(item).strip()
    if not text or "object at 0x" in text:
        text = str(getattr(item, "type", "")) or "STEP"
    return f"<b>{text.replace('    ', '&nbsp;&nbsp;')}</b>"


def timestamp_of(item) -> str:
    return clock_time(getattr(item, "starttime", None))


def duration_of(item) -> str:
    elapsed = getattr(item, "elapsedtime", 0)
    return f"{elapsed / 1000:.3f} s" if elapsed else ""


class KeywordCommentRenderer:
    """Builds the HTML comment of one keyword execution."""

    def __init__(
        self,
        max_depth: int = 5,
        max_rows: int = 300,
        log_level: str = "TRACE",
        rounded_pills: bool = True,
    ) -> None:
        self.max_depth = max_depth
        self.max_rows = max_rows
        self.min_level = LOG_LEVEL_ORDER.get(str(log_level).upper(), DEFAULT_LOG_LEVEL_ORDER)
        self.rounded_pills = rounded_pills

    def render(self, keyword) -> str:
        rows = list(self._rows_for(keyword))
        truncated = len(rows) > self.max_rows > 0
        if truncated:
            rows = rows[: self.max_rows]
            rows.append(("note", "", ["<i>... truncated, see the Robot Framework log</i>", "", ""]))
        table_rows = [self._header_row()]
        table_rows.extend(self._row_html(kind, label, cells) for kind, label, cells in rows)
        return (
            "<pre style='" + MONOSPACE + " font-size: 12px; color: #546e7a;'>"
            f"Start Time:   {iso_time(keyword.starttime)}\n"
            f"End Time:     {iso_time(keyword.endtime)}\n"
            f"Elapsed Time: {timedelta(milliseconds=keyword.elapsedtime)!s}\n"
            "</pre>"
            f"<table {TABLE_ATTRIBUTES} style='{TABLE_STYLE}'>"
            + "".join(table_rows)
            + "</table>"
        )

    def _shows_level(self, level: str) -> bool:
        return LOG_LEVEL_ORDER.get(level, DEFAULT_LOG_LEVEL_ORDER) >= self.min_level

    def _rows_for(self, item, depth: int = 0):
        if is_message(item):
            if self._shows_level(item.level):
                yield self._message_row(item, depth)
            return
        yield self._structure_row(item, depth)
        if depth < self.max_depth:
            # Body order keeps a log line between the sub keywords it happened between.
            for child in getattr(item, "body", []):
                yield from self._rows_for(child, depth + 1)
            return
        # The structure is folded away, its log messages still have to show up.
        for message in self._messages_below(item):
            yield self._message_row(message, depth + 1)
        hidden = self._count_folded(item)
        if hidden:
            plural = "s" if hidden > 1 else ""
            yield (
                "note",
                "",
                [f"{INDENT * (depth + 1)}<i>({hidden} sub keyword{plural} not shown)</i>", "", ""],
            )

    def _count_folded(self, item) -> int:
        """All structure items below, not just the direct children."""
        count = 0
        for child in getattr(item, "body", []):
            if not is_message(child):
                count += 1 + self._count_folded(child)
        return count

    def _messages_below(self, item):
        for child in getattr(item, "body", []):
            if is_message(child):
                if self._shows_level(child.level):
                    yield child
            else:
                yield from self._messages_below(child)

    def _structure_row(self, item, depth: int):
        return (
            "structure",
            str(item.status),
            [f"{INDENT * depth}{structure_title(item)}", duration_of(item), timestamp_of(item)],
        )

    def _message_row(self, message, depth: int):
        text = message.html_message.replace("<hr>", "<br/>").replace("<br>", "<br/>").strip()
        timestamp = clock_time(message.timestamp)
        return ("message", str(message.level), [f"{INDENT * depth}{text}", "", timestamp])

    @staticmethod
    def _header_row() -> str:
        cells = "".join(
            f"<td style='border: 0; border-bottom: 2px solid {GROUP_LINE_COLOR}; "
            f"padding: 4px 8px; color: #607d8b; font-size: 11px; text-align: left; "
            f"{column_style}'><b>{header}</b></td>"
            for header, column_style in zip(HEADERS, COLUMN_STYLE, strict=True)
        )
        return f"<tr>{cells}</tr>"

    def _row_html(self, kind: str, label: str, cells: list[str]) -> str:
        """Keyword status in column one, log level in column two.

        Every row carries 'data-tb-role' and, for messages, 'data-tb-level', so
        that other tools - the TestBench AI service reads the failure message
        out of here - can find a cell without parsing the styling.
        """
        group_line = f"border-top: 1px solid {GROUP_LINE_COLOR}; " if kind == "structure" else ""
        background = f"background-color: {GROUP_BACKGROUND}; " if kind == "structure" else ""
        # 'background-color' on a <td> is ignored by Sferyx, the attribute is not.
        bgcolor = f" bgcolor='{GROUP_BACKGROUND}'" if kind == "structure" else ""
        base = (
            f"border: 0; border-bottom: 1px solid {LINE_COLOR}; padding: 3px 8px; "
            f"vertical-align: top; "
        )
        status = render_pill(label, rounded=self.rounded_pills) if kind == "structure" else ""
        level = render_pill(label, rounded=self.rounded_pills) if kind == "message" else ""
        text = cells[0] if kind == "structure" else f"{MONO_OPEN}{cells[0]}{MONO_CLOSE}"
        values = [status, level, text, *cells[1:]]
        attributes = f" data-tb-role='{kind}'" + (
            f" data-tb-level='{label}'" if kind == "message" else ""
        )
        return (
            f"<tr{attributes}>"
            + "".join(
                f"<td{bgcolor} style='{base}{group_line}{background}{column_style}'"
                f"{cell_attribute}>{value}</td>"
                for value, column_style, cell_attribute in zip(
                    values, COLUMN_STYLE, CELL_ATTRIBUTE, strict=True
                )
            )
            + "</tr>"
        )
