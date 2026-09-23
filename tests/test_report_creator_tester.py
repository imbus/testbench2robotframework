"""'set-tester-from-report-creator' makes the report's creator the tester of executed test cases.

The creator is read from 'reportCreation.creator' in the report's 'manifest.json'.
Only test cases this run actually performed (verdict Pass or Fail) get the tester,
in 'protocol.json' ('testerKey') as well as in their test case file ('exec.tester').
"""

import json
import logging
from types import SimpleNamespace

import pytest
from robot.result import TestCase
from test_fetch_results_output import make_report_dir

from testbench2robotframework import robotframework2testbench
from testbench2robotframework.config import Configuration
from testbench2robotframework.log import logger
from testbench2robotframework.model import (
    ActivityStatus,
    ExecStatus,
    TestCaseDetails,
    TestCaseExecutionDetails,
    TestCaseExecutionForImport,
    UserInfo,
    UserReference,
    VerdictStatus,
)
from testbench2robotframework.result_writer import ResultWriter, read_report_creator

UID = "itb-TC-136099-PC-421880"

MANIFEST = {
    "formatVersion": "1.0",
    "serverLocation": {"host": "Salsa.local", "port": 443},
    "reportCreation": {
        "creator": {"userKey": "0", "userLogin": "tt-admin", "userName": "Administrator"},
        "startDate": "2026-09-23T15:49:45.845+02:00",
        "endDate": "2026-09-23T15:49:45.975+02:00",
        "scope": {"projectKey": "50012", "tovKey": "60034", "cycleKey": "40037"},
        "summary": {"testThemesCount": 0, "testCaseSetsCount": 1, "testCasesCount": 3},
    },
    "serverVersions": {"version": "4.1", "databaseVersion": "4.1.01", "revision": "260723/5db9"},
}

CREATOR = UserInfo(userKey="0", userLogin="tt-admin", userName="Administrator")


def make_itb_test_case(tester=None):
    return TestCaseDetails(
        uniqueID=UID,
        spec=None,
        testSequence=[],
        parameters=[],
        keywords=[],
        exec=TestCaseExecutionDetails(
            key="79361",
            status=ActivityStatus.Planned,
            execStatus=ExecStatus.NotBlocked,
            verdict=VerdictStatus.Undefined,
            plannedDuration=0,
            actualDuration=0,
            currentUser=UserReference(key="0", name="tt-admin"),
            comments="",
            defects=[],
            udfs=[],
            tags=[],
            references=[],
            tester=tester,
        ),
    )


def make_result_writer(report_creator):
    writer = ResultWriter.__new__(ResultWriter)  # bypasses the file system heavy __init__
    writer.report_creator = report_creator
    writer.protocol_test_case = TestCaseExecutionForImport(UID, "79361", None, None, None)  # type: ignore[arg-type]
    return writer


def execute(writer, itb_test_case, *statuses):
    phases = [TestCase(name=UID, status=status) for status in statuses]
    writer._set_itb_testcase_execution_result(itb_test_case, phases)
    writer._set_itb_testcase_tester(itb_test_case)


@pytest.fixture
def warnings():
    records: list[logging.LogRecord] = []

    class Collector(logging.Handler):
        def emit(self, record):
            if record.levelno == logging.WARNING:
                records.append(record)

    handler = Collector()
    logger.addHandler(handler)
    yield records
    logger.removeHandler(handler)


class ReadReportCreatorTests:
    def test_creator_is_read_from_manifest(self, tmp_path):
        (tmp_path / "manifest.json").write_text(json.dumps(MANIFEST))

        assert read_report_creator(tmp_path) == CREATOR

    def test_missing_manifest_warns_and_returns_none(self, tmp_path, warnings):
        assert read_report_creator(tmp_path) is None
        assert len(warnings) == 1

    def test_manifest_without_creator_warns_and_returns_none(self, tmp_path, warnings):
        (tmp_path / "manifest.json").write_text(json.dumps({"formatVersion": "1.0"}))

        assert read_report_creator(tmp_path) is None
        assert len(warnings) == 1

    def test_creator_without_user_key_warns_and_returns_none(self, tmp_path, warnings):
        manifest = {"reportCreation": {"creator": {"userLogin": "tt-admin", "userName": "A"}}}
        (tmp_path / "manifest.json").write_text(json.dumps(manifest))

        assert read_report_creator(tmp_path) is None
        assert len(warnings) == 1

    def test_invalid_manifest_warns_and_returns_none(self, tmp_path, warnings):
        (tmp_path / "manifest.json").write_text("{ not json")

        assert read_report_creator(tmp_path) is None
        assert len(warnings) == 1


