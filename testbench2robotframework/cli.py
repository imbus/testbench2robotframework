from pathlib import Path
from typing import Any

import click
import robot.version

from testbench2robotframework import __version__
from testbench2robotframework.robotframework2testbench import robot2testbench

from .config import (
    DEFAULT_GENERATION_DIRECTORY,
    DEFAULT_LIBRARY_REGEX,
    DEFAULT_LIBRARY_ROOTS,
    DEFAULT_RESOURCE_DIRECTORY_REGEX,
    DEFAULT_RESOURCE_REGEX,
    DEFAULT_RESOURCE_ROOTS,
    find_private_robot_toml,
    find_pyproject_toml,
    find_robot_toml,
    get_testbench2robotframework_toml_dict,
)
from .json_reader import read_json
from .testbench2robotframework import testbench2robotframework
from .utils import ALLOWED_SERVER_VERSIONS

TESTBENCH2ROBOTFRAMEWORK_DESCRIPTION = (
    """TestBench2RobotFramework converts a TestBench JSON report into Robot Framework
    test suites and writes the execution results provided by Robot Framework back into
    the TestBench report. The TestBench version your report was generated with must be
    compatible with the version of testbench2robotframework you are using.
    This version supports TestBench """
    + ", ".join(ALLOWED_SERVER_VERSIONS)
    + "."
)
GENERATE_HELP = """Converts a TestBench JSON report into Robot Framework test suites."""
FETCH_HELP = """Reads execution results from a Robot Framework result XML and writes
them into a TestBench JSON report."""
CONFIG_OPTION_HELP = """Path to a configuration file for TestBench2RobotFramework.
    """
ROBOT_RESULT_HELP = """Path to the XML file containing the Robot Framework results."""
ROBOT_OUTPUT_HELP = """Directory or ZIP file the TestBench JSON report with the
    results is written to."""


def parse_subdivision_mapping(
    ctx: click.Context, param: click.Option, values: tuple[str, ...]
) -> dict[str, Any]:
    subdivision_mapping = {}
    for value in values:
        try:
            subdivision, import_value = value.split(":", 1)
            subdivision_mapping[subdivision] = import_value
        except ValueError as err:
            raise click.BadParameter(f"Mapping '{value}' is not in 'name:value' format.") from err
    return subdivision_mapping


@click.group(help=TESTBENCH2ROBOTFRAMEWORK_DESCRIPTION)
@click.version_option(
    __version__,
    "-v",
    "--version",
    help="Prints the TestBench2RobotFramework, Robot Framework and Python version.",
    message=(
        f"TestBench2RobotFramework {__version__} with "
        f"Robot Framework {robot.version.get_full_version()}. "
        f"Compatible with TestBench server versions: {', '.join(ALLOWED_SERVER_VERSIONS)}."
    ),
)
@click.help_option("-h", "--help")
def testbench2robotframework_cli():
    pass


