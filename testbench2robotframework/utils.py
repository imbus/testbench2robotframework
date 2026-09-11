from __future__ import annotations

import ast
import json
import re
import shutil
import sys
import tempfile
from collections.abc import Mapping
from enum import Enum
from pathlib import Path, PurePath
from typing import Any
from zipfile import ZipFile

from testbench2robotframework.model import (
    RootNode,
    TestCaseNode,
    TestCaseSetNode,
    TestStructureTree,
    TestThemeNode,
    UDFType,
    UserDefinedField,
)

from .log import logger

# Nodes carrying a TestStructureItemBaseInformation, i.e. everything with a
# 'base.key'. A TestCaseNode has a TestCaseBaseInformation without a key and is
# registered under its 'spec.key' instead, so it needs a type of its own.
StructureNode = RootNode | TestThemeNode | TestCaseSetNode
TreeNode = StructureNode | TestCaseNode

ALLOWED_SERVER_VERSIONS = ["4.1"]
ERROR_COULD_NOT_READ_VERSION = (
    "Could not read TestBench report version. "
    "The report must be generated with one of the supported versions: "
    + ", ".join(ALLOWED_SERVER_VERSIONS)
)


def _get_error_incompatible_version_message(server_version: str) -> str:
    return (
        "The version of testbench2robotframework is not compatible with the "
        f"TestBench report version '{server_version}'. "
        f"Supported versions are: {', '.join(ALLOWED_SERVER_VERSIONS)}. "
    )


def perform_version_check(testbench_report: Path):
    try:
        manifest = read_manifest_json_from_testbench_report(testbench_report)
    except Exception:
        sys.exit(ERROR_COULD_NOT_READ_VERSION)
    server_version = manifest.get("serverVersions", {}).get("version", None)
    if not isinstance(server_version, str) or "." not in server_version:
        sys.exit(ERROR_COULD_NOT_READ_VERSION)
    minor_version = ".".join(server_version.split(".")[:2])

    if minor_version not in ALLOWED_SERVER_VERSIONS:
        sys.exit(_get_error_incompatible_version_message(server_version))


def read_manifest_json_from_testbench_report(testbench_report: Path) -> Any:
    if testbench_report.is_dir():
        manifest = testbench_report / "manifest.json"
        if not manifest.exists():
            raise FileNotFoundError("manifest.json not found")
        with manifest.open(encoding="utf-8") as f:
            return json.load(f)

    # ZIP archive
    elif testbench_report.suffix == ".zip":
        with ZipFile(testbench_report) as zf:
            try:
                with zf.open("manifest.json") as f:
                    return json.load(f)
            except KeyError as e:
                raise FileNotFoundError("manifest.json not found in zip") from e

    # Direct file
    elif testbench_report.is_file() and testbench_report.name == "manifest.json":
        with testbench_report.open(encoding="utf-8") as f:
            return json.load(f)
    else:
        raise FileNotFoundError(testbench_report)


def robot_tag_from_udf(udf: UserDefinedField) -> str | None:
    if (udf.udfType == UDFType.Enumeration and udf.value) or (
        udf.udfType == UDFType.String and udf.value
    ):
        return f"{udf.name}:{udf.value}"
    if udf.udfType == UDFType.Boolean and udf.value == "true":
        return udf.name
    return None


