import json
from dataclasses import asdict
from pathlib import Path
from typing import Union

from .config import Configuration
from .log import logger
from .model import TestCaseDetails, TestCaseSetDetails, TestStructureTree

TEST_STRUCTURE_TREE_FILE = "TestThemeTree"


def write_test_structure_element(
    json_dir: str,
    test_structure_element: Union[TestStructureTree, TestCaseSetDetails, TestCaseDetails],
) -> None:
    if isinstance(test_structure_element, TestStructureTree):
        filepath = Path(json_dir) / Path(TEST_STRUCTURE_TREE_FILE + ".json")
    else:
        filepath = Path(json_dir) / Path(f"{test_structure_element.uniqueID}.json")
    with open(filepath, 'w+', encoding="utf8") as output_file:
        json.dump(asdict(test_structure_element), output_file, indent=2)


def write_default_config(config_file):
    with open(config_file, 'w+', encoding='utf-8') as file:
        json.dump(
            Configuration.from_dict({}).__dict__,
            file,
            default=lambda o: o.__dict__,
            indent=2,
        )
        logger.warning(f"Default Configuration generated to {config_file}")
