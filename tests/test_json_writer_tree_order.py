"""cycle_structure.json must list the root node before its children.

model.py is generated from the OpenAPI spec, where 'root' is optional and thus
declared behind 'nodes'. Without the writer reordering them, asdict() would put
the parent of every element at the end of the file.
"""

import json

from testbench2robotframework.json_writer import tree_as_dict, write_test_structure_element
from testbench2robotframework.model import (
    ActivityStatus,
    ExecStatus,
    TestCaseBaseInformation,
    TestCaseExecution,
    TestCaseNode,
    TestCaseSetNode,
    TestStructureElementType,
    TestStructureItemBaseInformation,
    TestStructureItemExecution,
    TestStructureTree,
    VerdictStatus,
)

SET_UID = "itb-TC-136238"
TC_UID = "itb-TC-136238-PC-422506"


def build_tree():
    return TestStructureTree(
        root=TestCaseSetNode(
            elementType=TestStructureElementType.TestCaseSetNode,
            base=TestStructureItemBaseInformation(
                key="4611686020000056681",
                numbering="1.1.2",
                path=SET_UID,
                parentKey="-1",
                name=SET_UID,
                uniqueID=SET_UID,
                matchesFilter=True,
            ),
            exec=TestStructureItemExecution(
                status=ActivityStatus.Performed,
                execStatus=ExecStatus.NotBlocked,
                verdict=VerdictStatus.Pass,
                key="302",
            ),
        ),
        nodes=[
            TestCaseNode(
                elementType=TestStructureElementType.TestCaseNode,
                base=TestCaseBaseInformation(
                    numbering="1.1.2.1",
                    parentKey="4611686020000056681",
                    name=TC_UID,
                    uniqueID=TC_UID,
                    matchesFilter=True,
                ),
                exec=TestCaseExecution(
                    status=ActivityStatus.Performed,
                    execStatus=ExecStatus.NotBlocked,
                    verdict=VerdictStatus.Pass,
                    key="401",
                ),
            )
        ],
    )


def test_root_is_serialized_before_the_nodes():
    assert list(tree_as_dict(build_tree())) == ["root", "nodes"]


def test_written_file_lists_root_first():
    written = tree_as_dict(build_tree())

    assert list(written) == ["root", "nodes"]
    assert written["root"]["base"]["uniqueID"] == SET_UID
    assert [node["base"]["uniqueID"] for node in written["nodes"]] == [TC_UID]


def test_write_test_structure_element_keeps_the_order_on_disk(tmp_path):
    write_test_structure_element(str(tmp_path), build_tree())

    content = json.loads((tmp_path / "cycle_structure.json").read_text(encoding="utf-8"))
    assert list(content) == ["root", "nodes"]


def test_tree_without_root_still_serializes():
    tree = build_tree()
    tree.root = None

    written = tree_as_dict(tree)

    assert list(written) == ["root", "nodes"]
    assert written["root"] is None
