"""Exporting the attachments of a TestBench report next to the generated suites.

The report keeps every attached file below 'attachments/': representatives of
reference data types under 'representatives/DT-<key>/', files of test case sets
and test cases directly in the folder, and whatever else a TestBench extension
put there. The whole folder is copied - the library does not know all consumers.
"""

from __future__ import annotations

import posixpath
import shutil
from dataclasses import dataclass
from pathlib import Path, PurePath

from .config import Configuration
from .log import logger
from .utils import get_generation_directory, resolve_root_placeholder

REPORT_ATTACHMENTS_DIR = "attachments"


@dataclass(frozen=True)
class AttachmentsExport:
    """Where the attachments go, and how the suites refer to that place."""

    target: Path
    # Set when 'attachments-directory' is a relative path: the target lies inside the
    # output directory and suites address it relative to themselves, so the whole
    # output directory stays movable. None for an absolute target.
    relative_to_output: PurePath | None


def attachments_export(config: Configuration) -> AttachmentsExport | None:
    if not config.attachments_directory:
        return None
    given = Path(resolve_root_placeholder(config.attachments_directory))
    if given.is_absolute():
        return AttachmentsExport(given, None)
    output_directory = get_generation_directory(config.output_directory)
    return AttachmentsExport(output_directory.with_suffix("") / given, PurePath(given))


def variable_value(export: AttachmentsExport, suite_directory: PurePath) -> str:
    """The value the attachments variable gets in a suite lying in 'suite_directory'.

    'suite_directory' is relative to the output directory. Forward slashes
    throughout; Robot Framework and Python accept them on every platform.
    """
    if export.relative_to_output is None:
        return export.target.as_posix()
    relative = posixpath.relpath(export.relative_to_output.as_posix(), suite_directory.as_posix())
    return f"${{CURDIR}}/{relative}"


def copy_attachments(report_directory: Path, target: Path) -> None:
    """Copies the report's attachments folder to 'target', replacing what is there."""
    if target.exists():
        shutil.rmtree(target)
    source = report_directory / REPORT_ATTACHMENTS_DIR
    if not source.is_dir():
        logger.debug(f"The report has no '{REPORT_ATTACHMENTS_DIR}' folder.")
        target.mkdir(parents=True)
        return
    shutil.copytree(source, target)
    logger.info(f"Attachments copied to {target}.")
