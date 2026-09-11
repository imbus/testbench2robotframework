from pathlib import Path

from .blocked_filter import filter_blocked
from .config import Configuration
from .json_reader import TestBenchJsonReader
from .log import logger, setup_logger
from .testbench2rf import create_test_suites
from .testsuite_write import write_test_suites
from .utils import PathResolver, open_report, perform_version_check


def testbench2robotframework(testbench_report: str | Path, config: dict | Configuration):
    perform_version_check(Path(testbench_report))
    configuration = Configuration.from_dict(config) if isinstance(config, dict) else config
    setup_logger(configuration)
    logger.debug("Configuration loaded.")
    with open_report(Path(testbench_report), configuration.keep_extracted_report) as report:
        reader = TestBenchJsonReader(report.directory)
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
        write_test_suites(test_suites, configuration, report.directory)
