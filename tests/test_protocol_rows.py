"""Rows of the test case set comment table."""

from testbench2robotframework.execution_comment import (
    PhaseExecution,
    TestCaseRow,
    render_test_case_comment,
    render_test_case_set_table,
)
from testbench2robotframework.model import (
    ActivityStatus,
    ExecStatus,
    ExecutionResultForImport,
    RichTextForImport,
    TestCaseExecutionForImport,
    VerdictStatus,
)
from testbench2robotframework.result_writer import preserved_table_row, unexecuted_table_row


def make_preserved(
    verdict,
    comments=None,
    timestamp="2026-07-23 10:00:00",
    status=ActivityStatus.Performed,
    exec_status=ExecStatus.NotBlocked,
):
    return TestCaseExecutionForImport(
        uniqueID="itb-TC-0815-PC-4711",
        testCaseExecutionKey="3001",
        result=ExecutionResultForImport(
            status=status,
            execStatus=exec_status,
            verdict=verdict,
            timestamp=timestamp,
        ),
        durationMillis=42,
        comments=RichTextForImport(html=comments) if comments else None,
    )


def rows(*entries):
    return render_test_case_set_table(list(entries), start="10:00:00", end="10:00:01")


def test_preserved_row_uses_stored_verdict_and_comment():
    row = preserved_table_row(make_preserved(VerdictStatus.Fail, "<b>old failure</b>"))

    assert row.unique_id == "itb-TC-0815-PC-4711"
    assert row.status == "FAIL"
    assert row.message == "<b>old failure</b>"


def test_preserved_row_falls_back_to_timestamp():
    row = preserved_table_row(make_preserved(VerdictStatus.Pass))

    assert row.status == "PASS"
    assert row.message == "2026-07-23 10:00:00"


def test_blocked_execution_is_reported_as_blocked():
    """Canceled + blocked + undefined is what iTORX displays as 'Blocked'."""
    row = preserved_table_row(
        make_preserved(
            VerdictStatus.Undefined,
            status=ActivityStatus.Canceled,
            exec_status=ExecStatus.Blocked,
        )
    )

    assert row.status == "BLOCKED"


def test_row_without_any_execution_is_undefined():
    assert unexecuted_table_row("itb-TC-0815-PC-4711", None).status == "UNDEFINED"


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
