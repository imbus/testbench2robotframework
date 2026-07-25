from __future__ import annotations

from typing import TYPE_CHECKING

from .model import (
    ExecStatus,
    RootNode,
    TestCaseSetNode,
    TestStructureTree,
    TestThemeNode,
)

if TYPE_CHECKING:
    from .json_reader import TestCaseSet

# Nodes carrying a TestStructureItemBaseInformation, i.e. everything that can be
# the parent of a test case set. TestCaseNodes are leaves and are never parents.
StructureNode = RootNode | TestThemeNode | TestCaseSetNode


def is_blocked(execution) -> bool:
    """Whether an execution summary marks its test element as blocked.

    Specification-only exports carry no execution data at all. A missing
    execution therefore counts as 'not blocked'.
    """
    return execution is not None and execution.execStatus is ExecStatus.Blocked


def blocked_test_case_set_uids(test_theme_tree: TestStructureTree) -> set[str]:
    """UniqueIDs of all test case sets that are blocked themselves or inherit it.

    Blocking a test theme in TestBench blocks everything below it, so the whole
    chain of parents is checked.
    """
    nodes: dict[str, StructureNode] = {}
    if isinstance(test_theme_tree.root, (RootNode, TestThemeNode, TestCaseSetNode)):
        nodes[test_theme_tree.root.base.key] = test_theme_tree.root
    for node in test_theme_tree.nodes:
        if isinstance(node, (TestThemeNode, TestCaseSetNode)):
            nodes[node.base.key] = node
    blocked_uids = set()
    for node in test_theme_tree.nodes:
        if isinstance(node, TestCaseSetNode) and _is_blocked_with_parents(node, nodes):
            blocked_uids.add(node.base.uniqueID)
    return blocked_uids


def _is_blocked_with_parents(node: StructureNode, nodes: dict[str, StructureNode]) -> bool:
    visited: set[str] = set()
    current: StructureNode | None = node
    while current is not None and current.base.key not in visited:
        if is_blocked(getattr(current, "exec", None)):
            return True
        visited.add(current.base.key)
        current = nodes.get(current.base.parentKey)
    return False


def filter_blocked(
    test_case_set_catalog: dict[str, TestCaseSet],
    test_theme_tree: TestStructureTree,
) -> tuple[dict[str, TestCaseSet], int, int]:
    """Removes blocked test elements from a test case set catalog.

    Returns the filtered catalog, the number of dropped test case sets and the
    number of dropped test cases. A test case set that loses all of its test
    cases is dropped as well, while a test case set that was empty before is
    kept unchanged.
    """
    from .json_reader import TestCaseSet  # noqa: PLC0415 (avoids a circular import)

    blocked_uids = blocked_test_case_set_uids(test_theme_tree)
    filtered_catalog: dict[str, TestCaseSet] = {}
    dropped_test_case_sets = 0
    dropped_test_cases = 0
    for uid, test_case_set in test_case_set_catalog.items():
        if uid in blocked_uids:
            dropped_test_case_sets += 1
            continue
        kept_test_cases = {
            tc_uid: test_case
            for tc_uid, test_case in test_case_set.test_cases.items()
            if not is_blocked(test_case.exec)
        }
        dropped_test_cases += len(test_case_set.test_cases) - len(kept_test_cases)
        if test_case_set.test_cases and not kept_test_cases:
            dropped_test_case_sets += 1
            continue
        filtered_catalog[uid] = TestCaseSet(test_case_set.details, kept_test_cases)
    return filtered_catalog, dropped_test_case_sets, dropped_test_cases
