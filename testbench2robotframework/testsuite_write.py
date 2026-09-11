import os
import re
import shutil
import tempfile
from pathlib import Path

from robot.parsing.model.blocks import File

from .config import CleanMode, Configuration
from .log import logger
from .utils import directory_to_zip


def write_test_suites(test_suites: dict[str, File], config: Configuration) -> None:
    generation_directory = get_generation_directory(config.output_directory)
    if config.clean:
        if config.clean_mode is CleanMode.ALL:
            wipe_generation_directory(generation_directory)
        else:
            clear_generation_directory(generation_directory)
    if generation_directory.suffix.lower() != ".zip":
        write_test_suite_files(test_suites, generation_directory)
        if config.create_output_zip:
            directory_to_zip(generation_directory)
    else:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp_dir:
            write_test_suite_files(test_suites, Path(temp_dir))
            directory_to_zip(Path(temp_dir), str(generation_directory.with_suffix("")))
    logger.info(
        f"Successfully generated {len(test_suites)} Robot Framework test suites "
        f"in the following directory: {Path(generation_directory).resolve()!s}"
    )


def get_generation_directory(generation_directory: str) -> Path:
    root_path = Path(os.curdir).absolute()
    if not generation_directory:
        return root_path / "Generated"
    return Path(
        re.sub(
            r"^{root}",
            str(root_path).replace("\\", "\\\\"),
            generation_directory,
            flags=re.IGNORECASE,
        )
    )


def wipe_generation_directory(generation_dir: Path) -> None:
    """Removes the whole output directory - 'clean-mode = "ALL"' only.

    This is the pre-1.2 behaviour: everything below the directory is deleted,
    also files this tool did not write. Deliberately a configuration-file-only
    option without a CLI flag.
    """
    if generation_dir.is_dir():
        shutil.rmtree(str(generation_dir))
        logger.debug("Generation directory has been wiped.")
    elif generation_dir.suffix.lower() == ".zip":
        generation_dir.unlink(missing_ok=True)


# Every generated suite and __init__.robot carries this line in its settings.
GENERATED_SUITE_MARKER = re.compile(r"^Metadata\s{2,}UniqueID\s{2,}\S+", re.MULTILINE)


def is_generated_suite(robot_file: Path) -> bool:
    """Whether a .robot file was written by testbench2robotframework.

    Generated files always start with a settings section containing
    'Metadata    UniqueID    <uid>', so reading the head of the file suffices.
    """
    try:
        with robot_file.open(encoding="utf-8", errors="ignore") as handle:
            head = handle.read(4096)
    except OSError:
        return False
    return bool(GENERATED_SUITE_MARKER.search(head))


def clear_generation_directory(generation_dir: Path) -> None:
    """Removes previously generated suites - and nothing else.

    Only .robot files identified by 'is_generated_suite' are deleted, plus the
    directories that become empty by that. Files the tool did not write - hand
    written suites, resource files, notes - survive a clean. A .zip target is
    removed as a whole, since it only ever contains generated content.
    """
    if generation_dir.suffix.lower() == ".zip":
        generation_dir.unlink(missing_ok=True)
        return
    if not generation_dir.is_dir():
        return
    parents = set()
    removed = 0
    for robot_file in generation_dir.rglob("*.robot"):
        if is_generated_suite(robot_file):
            robot_file.unlink()
            parents.add(robot_file.parent)
            removed += 1
    for parent in sorted(parents, key=lambda path: len(path.parts), reverse=True):
        current = parent
        while current != generation_dir and current.is_dir() and not any(current.iterdir()):
            current.rmdir()
            current = current.parent
    if removed:
        logger.debug(f"Removed {removed} previously generated suite files.")


def write_test_suite_files(test_suites: dict[str, File], generation_directory: Path) -> None:
    for test_suite_file in test_suites.values():
        test_suite_file.source = Path(generation_directory / f"{test_suite_file.source}.robot")
        test_suite_file.save()
        logger.debug(f"File written to {os.path.relpath(test_suite_file.source)}")
