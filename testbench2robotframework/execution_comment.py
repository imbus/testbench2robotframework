"""Renders the execution comments of a test case and of a test case set.

Same markup rules as 'keyword_comment': one flat table, no CSS classes for
styling, no rowspan, no nested tables - the comments are exported to PDF and
pasted into Word.

Machine readable anchors
------------------------
Other tools read these comments back. The TestBench AI service inserts defect
explanations into the message cell of a failed test case. Instead of making it
guess from the styling, the markup carries explicit attributes:

    <tr data-tb-test-case="itb-TC-1-PC-2" data-tb-status="FAIL">
        ...
        <td data-tb-role="message"><pre>...</pre></td>

'data-tb-role="message"' marks the cell whose <pre> holds the failure message.
Attributes are invisible to a reader, are ignored by Word and PDF converters,
and survive a restyling of the table - unlike a regular expression over the
formatting.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .keyword_comment import (
    GROUP_LINE_COLOR,
    LINE_COLOR,
    MONO_CLOSE,
    MONO_OPEN,
    MONOSPACE,
    TABLE_ATTRIBUTES,
    render_pill,
)

SANS = "font-family: Segoe UI, Helvetica, Arial, sans-serif;"
LABEL_COLOR = "#607d8b"
BOX_BACKGROUND = "#f7f9fa"
META = f"color: {LABEL_COLOR}; font-size: 12px;"
SET_TABLE_HEADERS = ("Test Case", "Phase", "Status", "Message")
# 'YYYY-MM-DD HH:MM:SS.mmm' - what tb2rf writes as the message of a passing test.
TIMESTAMP_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+")


def message_box(message: str) -> str:
    """The failure message, wrapping and set off from the rest.

    A <div> with 'border-left' and a background renders in the Sferyx editor of
    the Java client as well, and <pre> is monospace there by default.
    """
    return (
        f"<div style='border-left: 3px solid {GROUP_LINE_COLOR}; "
        f"background-color: {BOX_BACKGROUND}; padding: 6px 10px;'>"
        f"<pre style='{MONOSPACE} font-size: 12px; margin: 0; white-space: pre-wrap; "
        f"overflow-wrap: anywhere;'>{message}</pre></div>"
    )


@dataclass
class PhaseExecution:
    """One executed phase of a test case - a test case that was not split has one."""

    status: str
    start: str
    end: str
    elapsed: str
    message: str
    phase: str = ""


def render_test_case_comment(execution: PhaseExecution) -> str:
    """Status pill, meta line and - unless the test case passed - the message.

    A passing test case has nothing to report beyond its status and timing, so
    the message block is left out. A message that a passing test case set itself
    (Robot's 'Set Test Message') is kept, though.
    """
    phase_note = (
        f"Phase {execution.phase}&nbsp;&nbsp;&middot;&nbsp;&nbsp;" if execution.phase else ""
    )
    message = execution.message.strip()
    show_message = bool(message) and (execution.status != "PASS" or not _is_timestamp(message))
    return (
        f"<div style='{SANS} font-size: 12px; margin-bottom: 10px;' "
        f"data-tb-role='test-case-execution' data-tb-status='{execution.status}'>"
        f"<div style='padding-bottom: {8 if show_message else 0}px;'>"
        f"{render_pill(execution.status)}"
        f"&nbsp;&nbsp;<span style='{META}'>{phase_note}{execution.start}"
        f"&nbsp;&nbsp;&rarr;&nbsp;&nbsp;{execution.end}&nbsp;&nbsp;&middot;&nbsp;&nbsp;"
        f"{execution.elapsed}</span></div>"
        f"{message_box(message) if show_message else ''}</div>"
    )


def _is_timestamp(message: str) -> bool:
    """Whether the message is just the end time tb2rf writes for a passing test."""
    return bool(TIMESTAMP_PATTERN.fullmatch(message))


@dataclass
class TestCaseRow:
    """One row of the test case set comment table."""

    unique_id: str
    name: str
    phase: str
    status: str
    message: str


def render_test_case_set_table(rows: list[TestCaseRow], start: str, end: str) -> str:
    """The comment table of a test case set.

    The phase column only exists when at least one test case of the set was
    split into phases - otherwise it would be an empty column in every row.
    """
    with_phase = any(row.phase for row in rows)
    headers = [header for header in SET_TABLE_HEADERS if with_phase or header != "Phase"]
    widths = ["white-space: nowrap; "] * (2 + with_phase) + ["width: 100%; "]
    header_cells = "".join(
        f"<td style='color: {LABEL_COLOR}; font-size: 11px; border: 0; "
        f"border-bottom: 2px solid {GROUP_LINE_COLOR}; padding: 5px 10px; text-align: left; "
        f"{width}'><b>{header}</b></td>"
        for header, width in zip(headers, widths, strict=True)
    )
    base = (
        f"border: 0; border-bottom: 1px solid {LINE_COLOR}; padding: 5px 10px; "
        f"vertical-align: top; "
    )
    body = []
    for row in rows:
        cells = [
            f"<td style='{base}{MONOSPACE} font-size: 12px; white-space: nowrap;'>"
            f"{MONO_OPEN}<b>{row.name}</b>{MONO_CLOSE}</td>"
        ]
        if with_phase:
            cells.append(f"<td style='{base}{META} white-space: nowrap;'>{row.phase}</td>")
        cells.append(f"<td style='{base}white-space: nowrap;'>{render_pill(row.status)}</td>")
        cells.append(
            f"<td style='{base}width: 100%;' data-tb-role='message'>"
            f"<pre style='{MONOSPACE} font-size: 12px; margin: 0; white-space: pre-wrap; "
            f"overflow-wrap: anywhere;'>{row.message}</pre></td>"
        )
        body.append(
            f"<tr data-tb-test-case='{row.unique_id}' data-tb-status='{row.status}'>"
            + "".join(cells)
            + "</tr>"
        )
    return (
        f"<div style='{SANS} font-size: 12px;' data-tb-role='test-case-set-execution'>"
        f"<pre style='{MONOSPACE} font-size: 12px; color: {LABEL_COLOR}; margin: 0 0 8px;'>"
        f"Start Time:   {start}\nEnd Time:     {end}</pre>"
        f"<table {TABLE_ATTRIBUTES} style='border-collapse: collapse; width: 100%; border: 0;'>"
        f"<tr>{header_cells}</tr>" + "".join(body) + "</table></div>"
    )
