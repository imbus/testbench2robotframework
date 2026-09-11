"""Where fetch-results writes the updated report, and what it leaves behind.

The input report is a directory or a ZIP; the output ('-d') is a ZIP, a directory,
or - without '-d' - the input itself. Whatever the combination, no extracted copy
of the input stays behind unless 'keep-extracted-report' asks for it.
"""

import json
import zipfile
from pathlib import Path

import pytest
from test_tree_verdicts import build_tree

from testbench2robotframework.config import Configuration
from testbench2robotframework.json_writer import write_test_structure_element
from testbench2robotframework.result_writer import ResultWriter

ORIGINAL_MARKER = "original"


def make_report_dir(path: Path) -> Path:
    path.mkdir()
    write_test_structure_element(str(path), build_tree())
    (path / "project.json").write_text(json.dumps({"name": ORIGINAL_MARKER}))
    (path / "manifest.json").write_text("{}")
    return path


def make_report_zip(path: Path) -> Path:
    source = make_report_dir(path.parent / "source_for_zip")
    with zipfile.ZipFile(path, "w") as archive:
        for file in source.iterdir():
            archive.write(file, file.name)
    return path


def config(**overrides) -> Configuration:
    return Configuration.from_dict({"merge-protocol": False, **overrides})


def run_fetch_results(report, target, cfg=None, listener_uid=None):
    output_xml = report.parent / "output.xml"
    output_xml.write_text("<robot/>")
    writer = ResultWriter(
        str(report), target and str(target), cfg or config(), str(output_xml), listener_uid
    )
    writer.end_result(None)
    return writer


def zip_names(path: Path) -> set[str]:
    with zipfile.ZipFile(path) as archive:
        return set(archive.namelist())


@pytest.fixture(autouse=True)
def run_in_tmp_path(tmp_path, monkeypatch):
    # The writer creates its temporary directories in the current working directory.
    monkeypatch.chdir(tmp_path)


def leftovers(directory: Path) -> set[str]:
    return {entry.name for entry in directory.iterdir() if entry.name.startswith("tmp")}


class ZipToTargetTests:
    def test_zip_to_zip(self, tmp_path):
        report = make_report_zip(tmp_path / "report.zip")
        run_fetch_results(report, tmp_path / "result.zip")
        assert "protocol.json" in zip_names(tmp_path / "result.zip")
        assert zip_names(report) == zip_names(tmp_path / "report.zip")
        assert not (tmp_path / "report").exists()
        assert not leftovers(tmp_path)

    def test_zip_to_directory(self, tmp_path):
        report = make_report_zip(tmp_path / "report.zip")
        run_fetch_results(report, tmp_path / "result")
        assert (tmp_path / "result" / "protocol.json").exists()
        assert (tmp_path / "result" / "project.json").exists()
        assert not (tmp_path / "report").exists()
        assert not leftovers(tmp_path)

    def test_zip_in_place_overwrites_the_zip(self, tmp_path):
        report = make_report_zip(tmp_path / "report.zip")
        assert "protocol.json" not in zip_names(report)
        run_fetch_results(report, None)
        assert "protocol.json" in zip_names(report)
        assert not (tmp_path / "report").exists()
        assert not leftovers(tmp_path)


class DirectoryToTargetTests:
    def test_directory_to_zip(self, tmp_path):
        report = make_report_dir(tmp_path / "report")
        run_fetch_results(report, tmp_path / "result.zip")
        assert "protocol.json" in zip_names(tmp_path / "result.zip")
        assert not (report / "protocol.json").exists()
        assert not leftovers(tmp_path)

    def test_directory_to_directory(self, tmp_path):
        report = make_report_dir(tmp_path / "report")
        run_fetch_results(report, tmp_path / "result")
        assert (tmp_path / "result" / "protocol.json").exists()
        assert not (report / "protocol.json").exists()
        assert not leftovers(tmp_path)

    def test_directory_in_place_updates_the_directory(self, tmp_path):
        report = make_report_dir(tmp_path / "report")
        run_fetch_results(report, None)
        assert (report / "protocol.json").exists()
        assert not (tmp_path / "report.zip").exists()
        assert not leftovers(tmp_path)


class KeepExtractedReportTests:
    def test_extracted_zip_stays_next_to_it(self, tmp_path):
        report = make_report_zip(tmp_path / "report.zip")
        run_fetch_results(
            report, tmp_path / "result.zip", config(**{"keep-extracted-report": True})
        )
        assert (tmp_path / "report" / "project.json").exists()
        assert not leftovers(tmp_path)

    def test_in_place_with_kept_extraction(self, tmp_path):
        report = make_report_zip(tmp_path / "report.zip")
        run_fetch_results(report, None, config(**{"keep-extracted-report": True}))
        assert "protocol.json" in zip_names(report)
        assert (tmp_path / "report" / "protocol.json").exists()


class ListenerModeTests:
    def test_partial_zip_per_suite_and_source_survives_until_the_end(self, tmp_path):
        # TestBenchMiniCI feeds a directory holding one test case set and asks for
        # '<uid>.zip'; after every suite a partial ZIP with the protocol is written.
        report = make_report_dir(tmp_path / "report")
        run_fetch_results(report, tmp_path / "out" / "itb-TC-1.zip", listener_uid="itb-TC-1")
        assert "protocol.json" in zip_names(tmp_path / "out" / "itb-TC-1.zip")
        writer_before_end = ResultWriter(
            str(report),
            str(tmp_path / "out2" / "itb-TC-1.zip"),
            config(),
            str(report.parent / "output.xml"),
            "itb-TC-1",
        )
        writer_before_end.write_listener_mode_protocols()
        assert {"protocol.json", "project.json"} <= zip_names(tmp_path / "out2" / "itb-TC-1.zip")
        assert json.loads(
            zipfile.ZipFile(tmp_path / "out2" / "itb-TC-1.zip").read("project.json")
        ) == {"name": ORIGINAL_MARKER}
        writer_before_end.end_result(None)
        assert not leftovers(tmp_path)


def test_source_is_released_when_there_is_no_structure_tree(tmp_path):
    report = tmp_path / "report.zip"
    with zipfile.ZipFile(report, "w") as archive:
        archive.writestr("manifest.json", "{}")
    run_fetch_results(report, tmp_path / "result.zip")
    assert {entry.name for entry in tmp_path.iterdir()} == {"output.xml", "report.zip"}