class SetTesterTests:
    @pytest.mark.parametrize("statuses", [("PASS",), ("FAIL",), ("PASS", "FAIL")])
    def test_performed_test_case_gets_the_creator_as_tester(self, statuses):
        writer = make_result_writer(CREATOR)
        itb_test_case = make_itb_test_case()

        execute(writer, itb_test_case, *statuses)

        assert writer.protocol_test_case.testerKey == "0"
        assert itb_test_case.exec.tester == UserReference(key="0", name="Administrator")

    @pytest.mark.parametrize("statuses", [("SKIP",), ("NOT RUN",), ("PASS", "SKIP")])
    def test_test_case_not_performed_gets_no_tester(self, statuses):
        writer = make_result_writer(CREATOR)
        itb_test_case = make_itb_test_case()

        execute(writer, itb_test_case, *statuses)

        assert writer.protocol_test_case.testerKey is None
        assert itb_test_case.exec.tester is None

    def test_existing_tester_is_overwritten(self):
        writer = make_result_writer(CREATOR)
        itb_test_case = make_itb_test_case(tester=UserReference(key="7", name="Neuer Benutzer 2"))

        execute(writer, itb_test_case, "PASS")

        assert itb_test_case.exec.tester == UserReference(key="0", name="Administrator")

    def test_without_creator_nothing_is_set(self):
        writer = make_result_writer(None)
        existing_tester = UserReference(key="7", name="Neuer Benutzer 2")
        itb_test_case = make_itb_test_case(tester=existing_tester)

        execute(writer, itb_test_case, "PASS")

        assert writer.protocol_test_case.testerKey is None
        assert itb_test_case.exec.tester == existing_tester


class OptionTests:
    def test_option_is_off_by_default(self):
        assert Configuration.from_dict({}).set_tester_from_report_creator is False

    def test_option_can_be_switched_on(self):
        configuration = Configuration.from_dict({"set-tester-from-report-creator": True})

        assert configuration.set_tester_from_report_creator is True


class ResultWriterOptionTests:
    @pytest.fixture(autouse=True)
    def run_in_tmp_path(self, tmp_path, monkeypatch):
        # The writer creates its temporary directories in the current working directory.
        monkeypatch.chdir(tmp_path)

    def make_writer(self, tmp_path, manifest, **options):
        report = make_report_dir(tmp_path / "report")
        (report / "manifest.json").write_text(json.dumps(manifest))
        (tmp_path / "output.xml").write_text("<robot/>")
        cfg = Configuration.from_dict({"merge-protocol": False, **options})
        return ResultWriter(str(report), None, cfg, str(tmp_path / "output.xml"))

    def test_with_option_the_creator_is_read(self, tmp_path):
        writer = self.make_writer(tmp_path, MANIFEST, **{"set-tester-from-report-creator": True})

        assert writer.report_creator == CREATOR

    def test_without_option_the_manifest_is_not_consulted(self, tmp_path, warnings):
        writer = self.make_writer(tmp_path, {})

        assert writer.report_creator is None
        assert not [record for record in warnings if "manifest.json" in record.getMessage()]


class Robot2TestbenchConfigurationTests:
    """Library callers may pass a Configuration instead of a config file dictionary.

    'dataclasses.asdict' of a Configuration uses field names, which 'from_dict' does
    not read - converting it back to a dictionary would silently drop every option.
    """

    def test_configuration_instance_is_used_as_is(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        report = make_report_dir(tmp_path / "report")
        (report / "manifest.json").write_text(json.dumps(MANIFEST))
        (tmp_path / "output.xml").write_text("<robot/>")
        used = {}
        monkeypatch.setattr(robotframework2testbench, "perform_version_check", lambda _: None)
        monkeypatch.setattr(robotframework2testbench, "setup_logger", lambda _: None)
        monkeypatch.setattr(
            robotframework2testbench,
            "ResultWriter",
            lambda _report, _result, configuration, _xml: used.setdefault("config", configuration),
        )
        monkeypatch.setattr(
            robotframework2testbench, "ExecutionResult", lambda _: SimpleNamespace(visit=lambda _: None)
        )
        configuration = Configuration.from_dict({"set-tester-from-report-creator": True})

        robotframework2testbench.robot2testbench(report, tmp_path / "output.xml", None, configuration)

        assert used["config"] is configuration
