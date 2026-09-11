import html
import os
import re
import shutil
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from shutil import copytree

from robot.result import Keyword, ResultVisitor, TestCase, TestSuite

from testbench2robotframework.model_utils import from_dict

from .config import Configuration, KeywordCommentStyle
from .execution_artifacts import ExecutionArtifactStorage
from .execution_comment import (
    PhaseExecution,
    TestCaseRow,
    render_test_case_comment,
    render_test_case_set_table,
)
from .json_reader import TestBenchJsonReader
from .json_writer import write_main_protocol, write_references, write_test_structure_element
from .keyword_comment import KeywordCommentRenderer
from .log import logger
from .model import (
    ActivityStatus,
    ExecStatus,
    ExecutionResultForImport,
    KeywordCall,
    KeywordCallExecution,
    KeywordType,
    KeywordVerdict,
    RichTextForImport,
    SequencePhase,
    TestCaseDetails,
    TestCaseExecutionForImport,
    TestCaseNode,
    TestCaseSetExecutionForImport,
    TestCaseSetNode,
    UserReference,
    VerdictStatus,
)
from .protocol_merge import (
    ExecutionState,
    Verdict,
    aggregate_verdicts,
    display_verdict_of,
    execution_state_for,
    index_by_test_case_set_key,
    merge_test_case_executions,
)
from .utils import directory_to_zip, get_directory

try:
    from robot.result import Group
except ImportError:
    Group = None


def _empty_keyword_call_execution() -> KeywordCallExecution:
    return KeywordCallExecution(
        verdict=KeywordVerdict.Undefined,
        duration=0,
        currentUser=UserReference(key="-1", name=""),
        comments="",
        references=[],
        defects=[],
    )


class StatusColor(Enum):
    """A background/foreground pair for one status."""

    def __init__(self, background: str, foreground: str) -> None:
        self.background = background
        self.foreground = foreground

    @property
    def style(self) -> str:
        return f"style='background-color: {self.background}; color: {self.foreground};'"


class TestBenchColor(StatusColor):
    """Verdict colours of the TestBench web clients.

    Used wherever the result is read inside TestBench: the comment table of a
    test case set and the comment of a test case.
    """

    PASS = ("#04AF91", "#fff")
    FAIL = ("#ce3e01", "#fff")
    SKIPPED = ("#263238", "#fff")
    TO_VERIFY = ("#ec901f", "#fff")
    UNDEFINED = ("#98abb5", "#fff")
    BLOCKED = ("#6a3030", "#fff")
    NEUTRAL = ("#fff", "#000")


class RobotLogColor(StatusColor):
    """Label colours of Robot Framework's log.html.

    Taken from 'robot/htmldata/rebot/common.css': --pass-color, --fail-color and
    --warn-color, with the base '.label' style as the default. Robot renders
    'fail'/'error' and 'skip'/'warn' with the same rule, which is why they share
    an entry here as well. Used for the log messages of a test step, so that
    they look like they do in the Robot Framework log.
    """

    PASS = ("#97bd61", "#000")
    FAIL = ("#ce3e01", "#fff")
    WARN = ("#fed84f", "#000")
    DEFAULT = ("#ddd", "#000")


# Robot Framework and TestBench name the same states differently: a robot test
# is 'SKIP' where a TestBench verdict is 'Skipped', and a log message is 'WARN'
# where a verdict is 'ToVerify'.
TESTBENCH_COLOR_BY_STATUS = {
    "PASS": TestBenchColor.PASS,
    "FAIL": TestBenchColor.FAIL,
    "ERROR": TestBenchColor.FAIL,
    "SKIP": TestBenchColor.SKIPPED,
    "SKIPPED": TestBenchColor.SKIPPED,
    "WARN": TestBenchColor.TO_VERIFY,
    "TO VERIFY": TestBenchColor.TO_VERIFY,
    "UNDEFINED": TestBenchColor.UNDEFINED,
    "BLOCKED": TestBenchColor.BLOCKED,
}

ROBOT_COLOR_BY_LEVEL = {
    "PASS": RobotLogColor.PASS,
    "FAIL": RobotLogColor.FAIL,
    "ERROR": RobotLogColor.FAIL,
    "SKIP": RobotLogColor.WARN,
    "WARN": RobotLogColor.WARN,
}

MEGABYTE = 1000 * 1000
TB_ARTIFACT_REGEX = r"itb-reference:\s*(\S*)"

# Labels and colours of the TestBench web clients, so that the comment table
# reads like the test theme tree in iTORX.
STATUS_BY_VERDICT = {
    Verdict.Pass: "PASS",
    Verdict.Fail: "FAIL",
    Verdict.ToVerify: "TO VERIFY",
    Verdict.Skipped: "SKIPPED",
    Verdict.Undefined: "UNDEFINED",
    Verdict.Blocked: "BLOCKED",
}


def render_status(status: str) -> str:
    """Colours a status for TestBench, no matter whether Robot or TestBench named it."""
    return TESTBENCH_COLOR_BY_STATUS.get(status, TestBenchColor.NEUTRAL).style