@testbench2robotframework_cli.command(short_help=GENERATE_HELP)
@click.option("-c", "--config", type=click.Path(path_type=Path), help=CONFIG_OPTION_HELP)
@click.option(
    "--clean/--no-clean",
    default=None,
    help="""Whether previously generated suites are removed before generating.
    Without either flag the configuration decides (default: clean). Use
    --no-clean to generate additively.""",
)
@click.option(
    "--fully-qualified",
    is_flag=True,
    help="""Calls Robot Framework keywords by their fully
    qualified names in the generated test suites.""",
)
@click.option(
    "--include-blocked",
    is_flag=True,
    help="""Also generates test elements whose TestBench execution status
    is 'blocked'. By default blocked test cases, test case sets and
    test themes are skipped.""",
)
@click.option(
    "-d",
    "--output-directory",
    type=click.Path(path_type=Path),
    help="Directory or ZIP archive containing the generated test suites.",
)
@click.option(
    "--compound-keyword-logging",
    type=click.Choice(["GROUP", "COMMENT", "NONE"], case_sensitive=False),
    help="Mode for logging compound keywords.",
)
@click.option(
    "--log-suite-numbering", is_flag=True, help="Enables logging of the test suite numbering."
)
@click.option(
    "--resource-directory",
    type=click.Path(path_type=Path),
    help="Directory containing the Robot Framework resource files.",
)
@click.option(
    "--resource-directory-regex",
    type=str,
    help="""Regular expression identifying the TestBench subdivision that
    corresponds to the <resource-directory>. Resources are imported relative
    to that subdivision, following the test element structure in TestBench.""",
)
@click.option(
    "--library-regex",
    multiple=True,
    type=str,
    help="""Regular expression identifying TestBench subdivisions that correspond
    to Robot Framework libraries. The name to import must be marked by a named group
    ('resourceName', 'libraryName' or 'name') or by exactly one capture group.""",
)
@click.option(
    "--library-root",
    multiple=True,
    type=str,
    help="""TestBench root subdivision whose direct children
         correspond to Robot Framework libraries.""",
)
@click.option(
    "--metadata",
    multiple=True,
    callback=parse_subdivision_mapping,
    help="""Add extra metadata to the settings of every generated Robot Framework
        test suite. Provide entries as 'key:value' pairs. The names 'UniqueID',
        'Name' and 'Numbering' are reserved for the generated suite metadata.""",
)
@click.option(
    "--resource-regex",
    multiple=True,
    type=str,
    help="""Regular expression identifying TestBench subdivisions that correspond
    to Robot Framework resources. Same rules as for --library-regex.""",
)
@click.option(
    "--resource-root",
    multiple=True,
    type=str,
    help="""TestBench root subdivision whose direct children
        correspond to Robot Framework resources.""",
)
@click.option(
    "--library-mapping",
    multiple=True,
    callback=parse_subdivision_mapping,
    help="""Library import statement to use for keywords from the given
    TestBench subdivision. Provide entries as 'subdivision:import' pairs.""",
)
@click.option(
    "--resource-mapping",
    multiple=True,
    callback=parse_subdivision_mapping,
    help="""Resource import statement to use for keywords from the given
    TestBench subdivision. Provide entries as 'subdivision:import' pairs.""",
)
@click.argument("testbench-report", type=click.Path(path_type=Path))
def generate_tests(  # noqa: PLR0913
    clean: bool | None,
    compound_keyword_logging: str,
    config: Path,
    fully_qualified: bool,
    include_blocked: bool,
    library_regex: tuple[str],
    resource_directory_regex: str,
    library_root: tuple[str],
    log_suite_numbering: bool,
    metadata: dict[str, str],
    output_directory: Path,
    resource_directory: Path,
    resource_regex: tuple[str],
    resource_root: tuple[str],
    testbench_report: Path,
    library_mapping: dict[str, str],
    resource_mapping: dict[str, str],
):
    """
    Generates Robot Framework Testsuites from a <TestBench Report>.
    """
    configuration = get_tb2robot_file_configuration(config)
    if clean is not None:
        configuration["clean"] = clean
    if fully_qualified:
        configuration["fully-qualified"] = True
    else:
        configuration["fully-qualified"] = configuration.get("fully-qualified", False)
    if include_blocked:
        configuration["include-blocked"] = True
    else:
        configuration["include-blocked"] = configuration.get("include-blocked", False)
    configuration["output-directory"] = (
        output_directory.as_posix()
        if output_directory
        else configuration.get("output-directory", DEFAULT_GENERATION_DIRECTORY)
    )
    configuration["library-mapping"] = library_mapping or configuration.get("library-mapping", {})
    if log_suite_numbering:
        configuration["log-suite-numbering"] = True
    else:
        configuration["log-suite-numbering"] = configuration.get("log-suite-numbering", False)
    configuration["metadata"] = metadata or configuration.get("metadata", {})
    configuration["compound-keyword-logging"] = compound_keyword_logging or configuration.get(
        "compound-keyword-logging", "GROUP"
    )
    configuration["resource-directory"] = (
        resource_directory.as_posix()
        if resource_directory
        # No CLI-side default: Configuration.from_dict decides (empty string),
        # so the CLI and the library entry point generate identical suites.
        else configuration.get("resource-directory", "")
    )
    configuration["resource-directory-regex"] = resource_directory_regex or configuration.get(
        "resource-directory-regex", DEFAULT_RESOURCE_DIRECTORY_REGEX
    )
    configuration["resource-mapping"] = resource_mapping or configuration.get(
        "resource-mapping", {}
    )
    configuration["library-regex"] = list(library_regex) or configuration.get(
        "library-regex", [DEFAULT_LIBRARY_REGEX]
    )
    configuration["library-root"] = list(library_root) or configuration.get(
        "library-root", DEFAULT_LIBRARY_ROOTS
    )
    configuration["resource-regex"] = list(resource_regex) or configuration.get(
        "resource-regex", [DEFAULT_RESOURCE_REGEX]
    )
    configuration["resource-root"] = list(resource_root) or configuration.get(
        "resource-root", DEFAULT_RESOURCE_ROOTS
    )
    testbench2robotframework(testbench_report, configuration)


@testbench2robotframework_cli.command(short_help=FETCH_HELP)
@click.option("-c", "--config", type=click.Path(path_type=Path), help=CONFIG_OPTION_HELP)
@click.option("-d", "--output-directory", type=click.Path(path_type=Path), help=ROBOT_OUTPUT_HELP)
@click.option(
    "--no-merge-protocol",
    is_flag=True,
    help="""Overwrite the main protocol instead of merging the Robot Framework results
    into the protocol.json that is already part of the TestBench report.""",
)
@click.argument("robot-result", type=click.Path(path_type=Path))
@click.argument("testbench-report", type=click.Path(path_type=Path))
def fetch_results(
    config: Path,
    robot_result: Path,
    output_directory: Path,
    testbench_report: Path,
    no_merge_protocol: bool,
):
    """
    Fetch Robot Framework execution results from <output XML> and save to a <TestBench Report>.
    """
    configuration = get_tb2robot_file_configuration(config)
    if no_merge_protocol:
        configuration["merge-protocol"] = False
    else:
        configuration["merge-protocol"] = configuration.get("merge-protocol", True)
    robot2testbench(testbench_report, robot_result, output_directory, configuration)


def get_tb2robot_file_configuration(config: Path | None) -> Any:
    if not config:
        pyproject_toml = find_pyproject_toml()
        robot_toml = find_robot_toml()
        private_robot_toml = find_private_robot_toml()
        pyproject_config = get_testbench2robotframework_toml_dict(pyproject_toml)
        robot_config = get_testbench2robotframework_toml_dict(robot_toml)
        private_robot_config = get_testbench2robotframework_toml_dict(private_robot_toml)
        return {**pyproject_config, **robot_config, **private_robot_config}
    config_path = config
    if not config_path:
        return {}
    if config_path.suffix == ".json":
        return read_json(config, False)
    return get_testbench2robotframework_toml_dict(config_path)
