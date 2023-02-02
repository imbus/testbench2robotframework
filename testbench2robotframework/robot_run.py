from typing import Dict

from robot.parsing.model.blocks import File
from robot.running.model import TestSuite

from .model import TestStructureTreeNode
from .utils import PathResolver


class RobotSuiteRunner:
    def __init__(self, test_suite_models: Dict[str, File], path_resolver: PathResolver) -> None:
        self.test_suite_models = test_suite_models
        self.path_resolver = path_resolver
        self.test_suites: Dict[str, TestSuite] = {"[Root]": TestSuite()}
        for _, tcs in self.path_resolver.tcs_catalog.items():
            self._add_test_structure_element_to_test_suite_hierarchy(tcs)

    def _add_test_structure_element_to_test_suite_hierarchy(self, tse: TestStructureTreeNode):
        suite_uid = tse.baseInformation.uniqueID
        test_suite = self._get_test_suite_from_model(suite_uid, self.test_suite_models[suite_uid])
        parent_tse = self.path_resolver.tree_dict[tse.baseInformation.parentKey]
        if parent_tse.baseInformation.name != "[Root]":
            parent_uid = parent_tse.baseInformation.uniqueID
            parent_testsuite = self._get_test_suite_from_model(
                parent_uid, self.test_suite_models[parent_uid]
            )
            parent_testsuite.suites.append(test_suite)
            self._add_test_structure_element_to_test_suite_hierarchy(parent_tse)
        else:
            self.test_suites["[Root]"].suites.append(test_suite)

    def _get_test_suite_from_model(self, suite_uid: str, model: File):
        if self.test_suites.get(suite_uid):
            return self.test_suites[suite_uid]
        test_suite = TestSuite.from_model(model, name=suite_uid)
        self.test_suites[suite_uid] = test_suite
        return test_suite

    def run_suites(self):
        self.test_suites["[Root]"].run(output='./results/output.xml')
