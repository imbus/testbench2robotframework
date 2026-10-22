"""Rows of the test case set comment table."""

from testbench2robotframework.execution_comment import (
    PhaseExecution,
    TestCaseRow,
    render_test_case_comment,
    render_test_case_set_table,
)


def rows(*entries):
    return render_test_case_set_table(list(entries), start="10:00:00", end="10:00:01")


def test_phase_column_is_dropped_when_no_test_case_has_phases():
    html = rows(
        TestCaseRow("itb-TC-1-PC-1", "itb-TC-1-PC-1", "", "PASS", "ok"),
        TestCaseRow("itb-TC-1-PC-2", "itb-TC-1-PC-2", "", "FAIL", "boom"),
    )

    assert "Phase" not in html
    assert html.count("<td") == 3 + 2 * 3  # header plus two rows of three cells


def test_phase_column_is_kept_when_a_test_case_was_split():
    html = rows(
        TestCaseRow("itb-TC-1-PC-1", "itb-TC-1-PC-1", "Phase 1/2", "PASS", "ok"),
        TestCaseRow("itb-TC-1-PC-1", "", "Phase 2/2", "FAIL", "boom"),
    )

    assert ">Phase</b>" in html
    assert "Phase 1/2" in html
    assert html.count("<td") == 4 + 2 * 4


def test_rows_carry_machine_readable_anchors():
    """Other tools must find the message cell without parsing the styling."""
    html = rows(TestCaseRow("itb-TC-1-PC-2", "itb-TC-1-PC-2", "", "FAIL", "boom"))

    assert "data-tb-test-case='itb-TC-1-PC-2'" in html
    assert "data-tb-status='FAIL'" in html
    assert "data-tb-role='message'" in html


def test_test_case_comment_starts_with_a_status_pill():
    html = render_test_case_comment(
        PhaseExecution(
            status="FAIL",
            start="10:00:00.000",
            end="10:00:01.280",
            elapsed="0:00:01.280",
            message="boom",
        )
    )

    assert html.index("FAIL") < html.index("10:00:00.000")  # pill comes first
    assert "border-radius" in html
    assert "boom" in html
    assert "Phase" not in html


def test_test_case_comment_shows_the_phase_when_there_is_one():
    html = render_test_case_comment(
        PhaseExecution(
            status="PASS",
            start="10:00:00.000",
            end="10:00:01.280",
            elapsed="0:00:01.280",
            message="ok",
            phase="2/2",
        )
    )

    assert "Phase 2/2" in html
