import shutil
import sys
from pathlib import Path
from typing import Optional
from urllib.parse import unquote

from .config import AttachmentConflictBehaviour, ReferenceBehaviour
from .log import logger
from .model import ReferenceAssignment, ReferenceKind

FILE_URI_SCHEME = "file://"
MEGABYTE = 1000 * 1000


class ExecutionArtifactStorage:
    def __init__(
        self,
        reference_behaviour: ReferenceBehaviour,
        attachment_conflict_behaviour: AttachmentConflictBehaviour,
        tb_references: list[ReferenceAssignment],
        output_xml: str,
        attachment_folder: str,
    ):
        self.reference_behaviour = reference_behaviour
        self.attachmentConflictBehaviour = attachment_conflict_behaviour
        self.tb_references: list[ReferenceAssignment] = tb_references
        self.output_xml = output_xml
        self.attachment_folder = attachment_folder
        self._key: Optional[int] = None

    def add_artifact(self, artifact: str) -> Optional[str]:
        """
        Adds an artifact to the storage based on the reference behaviour.

        :param artifact: The artifact to add.
        :type artifact: str
        :return: The key of the added artifact or None if it could not be added.
        :rtype: Optional[str]
        """
        artifact_value = self._dispatch_artifact_processing(artifact)
        if not artifact_value:
            return None
        existing_artifact = self._get_existing_artifact(artifact_value, self.reference_behaviour)
        if existing_artifact:
            # if self.reference_behaviour == ReferenceBehaviour.ATTACHMENT:
            #     self._handle_attachment_conflict(existing_artifact, artifact_value)
            return existing_artifact.key
        return self._add_new_reference(artifact_value, self.reference_behaviour)

    @property
    def new_key(self) -> int:
        if self._key is not None:
            self._key -= 1
            return self._key
        if not self.tb_references:
            self._key = -4
            return self._key
        min_key = min([int(ref.key) for ref in self.tb_references])
        starting_key_new_references = -3
        self._key = (
            min_key if min_key < starting_key_new_references else starting_key_new_references
        )
        self._key -= 1
        return self._key

    def _create_unique_attachment_path(self, attachement_path: Path) -> Path:
        counter = 1
        attachment_stem = attachement_path.stem
        while attachement_path.exists():
            attachement_path = Path(
                f"{attachement_path.parent}",
                f"{attachment_stem}_{counter}{attachement_path.suffix}",
            )
            counter += 1
        return attachement_path

    def _dispatch_attachment_copy(
        self, filename: str, artifact_value: str, attachment_folder_path: Path
    ) -> str:
        conflict_methods = {
            AttachmentConflictBehaviour.USE_NEW: (
                self._use_new_attachment,
                [filename, artifact_value, attachment_folder_path],
            ),
            AttachmentConflictBehaviour.RENAME_NEW: (
                self._rename_new_attachment,
                [filename, artifact_value, attachment_folder_path],
            ),
            AttachmentConflictBehaviour.USE_EXISTING: (self._use_existing_attachment, [filename]),
            AttachmentConflictBehaviour.ERROR: (self._log_attachment_error, [filename]),
        }
        method, args = conflict_methods.get(
            self.attachmentConflictBehaviour, (self._invalid_conflict_behaviour, [])
        )
        return method(*args)

    def _use_new_attachment(
        self, filename: str, artifact_value: str, attachment_folder_path: Path
    ) -> str:
        shutil.copyfile(artifact_value, attachment_folder_path / filename, follow_symlinks=True)
        return filename

    def _rename_new_attachment(
        self, filename: str, artifact_value: str, attachment_folder_path: Path
    ) -> str:
        unique_path = self._create_unique_attachment_path(attachment_folder_path / filename)
        unique_file = Path(unique_path).name
        logger.info(
            f"Attachment '{filename}' does already exist. "
            f"Creating new unique attachment '{unique_file}'."
        )
        shutil.copyfile(artifact_value, unique_path, follow_symlinks=True)
        return unique_file

    def _use_existing_attachment(self, filename: str) -> str:
        return filename

    def _log_attachment_error(self, filename: str):
        logger.error(f"Attachment '{filename}' does already exist.")
        return filename

    def _invalid_conflict_behaviour(self, filename: str):
        logger.error(
            f"Attachment conflict behaviour '{self.attachment_conflict_behaviour}' "
            f"is not valid value. Please consult the documentation."
        )
        sys.exit()

    def _copy_attachment(self, artifact_value: str) -> str:
        filename = Path(artifact_value).name
        attachment_folder_path = Path(self.attachment_folder)
        if not attachment_folder_path.exists():
            attachment_folder_path.mkdir(parents=True, exist_ok=True)
        if not (attachment_folder_path / filename).exists():
            return self._use_new_attachment(filename, artifact_value, attachment_folder_path)
        return self._dispatch_attachment_copy(filename, artifact_value, attachment_folder_path)

    def _process_artifact(self, artifact: str) -> Optional[str]:
        artifact_info = ExecutionArtifactInfo(artifact, self.output_xml)
        artifact_value = artifact_info.get_attachment_value()
        if not artifact_value:
            logger.warning(
                f"Attachment '{artifact}' does not exist or can not be handled as an attachment."
            )
            return None
        if not has_allowed_size(artifact_value):
            logger.error(
                f"Attachment '{artifact_value}' exceeds the maximum allowed size of 10 MB."
            )
            return None
        return self._copy_attachment(artifact_value)

    def _process_reference(self, artifact: str) -> Optional[str]:
        artifact_info = ExecutionArtifactInfo(artifact, self.output_xml)
        artifact_value = artifact_info.get_reference_value()
        if not artifact_value:
            logger.warning(
                f"Reference '{artifact}' does not exist or can not be handled as a reference."
            )
            return None
        return artifact_value

    def _process_unknown(self, artifact: str) -> Optional[str]:
        logger.error(
            f"Unknown reference behaviour '{self.reference_behaviour}'."
            f"Cannot add artifact '{artifact}'."
        )
        return None

    def _process_no_references_allowed(self, artifact: str) -> Optional[str]:
        logger.warning(
            f"Reference behaviour is set to NONE."
            f"Reference '{artifact}' will not be added to report."
        )
        return None

    def _dispatch_artifact_processing(self, artifact):
        artifact_processing_methods = {
            ReferenceBehaviour.NONE: self._process_no_references_allowed,
            ReferenceBehaviour.ATTACHMENT: self._process_artifact,
            ReferenceBehaviour.REFERENCE: self._process_reference,
        }
        return artifact_processing_methods.get(self.reference_behaviour, self._process_unknown)(
            artifact
        )

    def _add_new_reference(self, artifact_value: str, reference_behaviour: ReferenceBehaviour):
        new_key = str(self.new_key)
        self.tb_references.append(
            ReferenceAssignment(
                key=new_key,
                value=artifact_value,
                referenceType=ReferenceKind(reference_behaviour.capitalize()),
            )
        )
        return new_key

    def _get_existing_artifact(self, artifact_value: str, reference_behaviour: ReferenceBehaviour):
        return next(
            filter(
                lambda ref: ref.value == artifact_value
                and ref.referenceType.value.lower() == reference_behaviour.lower(),
                self.tb_references,
            ),
            None,
        )


