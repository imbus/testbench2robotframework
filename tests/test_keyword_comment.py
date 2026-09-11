"""The keyword comment shows the structure of a Robot user keyword with its logs."""

import re
from datetime import datetime

from robot import version as robot_version
from robot.result import Keyword, Message

from testbench2robotframework.keyword_comment import KeywordCommentRenderer, render_pill

# Robot Framework 7 renamed the keyword name attributes and switched timestamps
# from strings to datetime. The package supports 6 and 7, so do these fixtures.
ROBOT_7 = int(robot_version.VERSION.split(".")[0]) >= 7
TIME = datetime(2026, 7, 24, 10, 0, 0) if ROBOT_7 else "20260724 10:00:00.000"


def make_keyword(name, *, owner=None, args=(), status="PASS", assign=()):
    if ROBOT_7:
        keyword = Keyword(name=name, owner=owner, args=args, assign=assign, status=status)
        keyword.start_time = TIME
        keyword.end_time = TIME
    else:
        keyword = Keyword(kwname=name, libname=owner, args=args, assign=assign, status=status)
        keyword.starttime = TIME
        keyword.endtime = TIME
    return keyword


def log(keyword, message, level="INFO"):
    keyword.body.append(Message(message=message, level=level, timestamp=TIME))
    return keyword


def cells_of(html):
    """[(status, level, text), ...] of the rendered table, without the header."""
    rows = []
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S)[1:]:
        values = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)
        rows.append(
            tuple(re.sub("<.*?>", "", value).replace("&nbsp;", " ").strip() for value in values)
        )
    return rows


def user_keyword_with_sub_keywords():
    """A user keyword with an own log message and two sub keywords."""
    root = make_keyword("Login As Admin User", args=("admin",))
    log(root, "Starting login")
    step = make_keyword("Open Login Page")
    log(step, "Navigating")
    root.body.append(step)
    failing = make_keyword("Should Be Equal", owner="BuiltIn", args=("a", "b"), status="FAIL")
    log(failing, "a != b", level="FAIL")
    root.body.append(failing)
    return root


def test_keyword_row_shows_name_arguments_and_duration():
    keyword = make_keyword("Login As Admin User", args=("admin", "secret"))

    rows = cells_of(KeywordCommentRenderer().render(keyword))

    status, level, text = rows[0][0], rows[0][1], rows[0][2]
    assert status == "PASS"
    assert level == ""
    assert "Login As Admin User" in text
    assert "admin" in text and "secret" in text


def test_log_messages_are_rows_of_their_own_in_the_second_column():
    keyword = log(make_keyword("Do Something"), "hello world")

    rows = cells_of(KeywordCommentRenderer().render(keyword))

    assert rows[0][0] == "PASS"
    assert rows[1] [0] == ""  # the keyword status column stays empty for a message
    assert rows[1][1] == "INFO"
    assert "hello world" in rows[1][2]


def test_keyword_with_sub_keywords_keeps_its_own_messages_in_body_order():
    rows = cells_of(KeywordCommentRenderer().render(user_keyword_with_sub_keywords()))
    labels = [(status or level, text.strip()) for status, level, text, *_ in rows]

    assert labels == [
        ("PASS", "Login As Admin User  admin"),
        ("INFO", "Starting login"),
        ("PASS", "Open Login Page"),
        ("INFO", "Navigating"),
        ("FAIL", "BuiltIn.Should Be Equal  a  b"),
        ("FAIL", "a != b"),
    ]


def indents_of(html):
    """Leading spaces of the text column, before any stripping."""
    indents = []
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S)[1:]:
        text = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)[2]
        plain = re.sub("<.*?>", "", text).replace("&nbsp;", " ")
        indents.append(len(plain) - len(plain.lstrip()))
    return indents


def test_sub_keywords_are_indented_deeper_than_their_parent():
    indent_of = indents_of(KeywordCommentRenderer().render(user_keyword_with_sub_keywords()))

    assert indent_of[0] == 0  # root keyword
    assert indent_of[1] > indent_of[0]  # its own message
    assert indent_of[3] > indent_of[2]  # message of the sub keyword


