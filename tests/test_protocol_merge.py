from testbench2robotframework.model import (
    ActivityStatus,
    ExecStatus,
    ExecutionResultForImport,
    TestCaseExecutionForImport,
    TestCaseSetExecutionForImport,
    VerdictStatus,
)
from testbench2robotframework.protocol_merge import (
    ExecutionState,
    Verdict,
    aggregate_verdicts,
    execution_state_for,
    index_by_test_case_set_key,
    merge_test_case_executions,
    verdict_of_test_case_executions,
)


def make_test_case(
    unique_id: str,
    verdict: VerdictStatus,
    duration: int = 1,
    status: ActivityStatus = ActivityStatus.Performed,
    exec_status: ExecStatus = ExecStatus.NotBlocked,
):
    return TestCaseExecutionForImport(
        uniqueID=unique_id,
        testCaseExecutionKey="3001",
        result=ExecutionResultForImport(
            status=status,
            execStatus=exec_status,
            verdict=verdict,
        ),
        durationMillis=duration,
    )


def state(
    verdict: VerdictStatus,
    status: ActivityStatus = ActivityStatus.Performed,
    exec_status: ExecStatus = ExecStatus.NotBlocked,
):
    return ExecutionState(status=status, exec_status=exec_status, verdict=verdict)


PASSED = state(VerdictStatus.Pass)
FAILED = state(VerdictStatus.Fail)
UNDEFINED = state(VerdictStatus.Undefined, status=ActivityStatus.Planned)
BLOCKED = state(
    VerdictStatus.Undefined, status=ActivityStatus.Canceled, exec_status=ExecStatus.Blocked
)
SKIPPED = state(VerdictStatus.Undefined, status=ActivityStatus.Skipped)
TO_VERIFY = state(VerdictStatus.ToVerify)


def test_new_test_case_is_appended_to_existing_one():
    existing = [make_test_case("itb-TC-0815-PC-4711", VerdictStatus.Pass)]
    new = [make_test_case("itb-TC-0815-PC-4712", VerdictStatus.Fail)]

    merged = merge_test_case_executions(existing, new)

    assert [test_case.uniqueID for test_case in merged] == [
        "itb-TC-0815-PC-4711",
        "itb-TC-0815-PC-4712",
    ]


def test_robot_result_replaces_existing_test_case_in_place():
    existing = [
        make_test_case("itb-TC-0815-PC-4711", VerdictStatus.Pass, duration=1),
        make_test_case("itb-TC-0815-PC-4712", VerdictStatus.Pass, duration=1),
    ]
    new = [make_test_case("itb-TC-0815-PC-4711", VerdictStatus.Fail, duration=99)]

    merged = merge_test_case_executions(existing, new)

    assert [test_case.uniqueID for test_case in merged] == [
        "itb-TC-0815-PC-4711",
        "itb-TC-0815-PC-4712",
    ]
    assert merged[0].result.verdict is VerdictStatus.Fail
    assert merged[0].durationMillis == 99


def test_merge_without_existing_entries_returns_new_entries():
    new = [make_test_case("itb-TC-0815-PC-4711", VerdictStatus.Pass)]

    assert merge_test_case_executions([], new) == new


def test_display_verdict_matches_computeVerdictFromStatuses():
    """Port of computeVerdictFromStatuses() in libs/report/src/lib/acl/helpers.acl.ts."""
    assert PASSED.display_verdict is Verdict.Pass
    assert FAILED.display_verdict is Verdict.Fail
    assert TO_VERIFY.display_verdict is Verdict.ToVerify
    assert SKIPPED.display_verdict is Verdict.Skipped
    assert BLOCKED.display_verdict is Verdict.Blocked
    assert UNDEFINED.display_verdict is Verdict.Undefined


def test_blocked_needs_all_three_dimensions():
    """Canceled alone or blocked alone is Undefined, only both together are Blocked."""
    canceled_only = state(VerdictStatus.Undefined, status=ActivityStatus.Canceled)
    blocked_only = state(
        VerdictStatus.Undefined, status=ActivityStatus.Planned, exec_status=ExecStatus.Blocked
    )

    assert canceled_only.display_verdict is Verdict.Undefined
    assert blocked_only.display_verdict is Verdict.Undefined
    # An element with a verdict keeps it, even when canceled or blocked.
    assert state(VerdictStatus.Pass, status=ActivityStatus.Canceled).display_verdict is Verdict.Pass


