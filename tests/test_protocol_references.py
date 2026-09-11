"""Attachments referenced from a test message end up in the main protocol.

TestBench imports the execution from 'protocol.json'. A reference that is only
written to the test case file is therefore never shown in TestBench.
"""

from robot.result import TestCase

from testbench2robotframework.config import AttachmentConflictBehaviour, ReferenceBehaviour
from testbench2robotframework.execution_artifacts import ExecutionArtifactStorage
from testbench2robotframework.model import (
    ActivityStatus,
    ExecStatus,
    ExecutionResultForImport,
    TestCaseDetails,
    TestCaseExecutionDetails,
    TestCaseExecutionForImport,
    UserReference,
    VerdictStatus,
)
from testbench2robotframework.result_writer import ResultWriter


def make_itb_test_case():
    return TestCaseDetails(
        uniqueID="itb-TC-0815-PC-4711",
        spec=None,
        testSequence=[],
        parameters=[],
        keywords=[],
        exec=TestCaseExecutionDetails(
            key="3001",
            status=ActivityStatus.Performed,
            execStatus=ExecStatus.NotBlocked,
            verdict=VerdictStatus.Pass,
            plannedDuration=0,
            actualDuration=0,
            currentUser=UserReference(key="-1", name=""),
            comments="",
            defects=[],
            udfs=[],
            tags=[],
            references=[],
        ),
    )


def make_protocol_test_case():
    return TestCaseExecutionForImport(
        uniqueID="itb-TC-0815-PC-4711",
        testCaseExecutionKey="3001",
        result=ExecutionResultForImport(
            status=ActivityStatus.Performed,
            execStatus=ExecStatus.NotBlocked,
            verdict=VerdictStatus.Pass,
            timestamp="2026-07-23 10:00:00",
        ),
        durationMillis=42,
    )


def make_result_writer(tmp_path):
    (tmp_path / "output.xml").write_text("<robot/>")
    (tmp_path / "prozess_1.zip").write_bytes(b"zip")
    writer = ResultWriter.__new__(ResultWriter)  # bypasses the file system heavy __init__
    writer.artifact_storage = ExecutionArtifactStorage(
        ReferenceBehaviour.ATTACHMENT,
        AttachmentConflictBehaviour.USE_EXISTING,
        [],
        str(tmp_path / "output.xml"),
        str(tmp_path / "attachments"),
    )
    writer.protocol_test_case = make_protocol_test_case()
    return writer


def test_reference_is_written_to_test_case_file_and_protocol(tmp_path):
    writer = make_result_writer(tmp_path)
    itb_test_case = make_itb_test_case()
    test = TestCase(name="itb-TC-0815-PC-4711", message="done\n\nitb-reference: prozess_1.zip")

    writer._set_itb_testcase_references(itb_test_case, [test])

    assert itb_test_case.exec.references == ["-4"]
    assert writer.protocol_test_case.references == ["-4"]


def test_same_reference_from_two_phases_is_listed_once(tmp_path):
    writer = make_result_writer(tmp_path)
    itb_test_case = make_itb_test_case()
    phases = [
        TestCase(name="itb-TC-0815-PC-4711 : Phase 1/2", message="itb-reference: prozess_1.zip"),
        TestCase(name="itb-TC-0815-PC-4711 : Phase 2/2", message="itb-reference: prozess_1.zip"),
    ]

    writer._set_itb_testcase_references(itb_test_case, phases)

    assert itb_test_case.exec.references == ["-4"]
    assert writer.protocol_test_case.references == ["-4"]


def test_without_references_protocol_field_stays_unset(tmp_path):
    writer = make_result_writer(tmp_path)
    itb_test_case = make_itb_test_case()

    writer._set_itb_testcase_references(itb_test_case, [TestCase(name="x", message="done")])

    assert itb_test_case.exec.references == []
    assert writer.protocol_test_case.references is None