def test_structure_is_folded_but_log_messages_survive():
    rows = cells_of(KeywordCommentRenderer(max_depth=0).render(user_keyword_with_sub_keywords()))
    texts = [text.strip() for _, _, text, *_ in rows]

    assert "Open Login Page" not in texts  # structure folded away
    assert "Starting login" in texts  # messages are kept
    assert "Navigating" in texts
    assert "a != b" in texts
    assert any("2 sub keywords not shown" in text for text in texts)


def test_log_level_filter_is_a_threshold_like_robots():
    keyword = make_keyword("Do Something")
    log(keyword, "chattiest", level="TRACE")
    log(keyword, "chatty", level="DEBUG")
    log(keyword, "relevant", level="INFO")
    log(keyword, "warning", level="WARN")

    default = cells_of(KeywordCommentRenderer().render(keyword))
    debug = cells_of(KeywordCommentRenderer(log_level="DEBUG").render(keyword))
    warn = cells_of(KeywordCommentRenderer(log_level="WARN").render(keyword))

    # the default filters nothing
    assert [row[1] for row in default] == ["", "TRACE", "DEBUG", "INFO", "WARN"]
    # DEBUG passes everything except TRACE, WARN only WARN and graver
    assert [row[1] for row in debug] == ["", "DEBUG", "INFO", "WARN"]
    assert [row[1] for row in warn] == ["", "WARN"]


def test_log_level_accepts_the_configuration_enum():
    from testbench2robotframework.config import RobotLogLevel

    keyword = make_keyword("Do Something")
    log(keyword, "chatty", level="DEBUG")

    rendered = cells_of(KeywordCommentRenderer(log_level=RobotLogLevel.INFO).render(keyword))

    assert [row[1] for row in rendered] == [""]


def test_too_many_rows_are_truncated_visibly():
    keyword = make_keyword("Noisy Keyword")
    for index in range(20):
        log(keyword, f"message {index}")

    html = KeywordCommentRenderer(max_rows=5).render(keyword)

    assert "truncated" in html
    assert len(cells_of(html)) == 6  # 5 rows plus the note


def test_pills_degrade_to_rectangles_without_border_radius():
    assert "border-radius" in render_pill("PASS")
    assert "border-radius" not in render_pill("PASS", rounded=False)
    assert "<b>" not in render_pill("")


def test_markup_stays_compatible_with_word_and_pdf():
    """No construct that Word or a PDF converter is known to break on."""
    html = KeywordCommentRenderer().render(user_keyword_with_sub_keywords())

    for forbidden in ("rowspan", "colspan", "<details", "<script", "class=", "id=", "flex", "grid"):
        assert forbidden not in html
    assert html.count("<table") == 1  # no nested tables


def cell_styles_of(html, row_index=1):
    """Inline styles of the cells of one row (0 = header)."""
    row = re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S)[row_index]
    return re.findall(r"<td[^>]*style='([^']*)'", row)


def test_narrow_columns_never_wrap():
    """In a container too narrow to scroll the browser would break 'Duration'
    into 'Dur atio n' and a timestamp into three lines."""
    html = KeywordCommentRenderer().render(user_keyword_with_sub_keywords())

    for row_index in (0, 1):  # header and first keyword row
        _, _, _, duration, time = cell_styles_of(html, row_index)

        assert "white-space: nowrap" in duration
        assert "white-space: nowrap" in time
        assert "min-width" in duration
        assert "min-width" in time


def test_message_column_takes_the_rest_and_breaks_long_words():
    """A keyword argument can be a path without a single space in it."""
    html = KeywordCommentRenderer().render(user_keyword_with_sub_keywords())
    _, _, step, _, _ = cell_styles_of(html)

    assert "width: 100%" in step
    assert "overflow-wrap: anywhere" in step
    assert "word-wrap: break-word" in step  # legacy alias for old renderers
    assert "nowrap" not in step
