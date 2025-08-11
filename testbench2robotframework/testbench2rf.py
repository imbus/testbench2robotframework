from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path, PurePath
from uuid import uuid4

from robot import version as robot_version
from robot.parsing.lexer.tokens import Token
from robot.parsing.model.blocks import (
    End,
    File,
    Keyword,
    KeywordSection,
    SettingSection,
    TestCase,
    TestCaseSection,
)
from robot.parsing.model.statements import (
    Comment,
    EmptyLine,
    KeywordCall,
    LibraryImport,
    Metadata,
    ResourceImport,
    SectionHeader,
    Setup,
    Statement,
    Tags,
    Teardown,
    TestCaseName,
    VariablesImport,
)

from testbench2robotframework.utils import robot_tag_from_udf

try:
    from robot.parsing.model.statements import TestTags
except ImportError:
    from robot.parsing.model.statements import ForceTags as TestTags

from .config import CompoundInteractionLogging, Configuration
from .json_reader import TestCaseSet
from .log import logger
from .model import (
    InteractionCall,
    InteractionDetails,
    InteractionType,
    ParameterEvaluationType,
    SequencePhase,
    TestCaseDetails,
    TestStructureTreeNode,
    TestThemeNode,
    UDFType,
    UserDefinedField,
)
from .utils import PathResolver

try:
    from robot.parsing.model.blocks import Group
    from robot.parsing.model.statements import GroupHeader
except ImportError:
    Group = None

SEPARATOR = "    "
ROBOT_PATH_SEPARATOR = "/"
RELATIVE_RESOURCE_INDICATOR = r"^{root}"
SECTION_SEPARATOR = [EmptyLine.from_params()] * 2
LINE_SEPARATOR = [EmptyLine.from_params()]
UNKNOWN_IMPORT_TYPE = str(uuid4())
LIBRARY_IMPORT_TYPE = str(uuid4())
RESOURCE_IMPORT_TYPE = str(uuid4())


@dataclass
class RFInteractionCall:
    name: str
    cbv_parameters: dict[str, str]
    cbr_parameters: dict[str, str]
    indent: int
    sequence_phase: str
    is_atomic: bool
    import_prefix: str | None = None