def render_log_level(level: str) -> str:
    """Colours a log message of a test step the way the Robot Framework log does."""
    return ROBOT_COLOR_BY_LEVEL.get(level, RobotLogColor.DEFAULT).style


def preserved_table_row(test_case: TestCaseExecutionForImport) -> TestCaseRow:
    """Row for a test case execution the current Robot run did not cover.

    The status is the single verdict iTORX displays, computed from the three
    execution dimensions - a canceled and blocked execution shows as BLOCKED
    instead of the bare 'Undefined' of its verdict field.
    """
    verdict = display_verdict_of(test_case.result)
    message = ""
    if test_case.comments and test_case.comments.html:
        message = test_case.comments.html
    elif test_case.result and test_case.result.timestamp:
        message = test_case.result.timestamp
    return TestCaseRow(
        unique_id=test_case.uniqueID,
        name=test_case.uniqueID,
        phase="",
        status=STATUS_BY_VERDICT[verdict] if verdict else "UNDEFINED",
        message=message,
    )


def unexecuted_table_row(unique_id: str, verdict) -> TestCaseRow:
    """Row for a test case without any execution result.

    Blocked, canceled and not yet executed test cases end up here. They are part
    of the table so that the status of the test case set stays comprehensible.
    """
    return TestCaseRow(
        unique_id=unique_id,
        name=unique_id,
        phase="",
        status=STATUS_BY_VERDICT[verdict] if verdict else "UNDEFINED",
        message="",
    )


