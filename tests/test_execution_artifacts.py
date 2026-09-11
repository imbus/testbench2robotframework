"""How 'itb-reference:' values in a test message are resolved to files.

A value without a scheme is a relative reference and is resolved against the
directory of the output.xml. A 'file:' URI is always absolute (RFC 8089), so
'file:///x.zip' means the file system root - never the output directory.
"""

import pytest

from testbench2robotframework.config import AttachmentConflictBehaviour, ReferenceBehaviour
from testbench2robotframework.execution_artifacts import (
    ExecutionArtifactInfo,
    ExecutionArtifactStorage,
)
from testbench2robotframework.model import ReferenceAssignment, ReferenceKind


@pytest.fixture
def output_dir(tmp_path):
    results = tmp_path / "Results"
    results.mkdir()
    (results / "output.xml").write_text("<robot/>")
    (results / "prozess_1.zip").write_bytes(b"zip")
    return results


def storage(output_dir, behaviour=ReferenceBehaviour.ATTACHMENT):
    return ExecutionArtifactStorage(
        behaviour,
        AttachmentConflictBehaviour.USE_EXISTING,
        [],
        str(output_dir / "output.xml"),
        str(output_dir.parent / "attachments"),
    )


class RelativeReferenceTests:
    def test_is_resolved_against_output_xml_directory(self, output_dir):
        info = ExecutionArtifactInfo("prozess_1.zip", str(output_dir / "output.xml"))
        assert info.get_attachment_value() == str(output_dir / "prozess_1.zip")

    def test_is_attached_and_copied_into_attachment_folder(self, output_dir):
        artifact_storage = storage(output_dir)
        key = artifact_storage.add_artifact("prozess_1.zip")
        assert key == "-4"
        assert (output_dir.parent / "attachments" / "prozess_1.zip").read_bytes() == b"zip"
        # TestBench addresses attachments by their path inside the report.
        assert artifact_storage.tb_references[0].value == "attachments/prozess_1.zip"

    def test_reference_already_in_report_is_reused(self, output_dir):
        artifact_storage = storage(output_dir)
        artifact_storage.tb_references.append(
            ReferenceAssignment(
                key="647138",
                value="attachments/prozess_1.zip",
                referenceType=ReferenceKind.Attachment,
            )
        )
        assert artifact_storage.add_artifact("prozess_1.zip") == "647138"
        assert len(artifact_storage.tb_references) == 1

    def test_renamed_attachment_keeps_folder_prefix(self, output_dir):
        artifact_storage = ExecutionArtifactStorage(
            ReferenceBehaviour.ATTACHMENT,
            AttachmentConflictBehaviour.RENAME_NEW,
            [],
            str(output_dir / "output.xml"),
            str(output_dir.parent / "attachments"),
        )
        (output_dir.parent / "attachments").mkdir()
        (output_dir.parent / "attachments" / "prozess_1.zip").write_bytes(b"old")
        artifact_storage.add_artifact("prozess_1.zip")
        assert artifact_storage.tb_references[0].value == "attachments/prozess_1_1.zip"

    def test_missing_relative_file_is_not_attached(self, output_dir):
        assert storage(output_dir).add_artifact("missing.zip") is None


class FileUriTests:
    def test_three_slashes_is_absolute_from_root(self, output_dir):
        info = ExecutionArtifactInfo("file:///prozess_1.zip", str(output_dir / "output.xml"))
        assert info.artifact == "/prozess_1.zip"
        # The file lives in the output directory, but an absolute URI never
        # points there - so it is not found.
        assert info.get_attachment_value() is None

    def test_absolute_uri_to_existing_file(self, output_dir):
        info = ExecutionArtifactInfo(
            f"file://{output_dir / 'prozess_1.zip'}", str(output_dir / "output.xml")
        )
        assert info.get_attachment_value() == str(output_dir / "prozess_1.zip")

    def test_percent_encoding_is_unquoted(self, output_dir):
        (output_dir / "my file.zip").write_bytes(b"zip")
        info = ExecutionArtifactInfo("my%20file.zip", str(output_dir / "output.xml"))
        assert info.get_attachment_value() == str(output_dir / "my file.zip")