class RfTestCase:
    def __init__(self, test_case_details: TestCaseDetails, config: Configuration) -> None:
        self.test_case_details: TestCaseDetails = test_case_details
        self.uid: str = test_case_details.uniqueID
        self.rf_interaction_calls: list[RFInteractionCall] = []
        self.used_imports: dict[str, set[str]] = {}
        self.config = config
        self.lib_pattern_list = [re.compile(pattern) for pattern in config.library_regex]
        self.res_pattern_list = [re.compile(pattern) for pattern in config.resource_regex]
        for interaction in test_case_details.testSequence:
            self._get_interaction_call(interaction)
        self.rf_tags = self._get_tags(test_case_details)
        self.setup_keyword: Keyword | None = None
        self.teardown_keyword: Keyword | None = None
        # TODO description

    @staticmethod
    def _get_tags(test_case_details: TestCaseDetails) -> list[str]:
        tags = [keyword.name for keyword in test_case_details.spec.keywords]
        tags.extend(
            [
                robot_tag_from_udf(udf)
                for udf in test_case_details.spec.udfs
                if robot_tag_from_udf(udf)
            ]
        )
        return tags

    @staticmethod
    def _get_udf_tags(user_defined_fields: list[UserDefinedField]) -> list[str]:
        udfs = []
        for udf in user_defined_fields:
            if udf.udfType in [UDFType.Enumeration, UDFType.String] and udf.value:
                udfs.append(f"{udf.name}:{udf.value}")
            elif udf.udfType == UDFType.Boolean and udf.value.lower() == "true":
                udfs.append(udf.name)
        return udfs

    def _get_interaction_call(self, test_step: InteractionCall) -> None:
        indent = len(test_step.numbering.split("."))
        if test_step.spec.interactionType == InteractionType.Textual:
            self.rf_interaction_calls.append(
                RFInteractionCall(
                    name=f"# {test_step.spec.name}",
                    cbv_parameters={},
                    cbr_parameters={},
                    indent=indent,
                    import_prefix=None,
                    sequence_phase=test_step.spec.sequencePhase,
                    is_atomic=True,
                )
            )
            return
        cbv_params = self._get_params_by_use_type(test_step, ParameterEvaluationType.CallByValue)
        cbr_params = self._get_params_by_use_type(
            test_step,
            ParameterEvaluationType.CallByReference,
            ParameterEvaluationType.CallByReferenceMandatory,
        )
        if test_step.spec.interactionType == InteractionType.Compound:
            self._append_compound_ia(cbr_params, cbv_params, indent, test_step)
        elif test_step.spec.interactionType == InteractionType.Atomic:
            interaction_details: InteractionDetails = next(
                filter(
                    lambda interaction: interaction.key == test_step.spec.interactionKey,
                    self.test_case_details.interactions,
                ),
                None,
            )
            if interaction_details:
                interaction_path = interaction_details.path
            self._append_atomic_ia(
                cbr_params, cbv_params, indent, test_step, interaction_path
            )  # TODO: Else für textuelle Interaktionen

    def _append_atomic_ia(
        self,
        cbr_params: dict[str, str],
        cbv_params: dict[str, str],
        indent: int,
        test_step: InteractionCall,
        interaction_path: str,
    ):
        resource_type, import_prefix = self._get_keyword_import(test_step, interaction_path)

        if resource_type not in self.used_imports:
            self.used_imports[resource_type] = {import_prefix}
        else:
            self.used_imports[resource_type].add(import_prefix)
        self.rf_interaction_calls.append(
            RFInteractionCall(
                name=test_step.spec.name,
                cbv_parameters=cbv_params,
                cbr_parameters=cbr_params,
                indent=indent,
                import_prefix=import_prefix,
                sequence_phase=test_step.spec.sequencePhase,
                is_atomic=True,
            )
        )

    def _get_keyword_import(
        self, test_step: InteractionCall, interaction_path: str
    ) -> tuple[str, str]:
        for pattern in self.lib_pattern_list:
            match = pattern.search(interaction_path)
            if match:
                return LIBRARY_IMPORT_TYPE, match.group("resourceName").strip()
        for pattern in self.res_pattern_list:
            match = pattern.search(interaction_path)
            if match:
                return RESOURCE_IMPORT_TYPE, interaction_path
        splitted_interaction_path = interaction_path.split(".")
        minimum_length_subdivision_path_length = 2
        if (
            len(splitted_interaction_path) == minimum_length_subdivision_path_length
            and splitted_interaction_path[0] in self.config.library_root
        ):
            return LIBRARY_IMPORT_TYPE, splitted_interaction_path[1]
        return UNKNOWN_IMPORT_TYPE, interaction_path

    def _append_compound_ia(
        self,
        cbr_params: dict[str, str],
        cbv_params: dict[str, str],
        indent: int,
        test_step: InteractionCall,
    ):
        self.rf_interaction_calls.append(
            RFInteractionCall(
                test_step.spec.name,
                cbv_parameters=cbv_params,
                cbr_parameters=cbr_params,
                indent=indent,
                sequence_phase=test_step.spec.sequencePhase,
                is_atomic=False,
            )
        )

    def _create_rf_keyword_calls(
        self, interaction_calls: list[RFInteractionCall]
    ) -> list[list[Statement]]:
        keyword_lists: list[list[Statement]] = [[]]
        tc_index = 0
        is_first_atomic = True
        group_stack = []
        for interaction_call in interaction_calls:
            if interaction_call.is_atomic:
                if (
                    self.is_splitting_ia(interaction_call, keyword_lists, tc_index)
                    and not is_first_atomic
                ):
                    tc_index += 1
                    keyword_lists.append([])
                is_first_atomic = False
                atomic_keyword_call = self._create_rf_keyword(interaction_call)
                while group_stack and group_stack[-1][1] >= interaction_call.indent:
                    group_stack.pop()
                if group_stack:
                    group_stack[-1][0].body.append(atomic_keyword_call)
                else:
                    keyword_lists[tc_index].append(atomic_keyword_call)
            elif (
                not interaction_call.is_atomic
                and self.config.compound_interaction_logging != CompoundInteractionLogging.NONE
            ):
                compound_keyword_call = self._create_rf_compound_keyword(
                    interaction_call, self.config.compound_interaction_logging
                )
                while group_stack and group_stack[-1][1] >= interaction_call.indent:
                    group_stack.pop()
                if group_stack:
                    group_stack[-1][0].body.append(compound_keyword_call)
                else:
                    keyword_lists[tc_index].append(compound_keyword_call)
                if (
                    Group
                    and self.config.compound_interaction_logging == CompoundInteractionLogging.GROUP
                ):
                    group_stack.append((compound_keyword_call, interaction_call.indent))
        return keyword_lists

    def is_splitting_ia(self, interaction_call, keyword_lists, tc_index):
        return (
            re.search(
                self.config.testCaseSplitPathRegEx,
                f"{interaction_call.import_prefix}.{interaction_call.name}",
            )
            and keyword_lists[tc_index]
            and self.config.testCaseSplitPathRegEx
        )

    def _create_rf_setup_call(self, setup_interaction: RFInteractionCall) -> Setup:
        cbr_parameters = self._create_cbr_parameters(setup_interaction)
        if cbr_parameters:
            logger.error("No variable assignment in [setup] possible.")
        import_prefix = self._get_interaction_import_prefix(setup_interaction)
        interaction_indent = self._get_interaction_indent(setup_interaction)
        cbv_parameters = self._create_cbv_parameters(setup_interaction)
        return Setup.from_params(
            name=f"{import_prefix}{setup_interaction.name}",
            args=tuple(cbv_parameters),
            indent=interaction_indent,
        )

    def _create_rf_teardown_call(
        self,
        teardown_interaction: RFInteractionCall,
    ) -> Teardown:
        cbr_parameters = self._create_cbr_parameters(teardown_interaction)
        if cbr_parameters:
            logger.error("No variable assignment in [teardown] possible.")
        import_prefix = self._get_interaction_import_prefix(teardown_interaction)
        interaction_indent = self._get_interaction_indent(teardown_interaction)
        cbv_parameters = self._create_cbv_parameters(teardown_interaction)
        return Teardown.from_params(
            name=f"{import_prefix}{teardown_interaction.name}",
            args=tuple(cbv_parameters),
            indent=interaction_indent,
        )

    def _create_rf_keyword_from_interaction_list(
        self, keyword_name: str, interactions: list[RFInteractionCall]
    ):
        keyword_calls_lists = self._create_rf_keyword_calls(interactions)
        keyword = Keyword(header=TestCaseName.from_params(keyword_name))
        keyword.body.extend(keyword_calls_lists[0])
        keyword.body.extend(LINE_SEPARATOR)
        return keyword

    def _create_rf_setup(self, setup_interactions: list[RFInteractionCall]) -> Setup | None:
        rf_setup = None
        if len(setup_interactions) == 1:
            rf_setup = self._create_rf_setup_call(setup_interactions[0])
        elif len(setup_interactions) > 1:
            self.setup_keyword = self._create_rf_keyword_from_interaction_list(
                f"Setup-{self.uid}", setup_interactions
            )
            rf_setup = Setup.from_params(name=self.setup_keyword.name)
        return rf_setup

    def _get_teardown_params(self, interaction_calls: list[RFInteractionCall]):
        if len(interaction_calls) == 1:
            interaction = interaction_calls[0]
            return {
                "name": f"{self._get_interaction_import_prefix(interaction)}{interaction.name}",
                "args": tuple(self._create_cbv_parameters(interaction)),
                "indent": self._get_interaction_indent(interaction),
            }
        return {"name": f"Teardown-{self.uid}"}

    def _create_rf_teardown(self, teardown_interactions: list[RFInteractionCall]) -> Setup | None:
        rf_teardown = None
        if len(teardown_interactions) == 1:
            rf_teardown = self._create_rf_teardown_call(teardown_interactions[0])
        elif len(teardown_interactions) > 1:
            self.teardown_keyword = self._create_rf_keyword_from_interaction_list(
                f"Teardown-{self.uid}", teardown_interactions
            )
            rf_teardown = Teardown.from_params(name=self.teardown_keyword.name)
        return rf_teardown

    def to_robot_ast_test_cases(
        self,
    ) -> list[
        TestCase
    ]:  # TODO: Separate testcase splitting from this method --> new method: to_robot_ast_test_case
        setup_interactions = list(
            filter(
                lambda interaction: interaction.sequence_phase == SequencePhase.Setup,
                self.rf_interaction_calls,
            )
        )
        rf_setup = self._create_rf_setup(setup_interactions)
        test_step_interactions = list(
            filter(
                lambda interaction: interaction.sequence_phase == SequencePhase.TestStep,
                self.rf_interaction_calls,
            )
        )
        rf_keyword_call_lists = self._create_rf_keyword_calls(test_step_interactions)
        teardown_interactions = list(
            filter(
                lambda interaction: interaction.sequence_phase == SequencePhase.Teardown,
                self.rf_interaction_calls,
            )
        )
        rf_teardown = self._create_rf_teardown(teardown_interactions)
        rf_test_cases: list[TestCase] = []
        multiple_tests = len(rf_keyword_call_lists) > 1
        for index, rf_keywords in enumerate(rf_keyword_call_lists):
            phase_pattern = self.config.phasePattern
            tc_name = (
                phase_pattern.format(
                    testcase=self.uid,
                    index=index + 1,
                    length=len(rf_keyword_call_lists),
                )
                if multiple_tests
                else self.uid
            )
            # suffix = f' : Phase {index + 1}/{len(rf_keyword_lists)}' if multiple_tests else ''
            # tc_name = f"{self.uid}{suffix}"  # TODO later UID or Comments
            rf_test_case = TestCase(header=TestCaseName.from_params(tc_name))
            if self.rf_tags:
                rf_test_case.body.append(Tags.from_params(self.rf_tags))
            if index == 0 and rf_setup:
                rf_test_case.body.append(rf_setup)
            rf_test_case.body.extend(rf_keywords)
            if index == len(rf_keyword_call_lists) - 1 and rf_teardown:
                rf_test_case.body.append(rf_teardown)
            if index != len(rf_keyword_call_lists) - 1:
                rf_test_case.body.extend(LINE_SEPARATOR)
            rf_test_cases.append(rf_test_case)
        return rf_test_cases

    @staticmethod
    def _create_cbv_parameters(interaction: RFInteractionCall) -> list[str]:
        parameters = []
        previous_arg_forces_named = False
        for name, value in interaction.cbv_parameters.items():
            if not value or value == "undef.":
                previous_arg_forces_named = True
                continue
            if re.match(r"^\*\* ?", name):
                escaped_value = RfTestCase.escape_argument_value(value, False, False)
                parameters.append(escaped_value)
            elif re.match(r"^\* ?", name):
                escaped_value = RfTestCase.escape_argument_value(value, False)
                parameters.append(escaped_value)
                previous_arg_forces_named = True
            elif re.search(r"(^-\ ?|=$)", name) or previous_arg_forces_named:
                escaped_value = RfTestCase.escape_argument_value(value, equal_sign_escaping=False)
                pure_name = re.sub(r"(^-\ ?|=$)", "", name)
                parameters.append(f"{pure_name}={escaped_value}")
                previous_arg_forces_named = True
            elif value.find("=") != -1 and value[: value.find("=")] in interaction.cbv_parameters:
                escaped_value = RfTestCase.escape_argument_value(value)
                parameters.append(escaped_value)
            else:
                escaped_value = RfTestCase.escape_argument_value(value, True, False)
                parameters.append(escaped_value)
        return parameters

    @staticmethod
    def escape_argument_value(value: str, space_escaping=True, equal_sign_escaping=True) -> str:
        if space_escaping:
            value = re.sub(r"^(?= )|(?<= )$|(?<= )(?= )", r"\\", value)
        if equal_sign_escaping:
            value = re.sub(r"(?<!\\)=", r"\=", value)
        return re.sub(r"^#", r"\#", value)

    @staticmethod
    def _create_cbr_parameters(
        interaction: RFInteractionCall,
    ) -> list[str]:
        cbr_parameters = list(
            filter(lambda parameter: parameter != "", interaction.cbr_parameters.values())
        )
        for index, parameter in enumerate(cbr_parameters):
            if not parameter:
                logger.warning(
                    f"Interaction {interaction.name} has undefined CallByReference parameter value."
                )
                continue
            if not parameter.startswith("${"):
                cbr_parameters[index] = f"${{{parameter}}}"
        return cbr_parameters

    def _get_interaction_import_prefix(self, interaction: RFInteractionCall) -> str:
        return (self.config.fully_qualified or False) * f"{interaction.import_prefix}."

    def _get_interaction_indent(self, interaction: RFInteractionCall) -> str:
        return (
            SEPARATOR * interaction.indent
            if self.config.compound_interaction_logging
            in [CompoundInteractionLogging.GROUP, CompoundInteractionLogging.COMMENT]
            else SEPARATOR
        )

    def _create_rf_keyword(self, interaction: RFInteractionCall) -> KeywordCall:
        import_prefix = self._get_interaction_import_prefix(interaction)
        interaction_indent = self._get_interaction_indent(interaction)
        cbv_parameters = self._create_cbv_parameters(interaction)
        cbr_parameters = self._create_cbr_parameters(interaction)
        return KeywordCall.from_params(
            assign=tuple(cbr_parameters),
            name=f"{import_prefix}{interaction.name}",
            args=tuple(cbv_parameters),
            indent=interaction_indent,
        )

    def _create_rf_compound_keyword(
        self,
        interaction: RFInteractionCall,
        compound_interaction_type=CompoundInteractionLogging.COMMENT,
    ) -> Comment | Group:
        interaction_indent = " " * (interaction.indent * 4)
        if Group and compound_interaction_type == CompoundInteractionLogging.GROUP:
            return Group(
                GroupHeader.from_params(interaction.name, indent=interaction_indent),
                end=End.from_params(interaction_indent),
            )

        return Comment.from_params(
            comment=self._generate_compound_interaction_comment(interaction),
            indent=interaction_indent,
        )  # TODO  prio later key=value als named erlauben config?

    @staticmethod
    def _generate_compound_interaction_comment(
        interaction: RFInteractionCall,
    ) -> str:
        cbr_params = SEPARATOR.join(
            [
                f"{param_name}={param_value}"
                for param_name, param_value in interaction.cbr_parameters.items()
            ]
        )
        cbv_params = SEPARATOR.join(
            [
                f"{param_name}={param_value}"
                for param_name, param_value in interaction.cbv_parameters.items()
            ]
        )
        cmd = []
        if cbr_params:
            cmd.append(cbr_params)
        cmd.append(interaction.name)
        if cbv_params:
            cmd.append(cbv_params)
        return f"# {SEPARATOR.join(cmd)}"

    @staticmethod
    def _get_params_by_use_type(
        test_step: InteractionCall, *param_use_types: ParameterEvaluationType
    ) -> dict[str, str]:
        return {
            parameter.name: parameter.value
            for parameter in test_step.spec.callParameters
            if parameter.evaluationType in param_use_types
        }


