import json

import pytest

from testbench2robotframework.utils import perform_version_check


def write_manifest(directory, manifest):
    (directory / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return directory


def test_supported_format_version_from_newer_server_is_accepted(tmp_path):
    report = write_manifest(
        tmp_path, {"formatVersion": "1.0", "serverVersions": {"version": "4.2.02"}}
    )

    perform_version_check(report)


def test_unsupported_format_version_is_rejected(tmp_path):
    report = write_manifest(
        tmp_path, {"formatVersion": "2.0", "serverVersions": {"version": "4.1.02"}}
    )

    with pytest.raises(SystemExit, match=r"'2.0'"):
        perform_version_check(report)


def test_missing_format_version_is_rejected(tmp_path):
    report = write_manifest(tmp_path, {"serverVersions": {"version": "4.1.02"}})

    with pytest.raises(SystemExit, match="Could not read"):
        perform_version_check(report)
