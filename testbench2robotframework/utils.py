import argparse
import os
import re
import shutil
import sys
from pathlib import Path, PurePath
from typing import Dict, Optional, Tuple
from zipfile import ZipFile

from testbench2robotframework.model import (
    TestStructureTree,
    TestStructureTreeNode,
    TestStructureTreeNodeType,
)

CONVERTER_DESCRIPTION = """tB2Robot converts TestBench JSON report to Robot Framework Code
                        and Robot Result Model to JSON full report."""
WRITE_SUBPARSER_HELP = """Command to convert TestBench´s JSON REPORT to Robot Framework Code."""
READ_SUBPARSER_HELP = """Command to read a robot output xml file and
write the results to a TestBench JSON REPORT."""
JSON_PATH_ARGUMENT_HELP = "Path to a ZIP file or directory containing TestBenchs JSON report files."
CONFIG_ARGUMENT_HELP = """Path to a config json file to generate robot files
                        based on the given configuration.
                        If no path is given testbench2robot will search for a file
                        named \"config.json\" in the current working directory."""
ROBOT_OUTPUT_HELP = """Path to an XML file containing the robot results."""
ROBOT_RESULT_HELP = """Path to the directory or ZIP File the TestBench JSON reports
with result should be saved to."""


arg_parser = argparse.ArgumentParser(description=CONVERTER_DESCRIPTION)
arg_parser.add_argument(
    '--version',
    '--info',
    action='store_true',
    help='Writes the TestBench2RobotFramework, Robot Framework and Python version to console.',
)
subparsers = arg_parser.add_subparsers(dest="subcommand")

write_parser = subparsers.add_parser("write", help=WRITE_SUBPARSER_HELP)
write_parser.add_argument(
    "-c",
    "--config",
    help=CONFIG_ARGUMENT_HELP,
    type=str,
    required=False,
    default=os.path.join(os.path.abspath(os.curdir), "config.json"),
)

write_parser.add_argument("jsonReport", nargs=1, type=str, help=JSON_PATH_ARGUMENT_HELP)

read_parser = subparsers.add_parser("read", help=READ_SUBPARSER_HELP)
read_parser.add_argument(
    "-c",
    "--config",
    help=CONFIG_ARGUMENT_HELP,
    type=str,
    required=False,
    default=os.path.join(os.path.abspath(os.curdir), "config.json"),
)
read_parser.add_argument(
    "-r",
    "--result",
    help=ROBOT_RESULT_HELP,
    type=str,
    required=False,
)
required_named_arguments = read_parser.add_argument_group('required named arguments')
required_named_arguments.add_argument(
    "-o", "--output", help=ROBOT_OUTPUT_HELP, type=str, required=True
)

read_parser.add_argument("jsonReport", nargs=1, type=str, help=JSON_PATH_ARGUMENT_HELP)


class PathResolver:
    def __init__(
        self,
        test_theme_tree: TestStructureTree,
        uids_of_existing_tcs: Tuple[str, ...],
        log_suite_numbers: bool,
    ):
        self.tcs_catalog: Dict[str, TestStructureTreeNode] = {}
        self.tt_catalog: Dict[str, TestStructureTreeNode] = {}
        self.tree_dict: Dict[str, TestStructureTreeNode] = {}
        self._last_child_indices: Dict[str, int] = {}
        self._log_suite_numbers = log_suite_numbers
        self._uids_of_existing_tcs = uids_of_existing_tcs
        self._analyze_tree(test_theme_tree)
        self.tcs_paths = self._get_paths(self.tcs_catalog)
        self.tt_paths = self._get_paths(self.tt_catalog)

    def _analyze_tree(self, test_theme_tree: TestStructureTree):
        self.tree_dict[test_theme_tree.root.baseInformation.key] = test_theme_tree.root
        for tse in test_theme_tree.nodes:
            self._add_existing_tcs_to_catalog(tse)
            self.tree_dict[tse.baseInformation.key] = tse
            self._store_highest_child_index(tse)

    def _store_highest_child_index(self, tse):
        self._last_child_indices[tse.baseInformation.parentKey] = max(
            int(get_tse_index(tse)),
            self._last_child_indices.get(tse.baseInformation.parentKey, 0),
        )

    def _add_existing_tcs_to_catalog(self, tse):
        if (
            tse.elementType == TestStructureTreeNodeType.TestCaseSet
            and tse.baseInformation.uniqueID in self._uids_of_existing_tcs
        ):
            self.tcs_catalog[tse.baseInformation.uniqueID] = tse

    def _get_paths(self, tse_catalog: Dict[str, TestStructureTreeNode]) -> Dict[str, PurePath]:
        return {uid: self._resolve_tse_path(tse) for uid, tse in tse_catalog.items()}

    def _resolve_tse_path(self, tse: TestStructureTreeNode) -> PurePath:
        self._add_tt_to_tt_catalog(tse)
        if tse.elementType == TestStructureTreeNodeType.Root:
            return PurePath()
        tse_name = replace_invalid_characters(tse.baseInformation.name)
        if tse.baseInformation.parentKey not in self.tree_dict:
            return PurePath(f"{self._file_prefix(tse)}{tse_name}")
        parent_path = self._resolve_tse_path(self.tree_dict[tse.baseInformation.parentKey])
        return parent_path / f"{self._file_prefix(tse)}{tse_name}"

    def _add_tt_to_tt_catalog(self, tse):
        if (
            tse.elementType == TestStructureTreeNodeType.TestTheme
            and tse.baseInformation.uniqueID not in self.tt_catalog
        ):
            self.tt_catalog[tse.baseInformation.uniqueID] = tse

    def _file_prefix(self, tse) -> str:
        prefix_separator = '_' * self._log_suite_numbers
        return f"{self._get_padded_index(tse)}_{prefix_separator}"

    def _get_padded_index(self, tse) -> str:
        index = get_tse_index(tse)
        max_length = len(str(self._last_child_indices[tse.baseInformation.parentKey]))
        return index.zfill(max_length)


def get_directory(json_report_path: Optional[str]) -> str:
    if json_report_path is None:
        return ""
    if not os.path.exists(json_report_path):
        sys.exit("Error opening " + json_report_path + ". Path does not exist.")
    if os.path.isdir(json_report_path):
        return os.path.abspath(json_report_path)
    filename, ext = os.path.splitext(json_report_path)
    if ext.lower() == ".zip":
        with ZipFile(json_report_path, 'r') as zip_ref:
            zip_ref.extractall(filename)
        return os.path.abspath(filename)
    sys.exit("Error opening " + json_report_path + ". File is not a ZIP file.")


def ensure_dir_exists(cli_output_dir):
    if not Path(cli_output_dir).is_dir():
        Path(cli_output_dir).mkdir(parents=True, exist_ok=True)


def replace_invalid_characters(name: str) -> str:
    return re.sub(r'[<>:"/\\|?* ]', "_", name)


def get_tse_index(tse: TestStructureTreeNode) -> str:
    return tse.baseInformation.numbering.rsplit(".", 1)[-1]


def directory_to_zip(directory: Path, new_path: str = None):
    if new_path:
        shutil.make_archive(str(new_path), 'zip', str(directory))
    else:
        shutil.make_archive(str(directory), 'zip', str(directory))


def get_list_item(liste, index, default: Optional[str]):
    try:
        item = liste[index]
        return item
    except IndexError:
        return default