def create_test_suites(
    test_case_set_catalog: dict[str, TestCaseSet],
    path_resolver: PathResolver,
    config: Configuration,
) -> dict[str, File]:
    if not Group:
        if config.compound_interaction_logging == CompoundInteractionLogging.GROUP:
            logger.warning(
                f"You're using Robot Framework {robot_version.get_full_version()} "
                "which does not support 'Robot Framework Groups'. "
                "Compund interactions are logged as 'COMMENT'. To hide the warning "
                "set the configuration '--logCompoundInteractions' to 'COMMENT' or 'NONE'."
            )
        else:
            logger.debug(
                f"You're using Robot Framework {robot_version.get_full_version()} "
                "which does not support 'Robot Framework Groups'. Consider updating to "
                "newer Robot Framework version to get enhanced logging for compound interactions."
            )
    tcs_paths = path_resolver.tcs_paths
    test_suites = {}
    for uid, test_case_set in test_case_set_catalog.items():
        test_suites[uid] = RobotSuiteFileBuilder(
            test_case_set, tcs_paths[uid], config
        ).create_test_suite_file()
    tt_paths = path_resolver.tt_paths
    for uid, test_theme in path_resolver.tt_catalog.items():
        test_suites[uid] = RobotInitFileBuilder(
            test_theme, tt_paths[uid], config
        ).create_init_file()
    return test_suites