class ResultWriter(ResultVisitor):
    def __init__(
        self,
        json_report: str | Path,
        json_result: str | Path | None,
        config: Configuration,
        output_xml,
        listener_uid=None,
    ) -> None:
        self.listener_uid = listener_uid
        self.json_dir = get_directory(str(json_report))
        self.output_xml = output_xml
        self.reference_behaviour = config.referenceBehaviour
        self.attachment_conflict_behaviour = config.attachmentConflictBehaviour
        self.tempdir = tempfile.TemporaryDirectory(dir=os.curdir)
        self._test_setup_passed: bool | None = None
        if json_result is None:
            self.json_result = self.json_dir
            self.json_result_path = self.json_dir
            self.create_zip = bool(Path(json_report).suffix == ".zip")
        else:
            self.create_zip = bool(Path(json_result).suffix == ".zip")
            self.json_result_path = str(Path(json_result).parent / Path(json_result).stem)
            self.json_result = self.tempdir.name
            if self.create_zip:
                copytree(self.json_dir, self.json_result, dirs_exist_ok=True)
        self.json_reader = TestBenchJsonReader(self.json_dir)
        self.merge_protocol = config.merge_protocol
        self.base_protocol: list[TestCaseSetExecutionForImport] = (
            self.json_reader.read_main_protocol() if self.merge_protocol else []
        )
        self.base_protocol_by_key = index_by_test_case_set_key(self.base_protocol)
        self.merged_verdicts: dict[str, Verdict] = {}
        self.keyword_comment_style = config.keyword_comment_style
        self.keyword_comment_renderer = KeywordCommentRenderer(
            max_depth=config.keyword_comment_max_depth,
            max_rows=config.keyword_comment_max_rows,
            log_level=config.keyword_comment_log_level,
        )
        self.attachments_path = Path(self.json_result, "attachments")
        self.artifact_storage = self._create_artifact_storage()
        self.test_suites: dict[str, TestSuite] = {}
        self.keywords: list[Keyword] = []
        self.itb_test_case_catalog: dict[str, TestCaseDetails] = {}
        self.phase_pattern = config.phase_pattern
        self.test_chain: list[TestCase] = []
        self.executed_protocol: list[TestCaseSetExecutionForImport] = []

    def _create_artifact_storage(self):
        return ExecutionArtifactStorage(
            self.reference_behaviour,
            self.attachment_conflict_behaviour,
            self.json_reader.read_references(),
            self.output_xml,
            self.attachments_path.as_posix(),
        )

    def start_suite(self, suite: TestSuite):
        if suite.metadata:
            self.test_suites[suite.metadata["uniqueID"]] = suite
        self.protocol_test_cases: list[TestCaseExecutionForImport] = []

    def _get_keywords_by_type(self, keywords: list[KeywordCall], keyword_type: KeywordType):
        for keyword in keywords:
            if not keyword.spec:
                continue
            if keyword.spec.keywordType == keyword_type:
                yield keyword

    def end_test(self, test: TestCase):
        self._test_setup_passed = None
        test_chain = get_test_chain(test.name, self.phase_pattern)
        if test_chain:
            if test_chain.index == 1:
                self.test_chain = [test]
            else:
                self.test_chain.append(test)
            if test_chain.index != test_chain.length:
                return
        else:
            self.test_chain = [test]

        test_uid = test_chain.name if test_chain else test.name
        itb_test_case = self.json_reader.read_test_case(test_uid)  # TODO What if name != UID
        if not itb_test_case:
            logger.warning(f"No JSON file corresponding to test '{test_uid}' found in report.")
            return
        protocol_test_case = self._new_protocol_test_case(test_uid, itb_test_case)
        if protocol_test_case is None:
            return
        self.protocol_test_case: TestCaseExecutionForImport = protocol_test_case
        try:
            atomic_keywords = list(
                self._get_keywords_by_type(itb_test_case.testSequence, KeywordType.Atomic)
            )
            compound_keywords = list(
                self._get_keywords_by_type(itb_test_case.testSequence, KeywordType.Compound)
            )
            self._set_atomic_keywords_execution_result(atomic_keywords, self.test_chain)
            for keyword in compound_keywords:
                self._set_compound_keyword_execution_verdict(keyword, itb_test_case.testSequence)
            textual_steps = list(
                self._get_keywords_by_type(itb_test_case.testSequence, KeywordType.Textual)
            )
            for step in textual_steps:
                if step.exec is None:
                    step.exec = _empty_keyword_call_execution()
                step.exec.verdict = KeywordVerdict.Skipped
            self._set_itb_testcase_execution_result(itb_test_case, self.test_chain)
            self._set_itb_testcase_execution_comment(itb_test_case, self.test_chain)
            self._set_itb_testcase_references(itb_test_case, self.test_chain)
        except TypeError as e:
            logger.error(
                "Could not find a TestBench test case that corresponds "
                "to the given Robot Framework test case."
            )
            raise e
        self.itb_test_case_catalog[test_uid] = itb_test_case
        self.protocol_test_cases.append(self.protocol_test_case)
        write_test_structure_element(self.json_result, itb_test_case)
        logger.debug(
            f"Successfully wrote the result from test "
            f"{itb_test_case.uniqueID} to TestBench's Json Report."
        )

    @staticmethod
    def _new_protocol_test_case(
        test_uid: str, itb_test_case: TestCaseDetails
    ) -> TestCaseExecutionForImport | None:
        """The protocol entry of a test case, or None when it cannot be imported."""
        if itb_test_case.exec is None:
            logger.warning(
                f"Test case {itb_test_case.uniqueID} was exported without execution data "
                f"and can therefore not be imported."
            )
            return None
        if itb_test_case.exec.key in ["", "-1"]:
            logger.warning(
                f"Test case {itb_test_case.uniqueID} was not exported with execution data "
                f"and can therefore not be imported."
            )
        # 'result' and 'durationMillis' are filled in by the caller; the generated
        # model declares them required although the import accepts them empty.
        return TestCaseExecutionForImport(
            test_uid,
            itb_test_case.exec.key,
            None,  # type: ignore[arg-type]
            None,  # type: ignore[arg-type]
            None,
        )

    def _set_itb_testcase_references(
        self, itb_test_case: TestCaseDetails, test_chain: list[TestCase]
    ):
        if not itb_test_case.exec:
            return
        for test in test_chain:
            reference_values = self._get_itb_reference_values(test.message)
            for reference_value in reference_values:
                reference_key = self.artifact_storage.add_artifact(reference_value)
                if not reference_key:
                    continue
                if reference_key not in itb_test_case.exec.references:
                    itb_test_case.exec.references.append(reference_key)
                if self.protocol_test_case.references is None:
                    self.protocol_test_case.references = []
                if reference_key not in self.protocol_test_case.references:
                    self.protocol_test_case.references.append(reference_key)

    def _get_itb_reference_values(self, test_message: str) -> list[str]:
        return re.findall(f".*{TB_ARTIFACT_REGEX}.*", test_message)

    @staticmethod
    def _create_unique_path(attachement_path: Path) -> Path:
        counter = 1
        attachment_stem = attachement_path.stem
        while attachement_path.exists():
            attachement_path = Path(
                f"{attachement_path.parent}",
                f"{attachment_stem}_{counter}{attachement_path.suffix}",
            )
            counter += 1
        return attachement_path

    def _set_itb_testcase_execution_comment(self, itb_test_case, test_chain: list[TestCase]):
        exec_comments = []
        for test in test_chain:
            message = re.sub(TB_ARTIFACT_REGEX, "", test.message)
            html_message = (
                message[len("*HTML*") :].replace("<hr>", "<br/>").replace("<br>", "<br/>").strip()
                if test.message.startswith("*HTML*")
                else html.escape(message)
            )
            test_chain_obj = get_test_chain(test.name, self.phase_pattern)
            phase = (
                f"{test_chain_obj.index}/{test_chain_obj.length}" if test_chain_obj else ""
            )
            exec_comments.append(
                render_test_case_comment(
                    PhaseExecution(
                        status=test.status,
                        start=self.get_isotime_from_robot_timestamp(test.starttime),
                        end=self.get_isotime_from_robot_timestamp(test.endtime),
                        elapsed=str(timedelta(milliseconds=test.elapsedtime)),
                        message=html_message,
                        phase=phase,
                    )
                )
            )
        itb_test_case.exec.comments = f"{''.join(exec_comments)}"
        self.protocol_test_case.comments = RichTextForImport(html=f"{''.join(exec_comments)}")
        # A naive datetime is local time; astimezone() attaches the local zone.
        end_time = test.end_time.astimezone()
        # Isoformat currently not suported by server
        # self.protocol_test_case.result.timestamp = end_time.isoformat()
        timestamp = self._format_utc_timestamp(end_time)
        self.protocol_test_case.result.timestamp = timestamp
        itb_test_case.exec.time = timestamp
        self.protocol_test_case.durationMillis = test.elapsedtime

    def _set_itb_testcase_execution_result(self, itb_test_case: TestCaseDetails, test_chain):
        has_failed_chain = list(filter(lambda tc: tc.status.upper() == "FAIL", test_chain))
        passed_keywords = all(tc.status.upper() == "PASS" for tc in test_chain)
        elapsed_time = sum([tc.elapsedtime for tc in test_chain])
        if itb_test_case.exec:
            itb_test_case.exec.actualDuration = elapsed_time
        self.protocol_test_case.durationMillis = elapsed_time
        if has_failed_chain:
            protocol_result = self._set_itb_test_case_status(itb_test_case, "fail")
            self.protocol_test_case.result = protocol_result
        elif passed_keywords:
            protocol_result = self._set_itb_test_case_status(itb_test_case, "pass")
            self.protocol_test_case.result = protocol_result
        else:
            protocol_result = self._set_itb_test_case_status(itb_test_case, "undef")
            self.protocol_test_case.result = protocol_result

    def _get_test_phase_body(self, test_phase: TestCase) -> list[Keyword]:
        return self._get_keywords_from_rf_body(test_phase)

    def _get_test_phase_setup(self, test_phase: TestCase) -> list[Keyword]:
        test_phase_setup = []
        if test_phase.has_setup and test_phase.setup:
            test_phase_setup = self._get_keywords_from_rf_body(test_phase.setup)
        return test_phase_setup

    def _get_test_phase_teardown(self, test_phase: TestCase) -> list[Keyword]:
        test_phase_teardown = []
        if test_phase.has_teardown and test_phase.teardown:
            test_phase_teardown = self._get_keywords_from_rf_body(test_phase.teardown)
        return test_phase_teardown

    def _get_keywords_from_rf_body(self, rf_body) -> list[Keyword]:
        keywords = []
        for body_item in rf_body.body:
            if isinstance(body_item, Keyword):
                keywords.append(body_item)
            elif Group and isinstance(body_item, Group):
                keywords.extend(self._get_keywords_from_rf_body(body_item))
        return keywords

    def _set_atomic_keywords_execution_result(
        self, atomic_keywords: list[KeywordCall], test_chain: list[TestCase]
    ):
        self._test_setup_passed = True
        test_chain_setup = [
            keyword
            for test_phase in test_chain
            for keyword in self._get_test_phase_setup(test_phase)
        ]
        test_chain_body = [
            keyword
            for test_phase in test_chain
            for keyword in self._get_test_phase_body(test_phase)
        ]
        test_chain_teardown = [
            keyword
            for test_phase in test_chain
            for keyword in self._get_test_phase_teardown(test_phase)
        ]
        setup_keywords = self._filter_atomic_keywords_by_sequence_phase(
            atomic_keywords, SequencePhase.Setup
        )
        test_step_keywords = self._filter_atomic_keywords_by_sequence_phase(
            atomic_keywords, SequencePhase.TestStep
        )
        teardown_keywords = self._filter_atomic_keywords_by_sequence_phase(
            atomic_keywords, SequencePhase.Teardown
        )
        self._set_keyword_verdicts(setup_keywords, test_chain_setup, SequencePhase.Setup)
        self._set_keyword_verdicts(test_step_keywords, test_chain_body, SequencePhase.TestStep)
        self._set_keyword_verdicts(teardown_keywords, test_chain_teardown, SequencePhase.Teardown)

    def _set_keyword_verdicts(
        self,
        keyword_list: list[KeywordCall],
        test_chain_body: list[Keyword],
        sequence_phase: SequencePhase,
    ):
        for index, tb_keyword in enumerate(keyword_list):
            if tb_keyword.exec is None:
                tb_keyword.exec = _empty_keyword_call_execution()
            if sequence_phase == SequencePhase.TestStep and not self._test_setup_passed:
                tb_keyword.exec.verdict = KeywordVerdict.Skipped
                continue
            if index < len(test_chain_body):
                keyword = test_chain_body[index]
                self._check_matching_keyword_name(keyword, tb_keyword)
                tb_keyword_result = self._get_keyword_exec_from_keyword(keyword)
                tb_keyword.exec.verdict = tb_keyword_result.verdict
                tb_keyword.exec.duration = tb_keyword_result.duration
                tb_keyword.exec.comments = tb_keyword_result.comments
                tb_keyword.exec.time = tb_keyword_result.time
                continue
            if sequence_phase == SequencePhase.Setup and not self._test_setup_passed:
                tb_keyword.exec.verdict = KeywordVerdict.Skipped
                continue
            tb_keyword.exec.verdict = KeywordVerdict.Undefined

    def _filter_atomic_keywords_by_sequence_phase(
        self,
        atomic_keywords: list[KeywordCall],
        sequence_phase: SequencePhase,
    ):
        return list(
            filter(
                lambda atomic_keyword: atomic_keyword.spec.sequencePhase == sequence_phase,
                atomic_keywords,
            )
        )

    def _get_keyword_exec_from_keyword(self, keyword: Keyword) -> KeywordCallExecution:
        end_time = keyword.end_time.astimezone()

        return from_dict(
            KeywordCallExecution,
            {
                "verdict": self._get_keyword_result(keyword.status),
                "time": self._format_utc_timestamp(end_time),
                "duration": keyword.elapsedtime,
                "comments": self.get_html_keyword_comment(keyword),
                "currentUser": None,
                "references": [],
                "defects": [],
            },
        )

    def _check_matching_keyword_name(self, rf_keyword: Keyword, tb_keyword: KeywordCall) -> None:
        if not is_normalized_equal(
            rf_keyword.kwname, tb_keyword.spec.name
        ) and not is_normalized_equal(rf_keyword.kwname.split(".")[-1], tb_keyword.spec.name):
            raise NameError(
                f"Cannot parse the execution: the Robot Framework keyword '{rf_keyword.kwname}' "
                f"does not match the TestBench keyword '{tb_keyword.spec.name}'."
            )

    def _get_keyword_messages(self, keyword: Keyword):
        if hasattr(keyword, "messages"):
            for message in keyword.messages:
                yield self._create_itb_exec_comment(message)
        if hasattr(keyword, "body"):
            for kw in keyword.body:
                yield from self._get_keyword_messages(kw)

    def get_html_keyword_comment(self, keyword: Keyword):
        """Comment of one keyword execution.

        'STRUCTURED' shows the sub keywords of a Robot user keyword with their
        log messages, 'FLAT' keeps the plain list of messages of earlier
        versions.
        """
        if self.keyword_comment_style is KeywordCommentStyle.STRUCTURED:
            return f"<html><body>{self.keyword_comment_renderer.render(keyword)}</body></html>"
        return self._flat_keyword_comment(keyword)

    def _flat_keyword_comment(self, keyword: Keyword):
        messages = list(self._get_keyword_messages(keyword))
        unique_messages = []
        for msg in messages:
            if msg not in unique_messages:
                unique_messages.append(msg)
        return (
            "<html>"
            "<body>"
            "<pre>"
            f"Start Time:   {self.get_isotime_from_robot_timestamp(keyword.starttime)}\n"
            f"End Time:     {self.get_isotime_from_robot_timestamp(keyword.endtime)}\n"
            f"Elapsed Time: {timedelta(milliseconds=keyword.elapsedtime)!s}\n"
            "</pre>"
            "<table style='font-family: monospace; border: none; table-layout: auto;'>"
            "<tr>"
            f"{'</tr><tr>'.join(unique_messages)}"
            "</tr>"
            "</table>"
            "</body>"
            "</html>"
        )

    def _create_itb_exec_comment(
        self,
        message,
    ) -> str:  # Todo: low prio: pattern für message in config festlegen
        message_time = self.get_isotime_from_robot_timestamp(
            message.timestamp, time_format="%H:%M:%S.%f"
        )
        msg = message.html_message.replace("<hr>", "<br/>").replace("<br>", "<br/>").strip()
        return (
            f"<td {render_log_level(message.level)}><b>{message.level}</b></td>"
            f"<td><pre>{msg}</pre></td><td>{message_time}</td>"
        )

    @staticmethod
    def get_isotime_from_robot_timestamp(timestamp, time_format="%Y-%m-%d %H:%M:%S.%f"):
        try:
            return timestamp.astimezone().strftime(time_format)[:-3]
        except AttributeError:
            return (
                datetime.strptime(timestamp, "%Y%m%d %H:%M:%S.%f")
                .astimezone()
                .strftime(time_format)[:-3]
            )

    @staticmethod
    def _format_utc_timestamp(dt: datetime) -> str:
        """Format datetime to ISO 8601 UTC string with millisecond precision."""
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

    def _set_compound_keyword_execution_verdict(
        self, compound_keyword: KeywordCall, test_steps: list[KeywordCall]
    ):
        if compound_keyword.exec is None:
            compound_keyword.exec = _empty_keyword_call_execution()
        compound_keyword.exec.verdict = KeywordVerdict.Skipped
        children = list(filter(lambda ts: ts.parentID == compound_keyword.sequenceID, test_steps))
        for child in children:
            if child.exec is None:
                logger.debug(
                    f"Child keyword '{child.spec.name}' had no execution details "
                    f"and is therefore ignored."
                )
                child.exec = _empty_keyword_call_execution()
            if child.spec.keywordType == KeywordType.Compound:
                self._set_compound_keyword_execution_verdict(child, test_steps)
            if child.spec.keywordType == KeywordType.Textual:
                child.exec.verdict = KeywordVerdict.Skipped
            if child.exec.verdict is KeywordVerdict.Fail:
                compound_keyword.exec.verdict = KeywordVerdict.Fail
                break
            if child.exec.verdict is KeywordVerdict.Pass:
                compound_keyword.exec.verdict = KeywordVerdict.Pass

        compound_keyword.exec.duration = sum(
            child.exec.duration for child in children if child.exec
        )
        if children and children[-1].exec:
            compound_keyword.exec.time = children[-1].exec.time

    @staticmethod
    def _set_itb_test_case_status(itb_test_case: TestCaseDetails, robot_status: str):
        if not itb_test_case.exec:
            return None
        robot_status = robot_status.lower()
        if robot_status == "pass":
            itb_test_case.exec.status = ActivityStatus.Performed
            itb_test_case.exec.verdict = VerdictStatus.Pass
            return ExecutionResultForImport(
                status=ActivityStatus.Performed,
                verdict=VerdictStatus.Pass,
                execStatus=ExecStatus.NotBlocked,
            )
        if robot_status == "fail":
            itb_test_case.exec.status = ActivityStatus.Performed
            itb_test_case.exec.verdict = VerdictStatus.Fail
            return ExecutionResultForImport(
                status=ActivityStatus.Performed,
                verdict=VerdictStatus.Fail,
                execStatus=ExecStatus.NotBlocked,
            )
        itb_test_case.exec.status = ActivityStatus.Running
        itb_test_case.exec.verdict = VerdictStatus.Undefined
        return ExecutionResultForImport(
            status=ActivityStatus.Running,
            verdict=VerdictStatus.Undefined,
            execStatus=ExecStatus.NotBlocked,
        )

    def _render_robot_rows(self, suite: TestSuite) -> tuple[str, str, dict[str, list[TestCaseRow]]]:
        """Comment table rows of this run, keyed by test case uniqueID, plus the suite times."""
        suite_start_time = "99999999 00:00:00.000"
        suite_end_time = "00000000 00:00:00.000"
        robot_rows: dict[str, list[TestCaseRow]] = {}
        for test in suite.tests:
            suite_start_time = min(suite_start_time, test.starttime)
            suite_end_time = max(suite_end_time, test.endtime)
            test_chain = get_test_chain(test.name, self.phase_pattern)
            if test_chain:
                unique_id = test_chain.name
                name = test_chain.name if test_chain.index == 1 else ""
                phase = f"Phase {test_chain.index}/{test_chain.length}"
            else:
                unique_id = test.name
                name = test.name
                phase = ""
            if test.status != "PASS":
                message = re.sub(TB_ARTIFACT_REGEX, "", test.message)
                message = (
                    message[len("*HTML*") :]
                    .replace("<hr>", "<br />")
                    .replace("<br>", "<br />")
                    .strip()
                    if message.startswith("*HTML*")
                    else html.escape(message)
                )
            else:
                message = self.get_isotime_from_robot_timestamp(test.endtime)
            robot_rows.setdefault(unique_id, []).append(
                TestCaseRow(
                    unique_id=unique_id,
                    name=name,
                    phase=phase,
                    status=test.status,
                    message=message,
                )
            )
        return suite_start_time, suite_end_time, robot_rows

    def end_suite(self, suite: TestSuite):
        if not suite.metadata.get("uniqueID") or len(suite.suites):
            return
        test_case_set = self.json_reader.read_test_case_set(suite.metadata["uniqueID"])
        if not test_case_set or not test_case_set.exec:
            return
        for testcase in test_case_set.testCases:
            current_itb_test_case = self.itb_test_case_catalog.get(testcase.uniqueID)
            if current_itb_test_case is None or testcase.exec is None:
                continue
            if current_itb_test_case.exec:
                testcase.exec.verdict = current_itb_test_case.exec.verdict
                testcase.exec.status = current_itb_test_case.exec.status
                testcase.exec.execStatus = current_itb_test_case.exec.execStatus
                testcase.exec.comments = current_itb_test_case.exec.comments
        base_entry = self.base_protocol_by_key.get(test_case_set.key)
        merged_test_cases = (
            merge_test_case_executions(base_entry.testCases, self.protocol_test_cases)
            if base_entry
            else self.protocol_test_cases
        )
        children = self._test_case_set_children(test_case_set, merged_test_cases)
        self.merged_verdicts[test_case_set.uniqueID] = self._merged_test_case_set_verdict(
            suite, children
        )
        suite_start_time, suite_end_time, robot_rows = self._render_robot_rows(suite)
        table_rows: list[TestCaseRow] = []
        for unique_id, verdict, protocol_entry in children:
            if unique_id in robot_rows:
                table_rows.extend(robot_rows[unique_id])
            elif protocol_entry is not None:
                table_rows.append(preserved_table_row(protocol_entry))
            else:
                table_rows.append(unexecuted_table_row(unique_id, verdict))

        test_case_set.exec.comments = render_test_case_set_table(
            table_rows,
            start=self.get_isotime_from_robot_timestamp(suite_start_time),
            end=self.get_isotime_from_robot_timestamp(suite_end_time),
        )
        self.protocol_test_case_set = TestCaseSetExecutionForImport(
            testCaseSetKey=test_case_set.key,
            executionKey=str(test_case_set.exec.key),
            durationMillis=suite.elapsedtime,
            testCases=merged_test_cases,
            comments=RichTextForImport(html=test_case_set.exec.comments),
        )
        self.executed_protocol.append(self.protocol_test_case_set)
        write_test_structure_element(self.json_result, test_case_set)
        logger.debug(
            f"Successfully wrote the result from suite "
            f"{test_case_set.uniqueID} to TestBench's Json Report."
        )
        if self.listener_uid:
            self.write_listener_mode_protocols()

    def _assemble_main_protocol(self) -> list[TestCaseSetExecutionForImport]:
        """Executed test case sets plus every pre-existing entry this run did not touch."""
        executed_keys = {entry.testCaseSetKey for entry in self.executed_protocol}
        carried_over = [
            entry for entry in self.base_protocol if entry.testCaseSetKey not in executed_keys
        ]
        if carried_over:
            logger.info(
                f"{len(carried_over)} test case set executions of the existing protocol "
                f"were not part of this Robot Framework run and are kept unchanged."
            )
        return carried_over + self.executed_protocol

    def write_listener_mode_protocols(self):
        write_main_protocol(self.json_result, self._assemble_main_protocol())
        Path.mkdir(Path(self.json_result_path), parents=True)
        shutil.copy(
            Path(self.json_result) / "protocol.json",
            Path(self.json_result_path) / "protocol.json",
        )
        shutil.copy(
            Path(self.json_dir) / "project.json",
            Path(self.json_result_path) / "project.json",
        )
        for file in Path(self.json_result).iterdir():
            if file.name.startswith(self.listener_uid) and file.name.endswith(".json"):
                shutil.copy(
                    Path(self.json_result) / file.name,
                    Path(self.json_result_path) / file.name,
                )
        directory_to_zip(Path(self.json_result_path))
        shutil.rmtree(Path(self.json_result_path))

    def end_result(self, result):
        tt_tree = self.json_reader.read_test_theme_tree()
        if tt_tree:
            test_suite_counter = self._update_tree_verdicts(tt_tree)
            write_test_structure_element(self.json_result, tt_tree)
            write_main_protocol(self.json_result, self._assemble_main_protocol())
            write_references(self.json_result, self.artifact_storage.tb_references)
            if test_suite_counter and self.itb_test_case_catalog:
                logger.info(f"Successfully read {test_suite_counter} test suites.")
            else:
                logger.warning("No test suites with execution information found.")
            if self.create_zip:
                directory_to_zip(Path(self.json_result), self.json_result_path)
            elif self.json_result != self.json_result_path:
                # if not self.create_zip:
                copytree(self.json_dir, self.json_result_path, dirs_exist_ok=True)
                copytree(self.json_result, self.json_result_path, dirs_exist_ok=True)
            self.tempdir.cleanup()
        logger.info(
            f"Successfully wrote the Robot Framework execution results to the TestBench report: "
            f"'{Path(self.json_result_path).absolute()}{self.create_zip * '.zip'}'"
        )

    @staticmethod
    def _test_case_set_children(
        test_case_set, merged_test_cases: list[TestCaseExecutionForImport]
    ) -> list[tuple[str, Verdict | None, TestCaseExecutionForImport | None]]:
        """All test cases of a set in report order, with their current verdict.

        A test case the current run executed, and one only the existing protocol
        knows about, are represented by their protocol entry. Test cases without
        any execution - never run, blocked or canceled ones - contribute the
        verdict they carry in the report, so they are neither lost in the comment
        table nor in the verdict of the set.
        """
        protocol_by_unique_id = {test_case.uniqueID: test_case for test_case in merged_test_cases}
        children = []
        seen: set[str] = set()
        for test_case in test_case_set.testCases:
            seen.add(test_case.uniqueID)
            protocol_entry = protocol_by_unique_id.get(test_case.uniqueID)
            verdict = (
                display_verdict_of(protocol_entry.result)
                if protocol_entry is not None and protocol_entry.result is not None
                else display_verdict_of(test_case.exec)
            )
            children.append((test_case.uniqueID, verdict, protocol_entry))
        for test_case in merged_test_cases:
            if test_case.uniqueID not in seen:
                children.append(
                    (test_case.uniqueID, display_verdict_of(test_case.result), test_case)
                )
        return children

    def _merged_test_case_set_verdict(
        self,
        suite: TestSuite,
        children: list[tuple[str, Verdict | None, TestCaseExecutionForImport | None]],
    ) -> Verdict:
        """Verdict of a test case set over all of its test cases.

        Follows the priority of the web clients: a blocked test case outranks a
        failed one, a failed one outranks an undefined one, and a skipped test
        case never outranks anything.
        """
        robot_verdict = Verdict.Fail if suite.status.upper() == "FAIL" else Verdict.Undefined
        merged_verdict = aggregate_verdicts([verdict for _, verdict, _ in children])
        if merged_verdict is None:
            return robot_verdict
        # A suite that failed outside its test cases (e.g. in a suite setup) must
        # not be reported as passed.
        if robot_verdict is Verdict.Fail and merged_verdict is Verdict.Pass:
            return robot_verdict
        return merged_verdict

    def _update_tree_verdicts(self, tt_tree) -> int:
        """Writes the merged verdicts into the test structure tree and propagates them upwards."""
        nodes = [tt_tree.root, *tt_tree.nodes]
        children: dict[str, list] = {}
        for node in tt_tree.nodes:
            children.setdefault(node.base.parentKey, []).append(node)
        self._update_test_case_nodes(nodes)
        set_verdicts: dict[str, Verdict | None] = {}
        updated_nodes = 0
        for node in nodes:
            node_exec = getattr(node, "exec", None)
            if not isinstance(node, TestCaseSetNode) or node_exec is None:
                continue
            merged_verdict = self.merged_verdicts.get(node.base.uniqueID)
            if merged_verdict is not None:
                self._apply_verdict(node_exec, merged_verdict)
                updated_nodes += 1
            set_verdicts[node.base.key] = display_verdict_of(node_exec)
        for node in nodes:
            node_exec = getattr(node, "exec", None)
            if isinstance(node, (TestCaseSetNode, TestCaseNode)) or node_exec is None:
                continue
            if self.test_suites.get(node.base.uniqueID) is None:
                continue
            verdict = self._subtree_verdict(node, children, set_verdicts)
            if verdict is None:
                continue
            self._apply_verdict(node_exec, verdict)
            updated_nodes += 1
        return updated_nodes

    @staticmethod
    def _apply_verdict(node_exec, verdict: Verdict) -> None:
        """Writes the canonical status triple of a verdict, as the web clients do."""
        state: ExecutionState = execution_state_for(verdict)
        node_exec.verdict = state.verdict
        node_exec.status = state.status
        node_exec.execStatus = state.exec_status

    def _update_test_case_nodes(self, nodes: list) -> int:
        """Writes the execution result of every executed test case into the tree.

        Test cases the current Robot Framework run did not cover keep the values
        they were exported with.
        """
        updated_test_cases = 0
        for node in nodes:
            node_exec = getattr(node, "exec", None)
            if not isinstance(node, TestCaseNode) or node_exec is None:
                continue
            itb_test_case = self.itb_test_case_catalog.get(node.base.uniqueID)
            if itb_test_case is None or itb_test_case.exec is None:
                continue
            node_exec.verdict = itb_test_case.exec.verdict
            node_exec.status = itb_test_case.exec.status
            node_exec.execStatus = itb_test_case.exec.execStatus
            updated_test_cases += 1
        if updated_test_cases:
            logger.debug(f"Updated {updated_test_cases} test cases in the test structure tree.")
        return updated_test_cases

    def _subtree_verdict(self, node, children, set_verdicts) -> Verdict | None:
        verdicts: list[Verdict | None] = []
        for child in children.get(node.base.key, []):
            if isinstance(child, TestCaseNode):
                continue
            if isinstance(child, TestCaseSetNode):
                verdicts.append(set_verdicts.get(child.base.key))
            else:
                verdicts.append(self._subtree_verdict(child, children, set_verdicts))
        return aggregate_verdicts(verdicts)

    @staticmethod
    def _get_execution_result(robot_status: str) -> dict:
        robot_status = robot_status.lower()
        if robot_status == "pass":
            return {
                "execution_verdict": VerdictStatus.Pass,
                "activity_status": ActivityStatus.Performed,
            }
        if robot_status == "fail":
            return {
                "execution_verdict": VerdictStatus.Fail,
                "activity_status": ActivityStatus.Performed,
            }
        return {
            "execution_verdict": VerdictStatus.Undefined,
            "activity_status": ActivityStatus.Skipped,
        }

    @staticmethod
    def _get_keyword_result(robot_status: str) -> KeywordVerdict:
        robot_status = robot_status.upper()
        if robot_status == "PASS":
            return KeywordVerdict.Pass
        if robot_status == "FAIL":
            return KeywordVerdict.Fail
        if robot_status == "NOT RUN":
            return KeywordVerdict.Skipped
        return KeywordVerdict.Skipped


