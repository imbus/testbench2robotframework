import sys
import tempfile
from pathlib import Path

from .blocked_filter import filter_blocked
from .config import Configuration
from .json_reader import TestBenchJsonReader
from .log import logger, setup_logger
from .testbench2rf import create_test_suites
from .testsuite_write import write_test_suites
from .utils import (
    PathResolver,
    extract_to_working_directory,
    is_zip_file,
    perform_version_check,
)


def testbench2robotframework(testbench_report: str | Path, config: dict | Configuration):
    perform_version_check(Path(testbench_report))
    configuration = Configuration.from_dict(config) if isinstance(config, dict) else config
    setup_logger(configuration)
    logger.debug("Configuration loaded.")
    report_path = Path(testbench_report)
    temp_dir = None
    try:
        if is_zip_file(report_path):
            temp_dir = tempfile.TemporaryDirectory(dir=Path.cwd())
            working_dir = Path(temp_dir.name)
            extract_to_working_directory(report_path, working_dir)
        elif report_path.is_dir():
            working_dir = report_path.resolve()
        else:
            sys.exit(
                f"The given TestBench report '{report_path.as_posix()}' "
                f"is neither a ZIP file nor a directory."
            )
        reader = TestBenchJsonReader(Path(working_dir))
        test_case_set_catalog = reader.get_test_case_set_catalog()
        if not configuration.include_blocked:
            test_case_set_catalog, blocked_sets, blocked_cases = filter_blocked(
                test_case_set_catalog, reader.test_theme_tree
            )
            if blocked_sets or blocked_cases:
                logger.info(
                    f"Skipped {blocked_sets} blocked test case sets and "
                    f"{blocked_cases} blocked test cases. "
                    f"Use '--include-blocked' to generate them anyway."
                )
        path_resolver = PathResolver(
            reader.test_theme_tree,
            tuple(test_case_set_catalog.keys()),
            configuration.log_suite_numbering,
        )
        test_suites = create_test_suites(test_case_set_catalog, path_resolver, configuration)
        if not test_suites:
            logger.warning("The exported TestBench project contains no test suites.")
            return
        write_test_suites(test_suites, configuration)
    except Exception as exception:
        if temp_dir is not None:
            temp_dir.cleanup()
        raise exception