class RobotInitFileBuilder:
    def __init__(
        self,
        test_theme: TestStructureTreeNode,
        tt_path: PurePath,
        config: Configuration,
    ) -> None:
        self.test_theme: TestThemeNode = test_theme
        self.tt_path = PurePath(tt_path)
        self.config = config

    def create_init_file(self) -> File:
        sections = [self._create_setting_section()]
        return File(sections, source=str(self.tt_path / "__init__"))

    def _create_setting_section(self) -> SettingSection:
        setting_section = SettingSection(header=SectionHeader.from_params(Token.SETTING_HEADER))
        setting_section_meta_data = self._get_setting_section_metadata()
        setting_section.body.extend(
            [
                create_meta_data(metadata_name, metadata_value)
                for metadata_name, metadata_value in setting_section_meta_data.items()
            ]
        )
        return setting_section

    def _get_setting_section_metadata(self) -> dict[str, str]:
        meta_data = {
            "UniqueID": self.test_theme.base.uniqueID,
            "Numbering": self.test_theme.base.numbering,
        }
        if self.test_theme.spec:
            meta_data["Specification Status"] = self.test_theme.spec.status.value
        return meta_data


def create_meta_data(name, value):
    tokens = [
        Token(Metadata, "Metadata", 1),
        Token(SEPARATOR, "    ", 2),
        Token("NAME", name, 3),
        Token(SEPARATOR, "    ", 4),
        Token("ARGUMENT", value, 5),
        Token("EOL", "\n", 6),
    ]
    return Metadata(tokens)