class PathResolver:
    def __init__(
        self,
        test_theme_tree: TestStructureTree,
        uids_of_existing_tcs: tuple[str, ...],
        log_suite_numbers: bool,
    ):
        self.tcs_catalog: dict[str, StructureNode] = {}
        self.tt_catalog: dict[str, TestThemeNode] = {}
        self.tree_dict: dict[str, TreeNode] = {}
        self._last_child_indices: dict[str, int] = {}
        self._log_suite_numbers = log_suite_numbers
        self._uids_of_existing_tcs = uids_of_existing_tcs
        self._analyze_tree(test_theme_tree)
        self.tcs_paths = self._get_paths(self.tcs_catalog)
        self.tt_paths = self._get_paths(self.tt_catalog)

    def _analyze_tree(self, test_theme_tree: TestStructureTree):
        if not test_theme_tree.root:
            logger.warning("Test Structure Tree contains no root node.")
            return
        root = test_theme_tree.root
        if not isinstance(root, TestCaseNode):
            self.tree_dict[root.base.key] = root
        self._add_existing_tcs_to_catalog(root)
        for tse in test_theme_tree.nodes:
            self._add_existing_tcs_to_catalog(tse)
            if isinstance(tse, TestCaseNode):
                if tse.spec:
                    self.tree_dict[f"tc_{tse.spec.key}"] = tse
            else:
                self.tree_dict[tse.base.key] = tse
            self._store_highest_child_index(tse)

    def _store_highest_child_index(self, tse):
        self._last_child_indices[tse.base.parentKey] = max(
            int(get_tse_index(tse)),
            self._last_child_indices.get(tse.base.parentKey, 0),
        )

    def _add_existing_tcs_to_catalog(self, tse):
        if isinstance(tse, TestCaseSetNode) and tse.base.uniqueID in self._uids_of_existing_tcs:
            self.tcs_catalog[tse.base.uniqueID] = tse

    def _get_paths(self, tse_catalog: Mapping[str, TreeNode]) -> dict[str, PurePath]:
        return {uid: self._resolve_tse_path(tse) for uid, tse in tse_catalog.items()}

    def _resolve_tse_path(self, tse: TreeNode) -> PurePath:
        self._add_tt_to_tt_catalog(tse)
        if isinstance(tse, RootNode):
            return PurePath()
        tse_name = replace_invalid_characters(tse.base.name)
        if tse.base.parentKey not in self.tree_dict:
            return PurePath(f"{self._file_prefix(tse)}{tse_name}")
        parent_path = self._resolve_tse_path(self.tree_dict[tse.base.parentKey])
        return parent_path / f"{self._file_prefix(tse)}{tse_name}"

    def _add_tt_to_tt_catalog(self, tse):
        if isinstance(tse, TestThemeNode) and tse.base.uniqueID not in self.tt_catalog:
            self.tt_catalog[tse.base.uniqueID] = tse

    def _file_prefix(self, tse) -> str:
        prefix_separator = "_" * (not self._log_suite_numbers)
        return f"{self._get_padded_index(tse)}_{prefix_separator}"

    def _get_padded_index(self, tse) -> str:
        index = get_tse_index(tse)
        max_length = len(str(self._last_child_indices.get(tse.base.parentKey, "")))
        return index.zfill(max_length)


def safe_eval(expression: str, names: dict) -> object:
    """Evaluates an attribute/subscript path over the given names - nothing else.

    Deliberately narrower than a full expression evaluator: no calls, no
    operators, no comprehensions. Enough for '$tcs.spec.responsible.name' or
    '$tcs.spec.udfs[0].value', and safe to feed with configuration input.
    """
    tree = ast.parse(expression, mode="eval")

    def resolve(node: ast.AST) -> object:
        if isinstance(node, ast.Name):
            if node.id not in names:
                raise ValueError(f"Unknown name: {node.id}")
            return names[node.id]
        if isinstance(node, ast.Attribute):
            if node.attr.startswith("_"):
                raise ValueError("Private attributes are forbidden")
            return getattr(resolve(node.value), node.attr)
        if isinstance(node, ast.Subscript):
            index = node.slice
            if not isinstance(index, ast.Constant):
                raise ValueError("Only constant subscripts are allowed")
            container = resolve(node.value)
            return container[index.value]  # type: ignore[index]
        raise ValueError(f"Disallowed expression: {type(node).__name__}")

    return resolve(tree.body)


METADATA_PLACEHOLDER = re.compile(r"\{\s*\$(\w+)([^}]*)\}")


