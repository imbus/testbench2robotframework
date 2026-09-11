import json
from dataclasses import asdict
from pathlib import Path

from .config import Configuration
from .json_codec import write_json
from .log import logger
from .model import (
    ReferenceAssignment,
    TestCaseDetails,
    TestCaseSetDetails,
    TestCaseSetExecutionForImport,
    TestStructureTree,
)

TEST_STRUCTURE_TREE_FILE = "cycle_structure"


def tree_as_dict(test_structure_tree: TestStructureTree) -> dict:
    """Serializes a test structure tree with the root node in front of its children.

    'model.py' is generated from the OpenAPI spec, where 'root' is optional and
    therefore has to be declared behind 'nodes'. 'asdict' follows that field
    order, which would put the root - the parent of every other element - at the
    end of the file.
    """
    tree_dict = asdict(test_structure_tree)
    return {
        "root": tree_dict.get("root"),
        **{key: value for key, value in tree_dict.items() if key != "root"},
    }


def write_test_structure_element(
    json_dir: str,
    test_structure_element: TestStructureTree | TestCaseSetDetails | TestCaseDetails,
) -> None:
    if isinstance(test_structure_element, TestStructureTree):
        filepath = Path(json_dir) / Path(TEST_STRUCTURE_TREE_FILE + ".json")
        content = tree_as_dict(test_structure_element)
    else:
        filepath = Path(json_dir) / Path(f"{test_structure_element.uniqueID}.json")
        content = asdict(test_structure_element)
    write_json(filepath, content)


def write_main_protocol(json_dir: str, main_protocol: list[TestCaseSetExecutionForImport]) -> None:
    write_json(Path(json_dir) / "protocol.json", [asdict(tcs) for tcs in main_protocol])


def write_references(json_dir: str, references: list[ReferenceAssignment]) -> None:
    write_json(Path(json_dir) / "references.json", [asdict(ref) for ref in references])




def write_default_config(config_file):
    with Path(config_file).open("w+", encoding="utf-8") as file:
        json.dump(
            Configuration.from_dict({}).__dict__,
            file,
            default=lambda o: o.__dict__,
            indent=2,
        )
        logger.warning(f"Default configuration written to '{config_file}'.")
