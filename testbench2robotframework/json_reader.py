import json
import sys
from dataclasses import dataclass
from json import JSONDecodeError
from os import path
from typing import Dict, List, Optional

from .log import logger
from .model import TestCaseDetails, TestCaseSetDetails, TestStructureTree, TestStructureTreeNodeType

TEST_STRUCTURE_TREE_FILE = "TestThemeTree.json"


@dataclass
class TestCaseSet:
    details: TestCaseSetDetails
    test_cases: Dict[str, TestCaseDetails]

    @property
    def metadata(self) -> Dict[str, str]:
        return {
            "UniqueID": self.details.uniqueID,
            "Name": self.details.name,
            "Numbering": self.details.numbering,
        }


class TestBenchJsonReader:
    def __init__(self, json_dir):
        self.json_dir = json_dir
        self._test_theme_tree: Optional[TestStructureTree] = None
        self._test_case_sets: Dict[str, TestCaseSetDetails] = {}
        self._test_cases: Dict[str, TestCaseDetails] = {}
        if not json_dir:
            logger.warning("No jsonReport path given.")
            sys.exit()

    @property
    def test_theme_tree(self) -> TestStructureTree:
        if not self._test_theme_tree:
            test_theme_path = path.join(self.json_dir, TEST_STRUCTURE_TREE_FILE)
            logger.debug(f"Loading TestThemeTree from {test_theme_path}")
            test_structure_tree = read_json(test_theme_path)
            self._test_theme_tree = TestStructureTree.from_dict(test_structure_tree)
            logger.info(f"{len(self._test_theme_tree.nodes)} nodes from TestThemeTree loaded.")
        return self._test_theme_tree

    @property
    def test_case_sets(self) -> Dict[str, TestCaseSetDetails]:
        if not self._test_case_sets:
            for tcs_uid in self.get_test_case_set_uids():
                test_case_set = self.read_test_case_set(tcs_uid)
                if test_case_set is not None:
                    self._test_case_sets[tcs_uid] = test_case_set
                    logger.debug(f"TestCaseSetDetails {tcs_uid} loaded.")
                else:
                    logger.debug(f"TestCaseSetDetails {tcs_uid} not found.")
            logger.info(f"{len(self._test_case_sets)} TestCaseSetDetails loaded.")
        return self._test_case_sets

    @property
    def test_cases(self) -> Dict[str, TestCaseDetails]:
        if not self._test_cases:
            for tcs_uid in self.test_case_sets:
                tc_uids = self.get_test_case_uids(tcs_uid)
                self._read_test_cases(tc_uids)
        return self._test_cases

    def _read_test_cases(self, tc_uids):
        for tc_uid in tc_uids:
            test_case = self.read_test_case(tc_uid)
            if test_case is not None:
                self._test_cases[tc_uid] = test_case
                logger.debug(f"TestCaseDetails {tc_uid} loaded.")

    def get_test_case_set_catalog(self):
        tcs_catalog: Dict[str, TestCaseSet] = {}
        for tcs_uid, tcs in self.test_case_sets.items():
            tc_catalog: Dict[str, TestCaseDetails] = {}
            for tc_uid in self.get_test_case_uids(tcs_uid):
                tc_catalog[tc_uid] = self.test_cases[tc_uid]
            tcs_catalog[tcs_uid] = TestCaseSet(tcs, tc_catalog)
        return tcs_catalog

    def get_test_case_set_uids(self) -> List[str]:
        nodes = self.test_theme_tree.nodes
        return [
            tse.baseInformation.uniqueID
            for tse in nodes
            if tse.elementType == TestStructureTreeNodeType.TestCaseSet
        ]

    def get_test_case_uids(self, test_case_set_uid: str) -> List[str]:
        if not self._test_case_sets:
            test_case_set = self.read_test_case_set(test_case_set_uid)
            if test_case_set is None:
                logger.debug(f"TestCaseSet with uid '{test_case_set_uid}' not found.")
                return []
        else:
            test_case_set = self.test_case_sets[test_case_set_uid]
        return [tc.uniqueID for tc in test_case_set.testCases]

    def read_test_case_set(self, uid) -> Optional[TestCaseSetDetails]:
        tcs_dict = read_json(path.join(self.json_dir, f"{uid}.json"))
        if tcs_dict is None:
            return None
        return TestCaseSetDetails.from_dict(tcs_dict)

    def read_test_case(self, uid) -> Optional[TestCaseDetails]:
        tc_dict = read_json(path.join(self.json_dir, f"{uid}.json"))
        if tc_dict is None:
            return None
        return TestCaseDetails.from_dict(tc_dict)

    def read_test_theme_tree(self) -> Optional[TestStructureTree]:
        test_structure_tree = read_json(path.join(self.json_dir, TEST_STRUCTURE_TREE_FILE))
        if test_structure_tree is None:
            return None
        return TestStructureTree.from_dict(test_structure_tree)


def read_json(filepath: str):  # ToDo Configure to run silent or raise
    try:
        with open(filepath, encoding='utf-8') as json_file:
            return json.load(json_file)
    except FileNotFoundError:
        logger.debug(f"Cannot find json file {filepath}:")
        return None
    except JSONDecodeError as error:  # pylint: disable=broad-except
        logger.warning(f"Cannot decode json file {filepath}:")
        logger.warning(error)
        return None
