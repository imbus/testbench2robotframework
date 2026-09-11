"""Execution results have to reach cycle_structure.json for every element type."""

from types import SimpleNamespace

from testbench2robotframework.model import (
    ActivityStatus,
    ExecStatus,
    RootNode,
    TestCaseBaseInformation,
    TestCaseExecution,
    TestCaseNode,
    TestCaseSetNode,
    TestStructureElementType,
    TestStructureItemBaseInformation,
    TestStructureItemExecution,
    TestStructureTree,
    TestThemeNode,
    VerdictStatus,
)
from testbench2robotframework.protocol_merge import Verdict
from testbench2robotframework.result_writer import ResultWriter

THEME_UID = "itb-TT-1"
SET_UID = "itb-TC-1"
EXECUTED_TC_UID = "itb-TC-1-PC-2"
UNTOUCHED_TC_UID = "itb-TC-1-PC-1"


def item_base(key, parent, uid):
    return TestStructureItemBaseInformation(
        key=key, numbering="1", path=uid, parentKey=parent, name=uid, uniqueID=uid, matchesFilter=True
    )


def item_exec(key):
    return TestStructureItemExecution(
        status=ActivityStatus.Planned,
        execStatus=ExecStatus.NotBlocked,
        verdict=VerdictStatus.Undefined,
        key=key,
    )


def make_test_case_node(uid, numbering, with_exec=True):
    return TestCaseNode(
        elementType=TestStructureElementType.TestCaseNode,
        base=TestCaseBaseInformation(
            numbering=numbering, parentKey="300", name=uid, uniqueID=uid, matchesFilter=True
        ),
        exec=TestCaseExecution(
            status=ActivityStatus.Planned,
            execStatus=ExecStatus.NotBlocked,
            verdict=VerdictStatus.Undefined,
            key=f"exec-{uid}",
        )
        if with_exec
        else None,
    )


def build_tree(*test_case_nodes):
    return TestStructureTree(
        root=RootNode(
            elementType=TestStructureElementType.RootNode,
            base=item_base("100", "-1", "itb-RT-1"),
            filters=[],
        ),
        nodes=[
            TestThemeNode(
                elementType=TestStructureElementType.TestThemeNode,
                base=item_base("200", "100", THEME_UID),
                filters=[],
                exec=item_exec("202"),
            ),
            TestCaseSetNode(
                elementType=TestStructureElementType.TestCaseSetNode,
                base=item_base("300", "200", SET_UID),
                exec=item_exec("302"),
            ),
            *test_case_nodes,
        ],
    )


def executed_test_case(verdict=VerdictStatus.Pass):
    return SimpleNamespace(
        exec=SimpleNamespace(
            verdict=verdict, status=ActivityStatus.Performed, execStatus=ExecStatus.NotBlocked
        )
    )


def make_result_writer(catalog=None, merged_verdicts=None, executed_suites=()):
    writer = ResultWriter.__new__(ResultWriter)  # bypasses the file system heavy __init__
    writer.itb_test_case_catalog = catalog or {}
    writer.merged_verdicts = merged_verdicts or {}
    writer.test_suites = {uid: SimpleNamespace(status="PASS") for uid in executed_suites}
    return writer


def node_by_uid(tree, uid):
    return next(node for node in tree.nodes if node.base.uniqueID == uid)


def test_executed_test_case_node_gets_its_result():
    tree = build_tree(make_test_case_node(EXECUTED_TC_UID, "2"))
    writer = make_result_writer(
        catalog={EXECUTED_TC_UID: executed_test_case(VerdictStatus.Fail)},
        merged_verdicts={SET_UID: Verdict.Fail},
        executed_suites=[THEME_UID, SET_UID],
    )

    writer._update_tree_verdicts(tree)

    test_case = node_by_uid(tree, EXECUTED_TC_UID)
    assert test_case.exec.verdict is VerdictStatus.Fail
    assert test_case.exec.status is ActivityStatus.Performed
    assert test_case.exec.execStatus is ExecStatus.NotBlocked


def test_test_case_node_outside_the_robot_run_is_left_untouched():
    tree = build_tree(make_test_case_node(UNTOUCHED_TC_UID, "1"), make_test_case_node(EXECUTED_TC_UID, "2"))
    writer = make_result_writer(
        catalog={EXECUTED_TC_UID: executed_test_case()},
        merged_verdicts={SET_UID: Verdict.Pass},
        executed_suites=[THEME_UID, SET_UID],
    )

    writer._update_tree_verdicts(tree)

    untouched = node_by_uid(tree, UNTOUCHED_TC_UID)
    assert untouched.exec.verdict is VerdictStatus.Undefined
    assert untouched.exec.status is ActivityStatus.Planned


def test_test_case_node_without_execution_data_is_skipped():
    tree = build_tree(make_test_case_node(EXECUTED_TC_UID, "2", with_exec=False))
    writer = make_result_writer(
        catalog={EXECUTED_TC_UID: executed_test_case()},
        merged_verdicts={SET_UID: Verdict.Pass},
        executed_suites=[THEME_UID, SET_UID],
    )

    writer._update_tree_verdicts(tree)

    assert node_by_uid(tree, EXECUTED_TC_UID).exec is None


def test_test_case_set_and_theme_are_still_updated():
    tree = build_tree(make_test_case_node(EXECUTED_TC_UID, "2"))
    writer = make_result_writer(
        catalog={EXECUTED_TC_UID: executed_test_case(VerdictStatus.Fail)},
        merged_verdicts={SET_UID: Verdict.Fail},
        executed_suites=[THEME_UID, SET_UID],
    )

    writer._update_tree_verdicts(tree)

    assert node_by_uid(tree, SET_UID).exec.verdict is VerdictStatus.Fail
    assert node_by_uid(tree, SET_UID).exec.status is ActivityStatus.Performed
    assert node_by_uid(tree, THEME_UID).exec.verdict is VerdictStatus.Fail


def test_test_case_nodes_do_not_count_as_test_suites():
    tree = build_tree(make_test_case_node(EXECUTED_TC_UID, "2"))
    writer = make_result_writer(
        catalog={EXECUTED_TC_UID: executed_test_case()},
        merged_verdicts={SET_UID: Verdict.Pass},
        executed_suites=[THEME_UID, SET_UID],
    )

    assert writer._update_tree_verdicts(tree) == 2
