"""How a TestBench report is opened for reading.

A directory is used as it is. A ZIP is extracted - to a temporary directory that
is removed on close, or, with 'keep-extracted-report', to a directory of the same
name next to the ZIP that stays.
"""

import zipfile

import pytest

from testbench2robotframework.utils import open_report


@pytest.fixture
def report_zip(tmp_path):
    path = tmp_path / "report.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("cycle_structure.json", "{}")
        archive.writestr("attachments/a.txt", "a")
    return path


def test_directory_is_used_in_place(tmp_path):
    (tmp_path / "cycle_structure.json").write_text("{}")
    with open_report(tmp_path) as report:
        assert report.directory == tmp_path.resolve()
    assert (tmp_path / "cycle_structure.json").exists()


def test_zip_is_extracted_to_a_temporary_directory_that_is_removed(report_zip):
    with open_report(report_zip) as report:
        directory = report.directory
        assert (directory / "cycle_structure.json").exists()
        assert (directory / "attachments" / "a.txt").exists()
        assert directory.parent != report_zip.parent
    assert not directory.exists()
    assert not (report_zip.parent / "report").exists()


def test_zip_is_kept_next_to_it_when_asked(report_zip):
    with open_report(report_zip, keep_extracted=True) as report:
        assert report.directory == (report_zip.parent / "report").resolve()
    assert (report_zip.parent / "report" / "cycle_structure.json").exists()


def test_kept_directory_replaces_a_previous_extraction(report_zip):
    stale = report_zip.parent / "report"
    stale.mkdir()
    (stale / "stale.json").write_text("{}")
    with open_report(report_zip, keep_extracted=True):
        pass
    assert not (stale / "stale.json").exists()
    assert (stale / "cycle_structure.json").exists()


def test_close_is_idempotent(report_zip):
    report = open_report(report_zip)
    report.close()
    report.close()


def test_neither_zip_nor_directory_exits(tmp_path):
    other = tmp_path / "report.json"
    other.write_text("{}")
    with pytest.raises(SystemExit):
        open_report(other)