class RobotSuiteFileBuilder:
    def __init__(
        self, test_case_set: TestCaseSet, tcs_path: PurePath, config: Configuration
    ) -> None:
        self.test_case_set = test_case_set
        self.tcs_path = tcs_path
        self.config = config
        self._rf_test_cases: list[RfTestCase] = [
            RfTestCase(test_case_details=test_case, config=config)
            for test_case in self.test_case_set.test_cases.values()
        ]
        self.setup_keywords: list[Keyword] = []
        self.teardown_keywords: list[Keyword] = []

    def create_test_suite_file(self) -> File:
        sections = [self._create_setting_section(), self._create_test_case_section()]
        keyword_section = self._create_keywords_section()
        if keyword_section:
            sections[-1].body.extend(SECTION_SEPARATOR)
            sections.append(keyword_section)
        return File(sections, source=str(self.tcs_path))

    def _create_test_case_section(self) -> TestCaseSection:
        test_case_section = TestCaseSection(header=SectionHeader.from_params(Token.TESTCASE_HEADER))
        robot_ast_test_cases = []
        for index, test_case in enumerate(self._rf_test_cases):
            logger.debug(f"Processing test case: {test_case.uid}")
            robot_ast_test_cases.extend(test_case.to_robot_ast_test_cases())
            if index != len(self._rf_test_cases) - 1:
                robot_ast_test_cases[-1].body.extend(LINE_SEPARATOR)
            if test_case.setup_keyword:
                self.setup_keywords.append(test_case.setup_keyword)
            if test_case.teardown_keyword:
                self.teardown_keywords.append(test_case.teardown_keyword)
        test_case_section.body.extend(robot_ast_test_cases)
        return test_case_section

    def _create_keywords_section(self) -> KeywordSection | None:
        if not self.setup_keywords and not self.teardown_keywords:
            return None
        keywords_section = KeywordSection(header=SectionHeader.from_params(Token.KEYWORD_HEADER))
        keywords_section.body.extend(self.setup_keywords)
        keywords_section.body.extend(self.teardown_keywords)
        return keywords_section

    def _get_used_subdivisions(self) -> dict[str, set[str]]:
        import_dict: dict[str, set[str]] = {}
        for test_case in self._rf_test_cases:
            for root, import_names in test_case.used_imports.items():
                if root not in import_dict:
                    import_dict[root] = import_names
                else:
                    import_dict[root].update(import_names)
        return import_dict

    def _create_rf_variable_imports(self) -> list[VariablesImport]:
        return [
            VariablesImport.from_params(name=variable_file)
            for variable_file in self.config.forced_import.variables
        ]

    def _create_rf_resource_imports(self, import_dict: dict[str, set[str]]) -> list[ResourceImport]:
        resources = {
            str(resource)
            for resource_root, resources in import_dict.items()
            for resource in resources
            if not self._is_library(resource_root) and self._is_resource(resource_root)
        }
        resources.update(self.config.forced_import.resources)
        resource_paths = {
            self._create_resource_path(resource) for resource in sorted(resources)
        }  # TODO Fix Paths to correct models
        return [ResourceImport.from_params(res) for res in sorted(resource_paths)]

    def _get_resource_name(self, resource: str) -> str | None:
        resource_path_part = resource.split(".")[-1]
        for resource_regex in self.config.resource_regex:
            resource_name_match = re.search(resource_regex, resource_path_part, flags=re.IGNORECASE)
            if resource_name_match:
                return resource_name_match.group("resourceName").strip()
        return None

    def _get_resource_directory_path_index(self, resource: str) -> int | None:
        splitted_interaction_path = resource.split(".")
        for index, part in enumerate(splitted_interaction_path):
            resource_directory_match = re.match(
                self.config.resource_directory_regex, part, flags=re.IGNORECASE
            )
            if resource_directory_match:
                return index
        return None

    def _get_resource_path_index(self, resource: str) -> int | None:
        return len(resource.split(".")) - 1 if resource else None

    def _create_resource_path(self, resource: str) -> str:
        splitted_interaction_path = resource.split(".")
        resource_dir_index = self._get_resource_directory_path_index(resource)
        resource_name = self._get_resource_name(resource)
        resource_name_index = self._get_resource_path_index(resource)
        cropped_interaction_path = []
        if resource_dir_index is None:
            return f"{resource_name}.resource"
        cropped_interaction_path.extend(
            splitted_interaction_path[resource_dir_index + 1 : resource_name_index]
        )
        resource_path = Path(
            self.config.resource_directory,
            *cropped_interaction_path,
            f"{resource_name}.resource",
        ).as_posix()
        resource_path = self.config.subdivisionsMapping.resources.get(resource_name, resource_path)
        resource_path = re.sub(
            r"^{resourceDirectory}", self.config.resource_directory, resource_path
        )
        root_path = Path(os.curdir).absolute()
        return re.sub(
            RELATIVE_RESOURCE_INDICATOR,
            str(root_path).replace("\\", "/"),
            resource_path,
        )

    def _replace_relative_resource_indicator(self, path: Path | str) -> str:
        root_path = Path(os.curdir).absolute()
        return re.sub(
            RELATIVE_RESOURCE_INDICATOR,
            str(root_path).replace("\\", ROBOT_PATH_SEPARATOR),
            str(path),
            flags=re.IGNORECASE,
        ).replace("\\", ROBOT_PATH_SEPARATOR)

    def _get_relative_resource_directory(self) -> str:
        root_path = Path(os.curdir).absolute()
        return re.sub(
            RELATIVE_RESOURCE_INDICATOR,
            str(root_path).replace("\\", ROBOT_PATH_SEPARATOR),
            self.config.resource_directory,
            flags=re.IGNORECASE,
        ).replace("\\", ROBOT_PATH_SEPARATOR)

    @staticmethod
    def _is_library(root_subdivision: str) -> bool:
        return root_subdivision == LIBRARY_IMPORT_TYPE

    @staticmethod
    def _is_resource(root_subdivision: str) -> bool:
        return root_subdivision == RESOURCE_IMPORT_TYPE

    def _create_rf_library_imports(self, import_dict: dict[str, set[str]]) -> list[LibraryImport]:
        libraries = {
            str(library)
            for library_root, libraries in import_dict.items()
            for library in libraries
            if self._is_library(library_root)
        }
        libraries.update(self.config.forced_import.libraries)
        lib_imports = {
            self.config.subdivisionsMapping.libraries.get(library, library) for library in libraries
        }
        return [LibraryImport.from_params(lib) for lib in sorted(lib_imports)]

    def _create_rf_test_tags(self) -> TestTags | None:
        tb_keyword_names = [keyword.name for keyword in self.test_case_set.details.spec.keywords]
        udfs = [
            robot_tag_from_udf(udf)
            for udf in self.test_case_set.details.spec.udfs
            if robot_tag_from_udf(udf)
        ]
        test_tags = tb_keyword_names + udfs
        if test_tags:
            return TestTags.from_params(test_tags)
        return None

    def _create_rf_unknown_imports(self, import_dict: dict[str, set[str]]) -> list[Comment]:
        unknown_imports = {
            str(unknown_import)
            for root_subdivision, unknown_imports in import_dict.items()
            for unknown_import in unknown_imports
            if not self._is_library(root_subdivision) and not self._is_resource(root_subdivision)
        }
        if unknown_imports:
            logger.warning(
                f"{self.test_case_set.details.uniqueID} has unknown imports. "
                "TestBench Subdivisions which correspond to Libraries or Resources "
                "must be mapped via on of the following config options: 'rfLibraryRegex', "
                "'rfResourceRegex', 'rfLibraryRoots', 'rfResourceRoots'. "
                "The following subdivisions could not be identified "
                f"as library or resource: {list(unknown_imports)}."
            )
        return [
            Comment.from_params(comment=f"# UNKNOWN    {unknown}", indent="")
            for unknown in unknown_imports
        ]

    def _create_setting_section(self) -> SettingSection:
        subdivisions = self._get_used_subdivisions()
        setting_section = SettingSection(header=SectionHeader.from_params(Token.SETTING_HEADER))
        setting_section.body.extend(self._create_rf_variable_imports())
        setting_section.body.extend(self._create_rf_library_imports(subdivisions))
        setting_section.body.extend(self._create_rf_resource_imports(subdivisions))
        setting_section.body.extend(self._create_rf_unknown_imports(subdivisions))
        setting_section_meta_data = self.test_case_set.metadata
        setting_section.body.extend(
            [
                create_meta_data(metadata_name, metadata_value)
                for metadata_name, metadata_value in setting_section_meta_data.items()
            ]
        )
        setting_section.body.append(self._create_rf_test_tags())
        setting_section.body.extend(SECTION_SEPARATOR)
        return setting_section