class ExecutionArtifactInfo:
    def __init__(self, artifact: str, output_xml: str) -> None:
        unquoted_artifact = unquote(artifact)
        if unquoted_artifact.startswith(FILE_URI_SCHEME):
            unquoted_artifact = unquoted_artifact[len(FILE_URI_SCHEME) :]
        self.artifact = unquoted_artifact
        self.output_xml = output_xml

    def get_reference_value(self) -> Optional[str]:
        unquoted_path = Path(self.artifact)
        if not unquoted_path.exists():
            robot_output_dir = Path(self.output_xml).parent
            if Path(robot_output_dir, unquoted_path).exists():
                unquoted_path = robot_output_dir / unquoted_path
                unquoted_path = unquoted_path.resolve()
            elif unquoted_path.is_absolute():
                logger.warning(
                    f"Referenced file '{unquoted_path}' does not exist."
                    f"Reference will be attached anyway."
                )
            else:
                return None
        return str(unquoted_path)

    def get_attachment_value(self) -> Optional[str]:
        unquoted_path = Path(self.artifact)
        if not unquoted_path.exists():
            robot_output_dir = Path(self.output_xml).parent
            if not Path(robot_output_dir, unquoted_path).exists():
                return None
            unquoted_path = robot_output_dir / unquoted_path
        return str(unquoted_path)


def has_allowed_size(file: str) -> bool:
    file_size = Path.stat(Path(file)).st_size
    return not file_size >= 10 * MEGABYTE
