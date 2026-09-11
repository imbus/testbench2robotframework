from types import SimpleNamespace

from testbench2robotframework.blocked_filter import (
    blocked_test_case_set_uids,
    filter_blocked,
    is_blocked,
)
from testbench2robotframework.json_reader import TestCaseSet
from testbench2robotframework.model import (
    ActivityStatus,
    ExecStatus,
    RootNode,
    TestCaseSetNode,
    TestStructureElementType,
    TestStructureItemBaseInformation,
    TestStructureItemExecution,
    TestStructureTree,
    TestThemeNode,
    VerdictStatus,
)


def base(key, parent, uid):
    return TestStructureItemBaseInformation(
        key=key,
        numbering="1",
        path=uid,
        parentKey=parent,
        name=uid,
        uniqueID=uid,
        matchesFilter=True,
    )


def item_exec(blocked: bool):
    return TestStructureItemExecution(
        status=ActivityStatus.Planned,
        execStatus=ExecStatus.Blocked if blocked else ExecStatus.NotBlocked,
        verdict=VerdictStatus.Undefined,
        key=f"exec-{blocked}",
    )


def root_node():
    return RootNode(
        elementType=TestStructureElementType.RootNode, base=base("1", "-1", "RT"), filters=[]
    )


def theme_node(key, parent, uid, blocked=False, has_exec=True):
    return TestThemeNode(
        elementType=TestStructureElementType.TestThemeNode,
        base=base(key, parent, uid),
        filters=[],
        exec=item_exec(blocked) if has_exec else None,
    )


def set_node(key, parent, uid, blocked=False, has_exec=True):
    return TestCaseSetNode(
        elementType=TestStructureElementType.TestCaseSetNode,
        base=base(key, parent, uid),
        exec=item_exec(blocked) if has_exec else None,
    )


def make_test_case(blocked: bool):
    return SimpleNamespace(
        exec=SimpleNamespace(execStatus=ExecStatus.Blocked if blocked else ExecStatus.NotBlocked)
    )


def make_test_case_set(*test_cases):
    return TestCaseSet(
        details=None, test_cases={f"tc-{index}": tc for index, tc in enumerate(test_cases)}
    )


def test_is_blocked():
    assert is_blocked(item_exec(True)) is True
    assert is_blocked(item_exec(False)) is False
    assert is_blocked(None) is False


def test_directly_blocked_test_case_set_is_collected():
    tree = TestStructureTree(root=root_node(), nodes=[set_node("10", "1", "TCS-1", blocked=True)])

    assert blocked_test_case_set_uids(tree) == {"TCS-1"}


def test_test_case_set_below_blocked_theme_is_collected():
    tree = TestStructureTree(
        root=root_node(),
        nodes=[
            theme_node("10", "1", "TT-1", blocked=True),
            set_node("20", "10", "TCS-1"),
        ],
    )

    assert blocked_test_case_set_uids(tree) == {"TCS-1"}


def test_blocking_is_inherited_transitively():
    tree = TestStructureTree(
        root=root_node(),
        nodes=[
            theme_node("10", "1", "TT-1", blocked=True),
            theme_node("20", "10", "TT-2"),
            set_node("30", "20", "TCS-1"),
            set_node("40", "1", "TCS-2"),
        ],
    )

    assert blocked_test_case_set_uids(tree) == {"TCS-1"}


def test_nothing_is_blocked_without_execution_data():
    tree = TestStructureTree(
        root=root_node(),
        nodes=[
            theme_node("10", "1", "TT-1", has_exec=False),
            set_node("20", "10", "TCS-1", has_exec=False),
        ],
    )

    assert blocked_test_case_set_uids(tree) == set()


def test_blocked_test_case_set_is_dropped_from_catalog():
    tree = TestStructureTree(root=root_node(), nodes=[set_node("10", "1", "TCS-1", blocked=True)])
    catalog = {"TCS-1": make_test_case_set(make_test_case(False))}

    filtered, dropped_sets, dropped_cases = filter_blocked(catalog, tree)

    assert filtered == {}
    assert (dropped_sets, dropped_cases) == (1, 0)


def test_blocked_test_case_is_dropped_from_kept_set():
    tree = TestStructureTree(root=root_node(), nodes=[set_node("10", "1", "TCS-1")])
    catalog = {"TCS-1": make_test_case_set(make_test_case(False), make_test_case(True))}

    filtered, dropped_sets, dropped_cases = filter_blocked(catalog, tree)

    assert list(filtered) == ["TCS-1"]
    assert list(filtered["TCS-1"].test_cases) == ["tc-0"]
    assert (dropped_sets, dropped_cases) == (0, 1)


def test_set_losing_all_test_cases_is_dropped():
    tree = TestStructureTree(root=root_node(), nodes=[set_node("10", "1", "TCS-1")])
    catalog = {"TCS-1": make_test_case_set(make_test_case(True), make_test_case(True))}

    filtered, dropped_sets, dropped_cases = filter_blocked(catalog, tree)

    assert filtered == {}
    assert (dropped_sets, dropped_cases) == (1, 2)


def test_already_empty_set_is_kept():
    tree = TestStructureTree(root=root_node(), nodes=[set_node("10", "1", "TCS-1")])
    catalog = {"TCS-1": make_test_case_set()}

    filtered, dropped_sets, dropped_cases = filter_blocked(catalog, tree)

    assert list(filtered) == ["TCS-1"]
    assert (dropped_sets, dropped_cases) == (0, 0)


def test_unblocked_catalog_is_returned_unchanged():
    tree = TestStructureTree(root=root_node(), nodes=[set_node("10", "1", "TCS-1")])
    catalog = {"TCS-1": make_test_case_set(make_test_case(False), make_test_case(False))}

    filtered, dropped_sets, dropped_cases = filter_blocked(catalog, tree)

    assert list(filtered["TCS-1"].test_cases) == ["tc-0", "tc-1"]
    assert (dropped_sets, dropped_cases) == (0, 0)