def test_aggregation_returns_none_without_children():
    assert aggregate_verdicts([]) is None
    assert aggregate_verdicts([None, None]) is None


def test_parent_takes_the_highest_ranked_child():
    """Priority of Verdict.verdictValues(): Skipped < Pass < ToVerify < Undefined < Fail < Blocked."""
    assert aggregate_verdicts([Verdict.Pass, Verdict.Pass]) is Verdict.Pass
    assert aggregate_verdicts([Verdict.Pass, Verdict.Fail]) is Verdict.Fail
    assert aggregate_verdicts([Verdict.Pass, None]) is Verdict.Pass
    assert aggregate_verdicts([Verdict.Skipped, Verdict.Pass]) is Verdict.Pass
    assert aggregate_verdicts([Verdict.Pass, Verdict.ToVerify]) is Verdict.ToVerify
    assert aggregate_verdicts([Verdict.ToVerify, Verdict.Undefined]) is Verdict.Undefined
    # Fail outranks Undefined, Blocked outranks everything.
    assert aggregate_verdicts([Verdict.Undefined, Verdict.Fail]) is Verdict.Fail
    assert aggregate_verdicts([Verdict.Fail, Verdict.Blocked]) is Verdict.Blocked


def test_execution_state_for_verdict_matches_updateExecutionFromVerdict():
    """Port of updateExecutionFromVerdict() in libs/report/src/lib/acl/helpers.acl.ts."""
    assert execution_state_for(Verdict.Pass) == ExecutionState(
        ActivityStatus.Performed, ExecStatus.NotBlocked, VerdictStatus.Pass
    )
    assert execution_state_for(Verdict.Blocked) == ExecutionState(
        ActivityStatus.Canceled, ExecStatus.Blocked, VerdictStatus.Undefined
    )
    assert execution_state_for(Verdict.Skipped) == ExecutionState(
        ActivityStatus.Skipped, ExecStatus.NotBlocked, VerdictStatus.Undefined
    )
    assert execution_state_for(Verdict.Undefined) == ExecutionState(
        ActivityStatus.Planned, ExecStatus.NotBlocked, VerdictStatus.Undefined
    )
    # Every verdict round-trips through its canonical triple.
    for verdict in Verdict:
        assert execution_state_for(verdict).display_verdict is verdict


def test_executed_and_blocked_are_mutually_exclusive():
    """Blocked is never executed, and a verdict always implies an executed element."""
    blocked = execution_state_for(Verdict.Blocked)

    assert blocked.status is not ActivityStatus.Performed
    assert blocked.exec_status is ExecStatus.Blocked
    assert blocked.verdict is VerdictStatus.Undefined

    for verdict in (Verdict.Pass, Verdict.Fail, Verdict.ToVerify):
        state = execution_state_for(verdict)

        assert state.status is ActivityStatus.Performed
        assert state.exec_status is ExecStatus.NotBlocked

    for verdict in (Verdict.Skipped, Verdict.Undefined):
        state = execution_state_for(verdict)

        assert state.status is not ActivityStatus.Performed
        assert state.verdict is VerdictStatus.Undefined


def test_verdict_of_test_case_executions_uses_merged_children():
    test_cases = [
        make_test_case("itb-TC-0815-PC-4711", VerdictStatus.Pass),
        make_test_case("itb-TC-0815-PC-4712", VerdictStatus.Fail),
    ]

    assert verdict_of_test_case_executions(test_cases) is Verdict.Fail

    blocked_child = make_test_case(
        "itb-TC-0815-PC-4713",
        VerdictStatus.Undefined,
        status=ActivityStatus.Canceled,
        exec_status=ExecStatus.Blocked,
    )

    assert verdict_of_test_case_executions([*test_cases, blocked_child]) is Verdict.Blocked


def test_index_by_test_case_set_key():
    entry = TestCaseSetExecutionForImport(
        testCaseSetKey="1001", executionKey="2001", durationMillis=1, testCases=[]
    )

    assert index_by_test_case_set_key([entry]) == {"1001": entry}