class TestChain:
    def __init__(self, name, index, length):
        self.name = str(name)
        self.index = int(index)
        self.length = int(length)


def get_test_chain(test_name: str, phase_pattern: str) -> TestChain | None:
    matcher = re.match(get_test_chain_pattern(phase_pattern), test_name)
    if matcher:
        return TestChain(*matcher.groups())
    return None


def get_test_chain_pattern(phase_pattern: str) -> str:
    testcase_placeholder = str(uuid.uuid4().int)
    index_placeholder = str(uuid.uuid4().int)
    length_placeholder = str(uuid.uuid4().int)
    raw_pattern = re.escape(
        phase_pattern.format(
            testcase=testcase_placeholder,
            index=index_placeholder,
            length=length_placeholder,
        )
    )
    return (
        raw_pattern.replace(testcase_placeholder, r"(.+?)")
        .replace(index_placeholder, r"(\d)")
        .replace(length_placeholder, r"(\d)")
    )


def get_normalized_keyword_name(keyword_name: str) -> str:
    return re.sub(r"[\s_]", "", keyword_name.lower())


def is_normalized_equal(kw_one: str, kw_two: str) -> bool:
    norm_kw_one = get_normalized_keyword_name(kw_one)
    norm_kw_two = get_normalized_keyword_name(kw_two)
    return norm_kw_one == norm_kw_two
