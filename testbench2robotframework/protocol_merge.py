from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum

from .model import (
    ActivityStatus,
    ExecStatus,
    TestCaseExecutionForImport,
    TestCaseSetExecutionForImport,
    VerdictStatus,
)


class Verdict(Enum):
    """The single status a test element is displayed with.

    Mirrors 'Verdict' of the TestBench web clients
    (libs/report-model/src/lib/enumerations/verdict.enum.ts), which is what
    iTORX shows in the test theme tree.
    """

    Skipped = "Skipped"
    Pass = "Pass"
    ToVerify = "ToVerify"
    Undefined = "Undefined"
    Fail = "Fail"
    Blocked = "Blocked"


# Ascending priority, taken verbatim from Verdict.verdictValues() of the web
# clients: a parent takes the verdict of its highest ranked child. Blocked wins
# over Fail, Fail wins over Undefined, and Skipped never outranks anything.
VERDICT_PRIORITY: tuple[Verdict, ...] = (
    Verdict.Skipped,
    Verdict.Pass,
    Verdict.ToVerify,
    Verdict.Undefined,
    Verdict.Fail,
    Verdict.Blocked,
)


@dataclass(frozen=True)
class ExecutionState:
    """The three execution dimensions of a test element, kept consistent."""

    status: ActivityStatus
    exec_status: ExecStatus
    verdict: VerdictStatus

    @property
    def display_verdict(self) -> Verdict:
        """Combines the three dimensions into one verdict.

        Port of computeVerdictFromStatuses() in the web clients
        (libs/report/src/lib/acl/helpers.acl.ts). Note that 'Blocked' requires
        all three dimensions to agree - a canceled element that is not blocked
        counts as Undefined.
        """
        if self.verdict is VerdictStatus.Pass:
            return Verdict.Pass
        if self.verdict is VerdictStatus.Fail:
            return Verdict.Fail
        if self.verdict is VerdictStatus.ToVerify:
            return Verdict.ToVerify
        if self.verdict is VerdictStatus.Undefined and self.status is ActivityStatus.Skipped:
            return Verdict.Skipped
        if (
            self.verdict is VerdictStatus.Undefined
            and self.status is ActivityStatus.Canceled
            and self.exec_status is ExecStatus.Blocked
        ):
            return Verdict.Blocked
        return Verdict.Undefined


# Port of updateExecutionFromVerdict() in the web clients: the canonical triple
# a test element carries for each verdict.
EXECUTION_STATE_BY_VERDICT: dict[Verdict, ExecutionState] = {
    Verdict.Pass: ExecutionState(
        ActivityStatus.Performed, ExecStatus.NotBlocked, VerdictStatus.Pass
    ),
    Verdict.Fail: ExecutionState(
        ActivityStatus.Performed, ExecStatus.NotBlocked, VerdictStatus.Fail
    ),
    Verdict.ToVerify: ExecutionState(
        ActivityStatus.Performed, ExecStatus.NotBlocked, VerdictStatus.ToVerify
    ),
    Verdict.Skipped: ExecutionState(
        ActivityStatus.Skipped, ExecStatus.NotBlocked, VerdictStatus.Undefined
    ),
    Verdict.Blocked: ExecutionState(
        ActivityStatus.Canceled, ExecStatus.Blocked, VerdictStatus.Undefined
    ),
    Verdict.Undefined: ExecutionState(
        ActivityStatus.Planned, ExecStatus.NotBlocked, VerdictStatus.Undefined
    ),
}


def execution_state_of(execution) -> ExecutionState | None:
    """Reads an ExecutionState from anything carrying the three dimensions."""
    if execution is None:
        return None
    return ExecutionState(
        status=execution.status, exec_status=execution.execStatus, verdict=execution.verdict
    )


def display_verdict_of(execution) -> Verdict | None:
    state = execution_state_of(execution)
    return state.display_verdict if state else None


def aggregate_verdicts(verdicts: Iterable[Verdict | None]) -> Verdict | None:
    """The verdict a parent inherits from its children: the highest ranked one.

    Returns None when no child carries execution data, so callers can leave the
    parent untouched.
    """
    known_verdicts = [verdict for verdict in verdicts if verdict is not None]
    if not known_verdicts:
        return None
    return max(known_verdicts, key=VERDICT_PRIORITY.index)


def execution_state_for(verdict: Verdict) -> ExecutionState:
    return EXECUTION_STATE_BY_VERDICT[verdict]


def merge_test_case_executions(
    existing: list[TestCaseExecutionForImport],
    new: list[TestCaseExecutionForImport],
) -> list[TestCaseExecutionForImport]:
    """Merges the test case executions of a single test case set.

    Executions are identified by their uniqueID. Executions of the current Robot
    Framework run replace pre-existing ones in place, pre-existing executions the
    run did not cover are kept and executions new to this run are appended.
    """
    new_by_unique_id = {test_case.uniqueID: test_case for test_case in new}
    merged: list[TestCaseExecutionForImport] = []
    merged_unique_ids: set[str] = set()
    for test_case in existing:
        if test_case.uniqueID in merged_unique_ids:
            continue
        merged_unique_ids.add(test_case.uniqueID)
        merged.append(new_by_unique_id.get(test_case.uniqueID, test_case))
    for test_case in new:
        if test_case.uniqueID in merged_unique_ids:
            continue
        merged_unique_ids.add(test_case.uniqueID)
        merged.append(test_case)
    return merged


def verdict_of_test_case_executions(
    test_cases: Iterable[TestCaseExecutionForImport],
) -> Verdict | None:
    """The verdict a test case set inherits from its (merged) test case executions."""
    return aggregate_verdicts([display_verdict_of(test_case.result) for test_case in test_cases])


def index_by_test_case_set_key(
    protocol: Iterable[TestCaseSetExecutionForImport],
) -> dict[str, TestCaseSetExecutionForImport]:
    return {entry.testCaseSetKey: entry for entry in protocol}