def interpolate_metadata_value(value: str, names: dict) -> str:
    """Replaces '{$tcs...}' placeholders in a metadata value.

    Everything outside a placeholder stays literal, so plain values pass
    through unchanged. A placeholder that cannot be evaluated is left as it is
    and reported - the metadata entry itself survives.
    """

    def replace(match: re.Match) -> str:
        name, path = match.group(1), match.group(2)
        try:
            result = safe_eval(f"{name}{path}", names)
            # An enum like SpecStatus.NotPlanned should read 'NotPlanned'.
            return str(result.value) if isinstance(result, Enum) else str(result)
        except (ValueError, AttributeError, KeyError, IndexError, SyntaxError) as error:
            logger.warning(
                f"Metadata placeholder '{match.group(0)}' could not be evaluated: {error}"
            )
            return str(match.group(0))

    return str(METADATA_PLACEHOLDER.sub(replace, value))


class ReportSource:
    """A TestBench report opened for reading.

    'directory' holds the report's files. It is the report itself when a directory
    was given, otherwise the place the ZIP was extracted to. 'close()' removes a
    temporary extraction; a kept one (see 'open_report') and a directory input are
    left alone.
    """

    def __init__(self, directory: Path, extraction: tempfile.TemporaryDirectory | None) -> None:
        self.directory = directory
        self._extraction = extraction

    def close(self) -> None:
        if self._extraction is not None:
            self._extraction.cleanup()
            self._extraction = None

    def __enter__(self):
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()


def open_report(report: Path, keep_extracted: bool = False) -> ReportSource:
    """Opens a TestBench report given as a directory or a ZIP file.

    A ZIP is extracted to a temporary directory that 'ReportSource.close()' removes.
    With 'keep_extracted' it is extracted to a directory of the same name next to
    the ZIP instead ('report.zip' -> 'report/'), replacing what is there, and stays.
    """
    report = Path(report)
    if report.is_dir():
        return ReportSource(report.resolve(), None)
    if not report.exists():
        sys.exit(f"Error opening '{report.as_posix()}'. Path does not exist.")
    if not is_zip_file(report):
        sys.exit(f"Error opening '{report.as_posix()}'. File is not a ZIP file.")
    if keep_extracted:
        target = report.parent / report.stem
        if target.exists():
            shutil.rmtree(target)
        with ZipFile(report, "r") as archive:
            archive.extractall(target)
        return ReportSource(target.resolve(), None)
    # In the working directory, like the result directories, so that large reports
    # do not depend on the size of the system's temp location.
    extraction = tempfile.TemporaryDirectory(dir=Path.cwd())
    with ZipFile(report, "r") as archive:
        archive.extractall(extraction.name)
    return ReportSource(Path(extraction.name).resolve(), extraction)


def resolve_root_placeholder(path: str) -> str:
    """Replaces a leading '{root}' with the absolute path of the working directory."""
    return re.sub(r"^{root}", str(Path.cwd()).replace("\\", "\\\\"), path, flags=re.IGNORECASE)


def get_generation_directory(generation_directory: str) -> Path:
    if not generation_directory:
        return Path.cwd() / "Generated"
    return Path(resolve_root_placeholder(generation_directory))


def is_zip_file(path: Path) -> bool:
    return path.suffix.lower() == ".zip"


def ensure_dir_exists(cli_output_dir):
    if not Path(cli_output_dir).is_dir():
        Path(cli_output_dir).mkdir(parents=True, exist_ok=True)


def replace_invalid_characters(name: str) -> str:
    return re.sub(r'[<>:"/\\|?* ]', "_", name)


def get_tse_index(tse) -> str:
    return str(tse.base.numbering).rsplit(".", 1)[-1]


def directory_to_zip(directory: Path, new_path: str | None = None):
    if new_path:
        shutil.make_archive(str(new_path), "zip", str(directory))
    else:
        shutil.make_archive(str(directory), "zip", str(directory))


def get_list_item(lst, index, default: str | None):
    try:
        return lst[index]
    except IndexError:
        return default
