import html
import os
import re
import shutil
import tempfile
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from shutil import copytree
from typing import Dict, List, Optional, Union
from urllib.parse import unquote

from robot.result import Keyword, ResultVisitor, TestCase, TestSuite

from .config import AttachmentConflictBehaviour, Configuration, ReferenceBehaviour
from .json_reader import TestBenchJsonReader
from .json_writer import write_test_structure_element
from .log import logger
from .model import (
    ActivityStatus,
    ExecutionVerdict,
    InteractionDetails,
    InteractionExecutionSummary,
    InteractionType,
    InteractionVerdict,
    Reference,
    ReferenceType,
    SequencePhase,
    TestCaseDetails,
    TestCaseExecutionDetails,
)
from .utils import directory_to_zip, ensure_dir_exists, get_directory

BACKGROUND_COLOR = {
    "PASS": "#04AF91",
    "FAIL": "#ce3e01",
    "ERROR": "#ce3e01",
    "SKIP": "#F3E96A",
    "WARN": "#D48627",
    "INFO": "#ddd",
}
COLOR = {
    "PASS": "#fff",
    "FAIL": "#fff",
    "ERROR": "#fff",
    "SKIP": "#000",
    "WARN": "#fff",
    "INFO": "#000",
}


class ResultWriter(ResultVisitor):
    def __init__(
        self, json_report: str, json_result: str, config: Configuration, output_xml
    ) -> None:
        self.json_dir = get_directory(json_report)
        self.output_xml = output_xml
        self.reference_behaviour = config.referenceBehaviour
        self.attachment_conflict_behaviour = config.attachmentConflictBehaviour
        self.tempdir = tempfile.TemporaryDirectory(dir=os.curdir)
        if json_result is None:
            self.create_zip = bool(os.path.splitext(json_report)[1].lower() == ".zip")
            self.json_result = self.json_dir
            self.json_result_path = self.json_dir
        else:
            self.json_result_path, result_extension = os.path.splitext(json_result)
            self.create_zip = bool(result_extension.lower() == ".zip")
            self.json_result = self.tempdir.name
            if self.create_zip:
                copytree(self.json_dir, self.json_result, dirs_exist_ok=True)
        self.json_reader = TestBenchJsonReader(self.json_dir)
        self.attachments_path = Path(self.json_result, "attachments")
        # if self.attachments_path.exists():  TODO: RR Sollten wir löschen????
        #     shutil.rmtree(self.attachments_path)
        # os.mkdir(self.attachments_path)
        self.test_suites: Dict[str, TestSuite] = {}
        self.keywords: List[Keyword] = []
        self.itb_test_case_catalog: Dict[str, TestCaseDetails] = {}
        self.phase_pattern = config.phasePattern
        self.test_chain: List[TestCase] = []

    def start_suite(self, suite: TestSuite):
        if suite.metadata:
            self.test_suites[suite.metadata["uniqueID"]] = suite

    def _get_interactions_by_type(
        self, interactions: List[InteractionDetails], interaction_type: InteractionType
    ):
        for interaction in interactions:
            if interaction.interactionType == interaction_type:
                yield interaction
            if interaction.interactionType == InteractionType.Compound:
                yield from self._get_interactions_by_type(
                    interaction.interactions, interaction_type
                )

    def end_test(self, test: TestCase):
        self._test_setup_passed: Optional[bool] = None
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
        if itb_test_case.exec is None:
            itb_test_case.exec = TestCaseExecutionDetails.from_dict({})
        if itb_test_case.exec.key in ["", "-1"]:
            logger.warning(
                f"Test case {itb_test_case.uniqueID} was not exported based on "
                f"execution and is therefore not importable."
            )
        try:
            atomic_interactions = list(
                self._get_interactions_by_type(itb_test_case.interactions, InteractionType.Atomic)
            )
            compound_interactions = list(
                self._get_interactions_by_type(itb_test_case.interactions, InteractionType.Compound)
            )
            self._set_atomic_interactions_execution_result(atomic_interactions, self.test_chain)
            for interaction in compound_interactions:
                self._set_compound_interaction_execution_result(interaction)
            self._set_itb_testcase_execution_result(itb_test_case, self.test_chain)
            self._set_itb_testcase_execution_comment(itb_test_case, self.test_chain)
            if self.reference_behaviour != ReferenceBehaviour.NONE:
                self._set_itb_testcase_references(itb_test_case, self.test_chain)
        except TypeError:
            logger.error(
                "Could not find an itb testcase that corresponds "
                "to the given Robot Framework testcase."
            )
        self.itb_test_case_catalog[test_uid] = itb_test_case
        write_test_structure_element(self.json_result, itb_test_case)
        logger.debug(
            f"Successfully wrote the result from test "
            f"{itb_test_case.uniqueID} to TestBench's Json Report."
        )

    def _set_itb_testcase_references(
        self, itb_test_case: TestCaseDetails, test_chain: List[TestCase]
    ):
        for test in test_chain:
            itb_references = self._get_itb_reference(test.message)
            for reference in itb_references:
                if reference not in itb_test_case.exec.references:
                    itb_test_case.exec.references.append(reference)

    def _get_itb_reference(self, test_message: str) -> List[Reference]:
        references = []
        for path in re.findall(r"itb-reference:\s*(\S*)", test_message):
            if path.startswith("file:///"):
                file_path = Path(unquote(path[len("file:///") :]))
                output_dir = Path(self.output_xml).parent
                if file_path.exists():
                    reference_path = file_path
                elif Path(output_dir, file_path).exists():
                    reference_path = Path(output_dir, file_path)
                else:
                    if (
                        file_path.is_absolute()
                        and self.reference_behaviour == ReferenceBehaviour.REFERENCE
                    ):
                        references.append(self._create_reference(file_path))
                    else:
                        logger.warning(f"Referenced file '{file_path}' does not exist.")
                    continue
                file_size = os.path.getsize(reference_path)
                if file_size >= 10000000:
                    logger.error(
                        f"Trying to attach file '{reference_path}'. "
                        "Attachment file size must not exceed 10 MB "
                        f"but is {file_size / 1000000} MB."
                    )
                    reference = self._create_reference(reference_path.name)
                else:
                    reference = self._create_attachment(reference_path)
                if reference:
                    references.append(reference)
            elif re.match(r"\S+://", path):
                references.append(Reference(ReferenceType.Hyperlink, path))
            else:
                logger.warning(f"Could not identify type of test message reference '{path}'.")
        return references

    @staticmethod
    def _create_reference(reference_path: Union[Path, str]) -> Reference:
        return Reference(ReferenceType.Reference, str(reference_path))

    def _create_attachment(self, filepath: Path) -> Optional[Reference]:
        if self.reference_behaviour == ReferenceBehaviour.REFERENCE:
            return self._create_reference(filepath.resolve())
        ensure_dir_exists(self.attachments_path)
        filename = Path(filepath).name
        if (
            not Path(self.attachments_path, filename).exists()
            or self.attachment_conflict_behaviour == AttachmentConflictBehaviour.USE_NEW
        ):
            shutil.copyfile(filepath, self.attachments_path / filename, follow_symlinks=True)
            return Reference(ReferenceType.Attachment, f"attachments/{filename}")
        if self.attachment_conflict_behaviour == AttachmentConflictBehaviour.USE_EXISTING:
            return Reference(ReferenceType.Attachment, f"attachments/{filename}")
        if self.attachment_conflict_behaviour == AttachmentConflictBehaviour.RENAME_NEW:
            unique_path = self._create_unique_path(self.attachments_path / filename)
            shutil.copyfile(filepath, unique_path, follow_symlinks=True)
            unique_file = Path(unique_path).name
            logger.info(
                f"Attachment '{filename}' does already exist. "
                f"Creating new unique attachment '{unique_file}'."
            )
            return Reference(ReferenceType.Attachment, f"attachments/{unique_file}")
        if self.attachment_conflict_behaviour == AttachmentConflictBehaviour.ERROR:
            logger.error(f"Attachment '{filename}' does already exist.")
            return None

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

    def _set_itb_testcase_execution_comment(self, itb_test_case, test_chain: List[TestCase]):
        exec_comments = []
        for test in test_chain:
            message = re.sub(r"\s*itb-reference:\s*(\S*)", "", test.message)
            html_message = (
                message[len("*HTML*") :].replace("<hr>", "<br/>").replace("<br>", "<br/>").strip()
                if test.message.startswith("*HTML*")
                else html.escape(message)
            )
            test_chain_obj = get_test_chain(test.name, self.phase_pattern)
            test_phase_name = (
                f"<b>Phase {test_chain_obj.index}/{test_chain_obj.length} : "
                f"<span {self.render_status(test.status)}>{test.status}</span></b>"
                if test_chain_obj
                else f"<b><span {self.render_status(test.status)}>{test.status}</span></b>"
            )
            exec_comment = (
                f"{test_phase_name}"
                "<pre>"
                f"Start Time:   {self.get_isotime_from_robot_timestamp(test.starttime)}\n"
                f"End Time:     {self.get_isotime_from_robot_timestamp(test.endtime)}\n"
                f"Elapsed Time: {str(timedelta(milliseconds=test.elapsedtime))}\n"
                "</pre>"
                f"Message: <p><pre>{html_message}</pre></p>\n"
            )
            exec_comments.append(exec_comment)
        itb_test_case.exec.comments = f"<html><body>{''.join(exec_comments)}</body></html>"

    def _set_itb_testcase_execution_result(self, itb_test_case, test_chain):
        has_failed_chain = list(filter(lambda tc: tc.status.upper() == "FAIL", test_chain))
        passed_keywords = all(tc.status.upper() == "PASS" for tc in test_chain)
        itb_test_case.exec.actualDuration = sum([tc.elapsedtime for tc in test_chain])
        if has_failed_chain:
            self._set_itb_test_case_status(itb_test_case, "fail")
        elif passed_keywords:
            self._set_itb_test_case_status(itb_test_case, "pass")
        else:
            self._set_itb_test_case_status(itb_test_case, "undef")

    def _get_test_phase_body(self, test_phase: TestCase):
        return test_phase.body

    def _get_test_phase_setup(self, test_phase: TestCase):
        test_phase_setup = []
        if test_phase.has_setup:
            self._test_setup_passed = test_phase.setup.passed
            setup_keywords = list(filter(lambda kw: isinstance(kw, Keyword), test_phase.setup.body))
            if setup_keywords:
                test_phase_setup = setup_keywords
            else:
                test_phase_setup = [test_phase.setup]
        return test_phase_setup

    def _get_test_phase_teardown(self, test_phase: TestCase):
        test_phase_teardown = []
        if test_phase.has_teardown:
            teardown_keywords = list(
                filter(lambda kw: isinstance(kw, Keyword), test_phase.teardown.body)
            )
            if teardown_keywords:
                test_phase_teardown = teardown_keywords
            else:
                test_phase_teardown = [test_phase.teardown]
        return test_phase_teardown

    def _set_atomic_interactions_execution_result(
        self, atomic_interactions: List[InteractionDetails], test_chain: List[TestCase]
    ):
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
        setup_interactions = list(
            filter(
                lambda atomic_interaction: atomic_interaction.spec.sequencePhase
                == SequencePhase.Setup,
                atomic_interactions,
            )
        )
        test_step_interactions = list(
            filter(
                lambda atomic_interaction: atomic_interaction.spec.sequencePhase
                == SequencePhase.TestStep,
                atomic_interactions,
            )
        )
        teardown_interactions = list(
            filter(
                lambda atomic_interaction: atomic_interaction.spec.sequencePhase
                == SequencePhase.Teardown,
                atomic_interactions,
            )
        )
        for index, interaction in enumerate(setup_interactions):
            if interaction.exec is None:
                interaction.exec = InteractionExecutionSummary.from_dict({})
            if index < len(test_chain_setup):
                keyword = test_chain_setup[index]
                self._check_matching_interaction_and_keyword_name(keyword, interaction)
                interaction.exec = self._get_interaction_exec_from_keyword(keyword)
            else:
                if self._test_setup_passed:
                    interaction.exec.verdict = InteractionVerdict.Undefined
                else:
                    interaction.exec.verdict = InteractionVerdict.Skipped

        for index, interaction in enumerate(test_step_interactions):
            if interaction.exec is None:
                interaction.exec = InteractionExecutionSummary.from_dict({})
            if not self._test_setup_passed:
                interaction.exec.verdict = InteractionVerdict.Skipped
            elif index < len(test_chain_body):
                keyword = test_chain_body[index]
                self._check_matching_interaction_and_keyword_name(keyword, interaction)
                interaction.exec = self._get_interaction_exec_from_keyword(keyword)
            else:
                interaction.exec.verdict = InteractionVerdict.Undefined

        for index, interaction in enumerate(teardown_interactions):
            if interaction.exec is None:
                interaction.exec = InteractionExecutionSummary.from_dict({})
            if index < len(test_chain_teardown):
                keyword = test_chain_teardown[index]
                self._check_matching_interaction_and_keyword_name(keyword, interaction)
                interaction.exec = self._get_interaction_exec_from_keyword(keyword)
            else:
                interaction.exec.verdict = InteractionVerdict.Undefined

    def _get_interaction_exec_from_keyword(self, keyword: Keyword) -> InteractionExecutionSummary:
        return InteractionExecutionSummary.from_dict(
            {
                'verdict': self._get_interaction_result(keyword.status),
                'time': keyword.endtime,
                'duration': keyword.elapsedtime,
                'comments': self.get_html_keyword_comment(keyword),
            }
        )

    def _check_matching_interaction_and_keyword_name(
        self, keyword: Keyword, interaction: InteractionDetails
    ) -> None:
        if not is_normalized_equal(keyword.kwname, interaction.name) and not is_normalized_equal(
            keyword.kwname.split('.')[-1], interaction.name
        ):
            raise NameError(
                f"Execution can not be parsed, "
                f"because keyword name '{keyword.kwname}' does not match with "
                f"interaction '{interaction.name}' name."
            )

    def _get_keyword_messages(self, keyword: Keyword):
        if hasattr(keyword, "messages"):
            for message in keyword.messages:
                yield self._create_itb_exec_comment(message)
        if hasattr(keyword, "body"):
            for keyword in keyword.body:
                yield from self._get_keyword_messages(keyword)

    def get_html_keyword_comment(self, keyword: Keyword):
        messages = list(self._get_keyword_messages(keyword))
        return (
            "<html>"
            "<body>"
            "<style>"
            "td {padding: 5px; border: none;} "
            "table {font-family: monospace; border: none;}"
            "</style>"
            "<pre>"
            f"Start Time:   {self.get_isotime_from_robot_timestamp(keyword.starttime)}\n"
            f"End Time:     {self.get_isotime_from_robot_timestamp(keyword.endtime)}\n"
            f"Elapsed Time: {str(timedelta(milliseconds=keyword.elapsedtime))}\n"
            "</pre>"
            "<table>"
            "<tr>"
            f"{'</tr><tr>'.join(messages)}"
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
            f"<td {self.render_status(message.level)}><b>{message.level}</b></td>"
            f"<td><pre>{msg}</pre></td><td>{message_time}</td>"
        )

    @staticmethod
    def get_isotime_from_robot_timestamp(timestamp, time_format="%Y-%m-%d %H:%M:%S.%f"):
        return datetime.strptime(timestamp, "%Y%m%d %H:%M:%S.%f").strftime(time_format)[:-3]

    def _set_compound_interaction_execution_result(self, compound_interaction: InteractionDetails):
        atomic_interactions = list(
            self._get_interactions_by_type(
                compound_interaction.interactions, InteractionType.Atomic
            )
        )
        if compound_interaction.exec is None:
            compound_interaction.exec = InteractionExecutionSummary.from_dict({})
        compound_interaction.exec.verdict = InteractionVerdict.Skipped
        for atomic in atomic_interactions:
            if atomic.exec is None:
                logger.debug(
                    f"Atomic interaction {atomic.uniqueID} "
                    f"had no exec details and therefore ignored."
                )
                atomic.exec = InteractionExecutionSummary.from_dict({})
                # continue
            if atomic.exec.verdict is InteractionVerdict.Fail:
                compound_interaction.exec.verdict = InteractionVerdict.Fail
                break
            if atomic.exec.verdict is InteractionVerdict.Pass:
                compound_interaction.exec.verdict = InteractionVerdict.Pass

        compound_interaction.exec.duration = sum(
            [interaction.exec.duration for interaction in atomic_interactions]
        )
        compound_interaction.exec.time = atomic_interactions[-1].exec.time

    @staticmethod
    def _set_itb_test_case_status(itb_test_case: TestCaseDetails, robot_status: str):
        robot_status = robot_status.lower()
        if robot_status == "pass":
            itb_test_case.exec.status = ActivityStatus.Performed
            itb_test_case.exec.verdict = ExecutionVerdict.Pass
        elif robot_status == "fail":
            itb_test_case.exec.status = ActivityStatus.Performed
            itb_test_case.exec.verdict = ExecutionVerdict.Fail
        else:
            itb_test_case.exec.status = ActivityStatus.Running
            itb_test_case.exec.verdict = ExecutionVerdict.Undefined

    def end_suite(self, suite: TestSuite):
        if not suite.metadata.get("uniqueID") or len(suite.suites):
            return
        test_case_set = self.json_reader.read_test_case_set(suite.metadata["uniqueID"])
        if not test_case_set:
            return
        test_case_set.exec.verdict = suite.status

        for testcase in test_case_set.testCases:
            current_itb_test_case = self.itb_test_case_catalog.get(testcase.uniqueID)
            if current_itb_test_case is None:
                continue
            testcase.exec.verdict = current_itb_test_case.exec.verdict
            testcase.exec.status = current_itb_test_case.exec.status
            testcase.exec.execStatus = current_itb_test_case.exec.execStatus
            testcase.exec.comments = current_itb_test_case.exec.comments
        suite_start_time = "99999999 00:00:00.000"
        suite_end_time = "00000000 00:00:00.000"
        table_content = []
        for test in suite.tests:
            suite_start_time = min(suite_start_time, test.starttime)
            suite_end_time = max(suite_end_time, test.endtime)
            test_chain = get_test_chain(test.name, self.phase_pattern)

            if test_chain:
                name = test_chain.name if test_chain.index == 1 else ""
                phase = f"Phase {test_chain.index}/{test_chain.length}"
            else:
                name = test.name
                phase = ""
            if test.status != "PASS":
                message = re.sub(r"\s*itb-reference:\s*(\S*)", "", test.message)
                message = (
                    message[len("*HTML*") :]
                    .replace('<hr>', '<br />')
                    .replace('<br>', '<br />')
                    .strip()
                    if message.startswith("*HTML*")
                    else message
                )
            else:
                message = self.get_isotime_from_robot_timestamp(test.endtime)

            table_content.append(
                f"<td>{name}</td>"
                f"<td>{phase}</td>"
                f"<td {self.render_status(test.status)}><b>{test.status}</b></td>"
                f"<td><pre>{message}</pre></td>"
            )

        test_case_set.exec.comments = (
            "<html>"
            "<head>"
            "<style>"
            "td {padding: 5px; border: none; white-space: pre-wrap;} "
            "table {font-family: monospace; border: none;}"
            "</style>"
            "</head>"
            "<body>"
            "<pre>"
            f"Start Time:   {self.get_isotime_from_robot_timestamp(suite_start_time)}\n"
            f"End Time:     {self.get_isotime_from_robot_timestamp(suite_end_time)}\n"
            "</pre>"
            "<table>"
            "<tr>"
            f"{'</tr><tr>'.join(table_content)}"
            "</tr>"
            "</table>"
            "</body>"
            "</html>"
        )
        write_test_structure_element(self.json_result, test_case_set)
        logger.debug(
            f"Successfully wrote the result from suite "
            f"{test_case_set.uniqueID} to TestBench's Json Report."
        )

    @staticmethod
    def render_status(status):
        return (
            "style='"
            f"background-color: {BACKGROUND_COLOR.get(status, '#fff')}; "
            f"color: {COLOR.get(status, '#000')};'"
        )

    def end_result(self, result):
        tt_tree = self.json_reader.read_test_theme_tree()
        if tt_tree:
            test_suite_counter = 0
            for tse in tt_tree.nodes:
                if self.test_suites.get(tse.baseInformation.uniqueID) is None:
                    continue
                execution_result = self._get_execution_result(
                    self.test_suites[tse.baseInformation.uniqueID].status
                )
                tse.execution.verdict = execution_result["execution_verdict"]
                tse.execution.status = execution_result["activity_status"]
                test_suite_counter += 1
            write_test_structure_element(self.json_result, tt_tree)
            if test_suite_counter and self.itb_test_case_catalog:
                logger.info(f"Successfully read {test_suite_counter} test suites.")
            else:
                logger.warning("No test suites with execution information found.")
            if self.create_zip:
                directory_to_zip(self.json_result, self.json_result_path)
            elif self.json_result != self.json_result_path:
                copytree(self.json_dir, self.json_result_path, dirs_exist_ok=True)
                copytree(self.json_result, self.json_result_path, dirs_exist_ok=True)
            self.tempdir.cleanup()
        logger.info("Successfully wrote the robot execution results to TestBench's Json Report.")

    @staticmethod
    def _get_execution_result(robot_status: str) -> Dict:
        robot_status = robot_status.lower()
        if robot_status == "pass":
            return {
                "execution_verdict": ExecutionVerdict.Pass,
                "activity_status": ActivityStatus.Performed,
            }
        if robot_status == "fail":
            return {
                "execution_verdict": ExecutionVerdict.Fail,
                "activity_status": ActivityStatus.Performed,
            }
        return {
            "execution_verdict": ExecutionVerdict.Undefined,
            "activity_status": ActivityStatus.Skipped,
        }

    @staticmethod
    def _get_interaction_result(robot_status: str) -> InteractionVerdict:
        robot_status = robot_status.upper()
        if robot_status == "PASS":
            return InteractionVerdict.Pass
        if robot_status == "FAIL":
            return InteractionVerdict.Fail
        if robot_status == "NOT RUN":
            return InteractionVerdict.Skipped
        return InteractionVerdict.Skipped


class TestChain:
    def __init__(self, name, index, length):
        self.name = str(name)
        self.index = int(index)
        self.length = int(length)


def get_test_chain(test_name: str, phase_pattern: str) -> Optional[TestChain]:
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
