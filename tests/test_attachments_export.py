"""Exporting the report's attachments next to the generated suites.

'attachments-directory' says where the report's 'attachments/' folder is copied
to. A relative path lives inside the output directory and every suite gets a
variable pointing there relative to itself, so the output stays movable. An
absolute path is used as it is - in the copy and in the variable.
"""

import zipfile
from pathlib import Path, PurePath
from types import SimpleNamespace

import pytest
from test_attachment_parameters import DATATYPE, keyword_call, parameter
from test_tree_verdicts import item_base, item_exec

from testbench2robotframework.attachments import (
    AttachmentsExport,
    attachments_export,
    copy_attachments,
    variable_value,
)
from testbench2robotframework.config import Configuration
from testbench2robotframework.model import (
    KeywordType,
    RepresentativeType,
    TestCaseDetails,
    TestStructureElementType,
    TestThemeNode,
)
from testbench2robotframework.testbench2rf import (
    RfTestCase,
    RobotInitFileBuilder,
    attachments_variable_section,
)
from testbench2robotframework.testsuite_write import write_test_suites


def config(**overrides) -> Configuration:
    return Configuration.from_dict({"output-directory": "{root}/Generated", **overrides})


@pytest.fixture(autouse=True)
def run_in_tmp_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


class ResolvingTheTargetTests:
    def test_no_directory_means_no_export(self):
        assert attachments_export(config()) is None

    def test_relative_path_lives_in_the_output_directory(self, tmp_path):
        export = attachments_export(config(**{"attachments-directory": "attachments"}))
        assert export.target == tmp_path / "Generated" / "attachments"
        assert export.relative_to_output == PurePath("attachments")

    def test_nested_relative_path(self, tmp_path):
        export = attachments_export(config(**{"attachments-directory": "data/att"}))
        assert export.target == tmp_path / "Generated" / "data" / "att"
        assert export.relative_to_output == PurePath("data/att")

    def test_absolute_path_is_used_as_given(self, tmp_path):
        export = attachments_export(
            config(**{"attachments-directory": str(tmp_path / "elsewhere")})
        )
        assert export.target == tmp_path / "elsewhere"
        assert export.relative_to_output is None

    def test_root_placeholder_makes_the_path_absolute(self, tmp_path):
        export = attachments_export(config(**{"attachments-directory": "{root}/att"}))
        assert export.target == tmp_path / "att"
        assert export.relative_to_output is None


class VariableValueTests:
    def test_relative_target_is_addressed_from_the_suite_directory(self):
        export = AttachmentsExport(Path("/out/attachments"), PurePath("attachments"))
        assert variable_value(export, PurePath("1__Theme")) == "${CURDIR}/../attachments"
        assert variable_value(export, PurePath()) == "${CURDIR}/attachments"
        assert variable_value(export, PurePath("1__Theme/2__Sub")) == "${CURDIR}/../../attachments"

    def test_nested_relative_target(self):
        export = AttachmentsExport(Path("/out/data/att"), PurePath("data/att"))
        assert variable_value(export, PurePath("1__Theme")) == "${CURDIR}/../data/att"

    def test_absolute_target_is_written_with_forward_slashes(self):
        export = AttachmentsExport(Path("/data/run 1/attachments"), None)
        assert variable_value(export, PurePath("1__Theme")) == "/data/run 1/attachments"


class CopyingTests:
    def make_report(self, tmp_path):
        report = tmp_path / "report"
        (report / "attachments" / "representatives" / "DT-1").mkdir(parents=True)
        (report / "attachments" / "representatives" / "DT-1" / "a.xml").write_text("a")
        (report / "attachments" / "b.pdf").write_text("b")
        (report / "cycle_structure.json").write_text("{}")
        return report

    def test_whole_attachments_folder_is_copied(self, tmp_path):
        report = self.make_report(tmp_path)
        target = tmp_path / "out" / "attachments"
        copy_attachments(report, target)
        assert (target / "representatives" / "DT-1" / "a.xml").read_text() == "a"
        assert (target / "b.pdf").read_text() == "b"
        assert not (target / "cycle_structure.json").exists()

    def test_target_is_emptied_first(self, tmp_path):
        report = self.make_report(tmp_path)
        target = tmp_path / "out" / "attachments"
        target.mkdir(parents=True)
        (target / "stale.txt").write_text("old")
        copy_attachments(report, target)
        assert not (target / "stale.txt").exists()
        assert (target / "b.pdf").exists()

    def test_report_without_attachments_gives_an_empty_target(self, tmp_path):
        report = tmp_path / "report"
        report.mkdir()
        target = tmp_path / "out" / "attachments"
        copy_attachments(report, target)
        assert target.is_dir()
        assert not any(target.iterdir())


class VariablesSectionInSuitesTests:
    """Only a suite that actually refers to the variable gets it defined."""

    def render(self, file):
        return "".join(
            token.value
            for section in file.sections
            for statement in section.body
            for token in statement.tokens
        ) + "".join(section.header.tokens[0].value for section in file.sections)

    def make_theme(self):
        return TestThemeNode(
            elementType=TestStructureElementType.TestThemeNode,
            base=item_base("200", "100", "itb-TT-1"),
            filters=[],
            exec=item_exec("202"),
        )

    def rf_test_case(self, value, value_type, cfg):
        step = keyword_call(
            "Vorlage holen",
            parameter(value, value_type, data_type=DATATYPE),
            keyword_type=KeywordType.Compound,
        )
        details = TestCaseDetails(
            uniqueID="itb-TC-1-PC-1",
            spec=SimpleNamespace(tags=[], udfs=[]),
            testSequence=[step],
            parameters=[],
            keywords=[],
        )
        return RfTestCase(details, cfg)

    def test_test_case_with_an_attachment_parameter_uses_the_variable(self):
        cfg = config(**{"attachments-directory": "attachments"})
        assert self.rf_test_case(
            "Vorlage.xml", RepresentativeType.Attachment, cfg
        ).uses_attachments_variable
        assert not self.rf_test_case(
            "Vorlage.xml", RepresentativeType.Text, cfg
        ).uses_attachments_variable

    def test_text_that_already_names_the_variable_counts_too(self):
        # The platform's XmlGenerator injects keyword calls whose argument is
        # '${ITB_ATTACHMENTS_DIR}/advancedContent/...' before the suites are generated.
        cfg = config(**{"attachments-directory": "attachments"})
        assert self.rf_test_case(
            "${ITB_ATTACHMENTS_DIR}/advancedContent/IA.xml", RepresentativeType.Text, cfg
        ).uses_attachments_variable

    def test_section_for_a_suite_that_uses_the_variable(self):
        cfg = config(**{"attachments-directory": "attachments"})
        section = attachments_variable_section(cfg, PurePath("1__Theme"), uses_variable=True)
        text = "".join(t.value for st in section.body for t in st.tokens)
        assert section.header.tokens[0].value == "*** Variables ***"
        assert "${ITB_ATTACHMENTS_DIR}    ${CURDIR}/../attachments" in text

    def test_no_section_for_a_suite_without_attachments(self):
        cfg = config(**{"attachments-directory": "attachments"})
        assert attachments_variable_section(cfg, PurePath("1__Theme"), uses_variable=False) is None

    def test_no_section_without_attachments_directory(self):
        assert (
            attachments_variable_section(config(), PurePath("1__Theme"), uses_variable=True) is None
        )

    def test_no_section_when_the_variable_name_is_empty(self):
        cfg = config(**{"attachments-directory": "attachments", "attachments-variable": ""})
        assert attachments_variable_section(cfg, PurePath("1__Theme"), uses_variable=True) is None

    def test_custom_variable_name(self):
        cfg = config(**{"attachments-directory": "attachments", "attachments-variable": "ATT"})
        section = attachments_variable_section(cfg, PurePath("1__Theme"), uses_variable=True)
        assert "${ATT}    ${CURDIR}/../attachments" in "".join(
            t.value for st in section.body for t in st.tokens
        )

    def test_init_file_never_gets_the_variable(self):
        file = RobotInitFileBuilder(
            self.make_theme(),
            PurePath("1__Theme"),
            config(**{"attachments-directory": "attachments"}),
        ).create_init_file()
        assert "*** Variables ***" not in self.render(file)


class ExportDuringGenerationTests:
    def make_report(self, tmp_path):
        report = tmp_path / "report"
        (report / "attachments").mkdir(parents=True)
        (report / "attachments" / "b.pdf").write_text("b")
        return report

    def test_relative_target_lands_in_the_output_directory(self, tmp_path):
        write_test_suites(
            {}, config(**{"attachments-directory": "attachments"}), self.make_report(tmp_path)
        )
        assert (tmp_path / "Generated" / "attachments" / "b.pdf").exists()

    def test_relative_target_lands_inside_a_zip_output(self, tmp_path):
        write_test_suites(
            {},
            config(
                **{"output-directory": "{root}/suites.zip", "attachments-directory": "attachments"}
            ),
            self.make_report(tmp_path),
        )
        assert "attachments/b.pdf" in zipfile.ZipFile(tmp_path / "suites.zip").namelist()

    def test_absolute_target(self, tmp_path):
        write_test_suites(
            {},
            config(**{"attachments-directory": str(tmp_path / "att")}),
            self.make_report(tmp_path),
        )
        assert (tmp_path / "att" / "b.pdf").exists()
        assert not (tmp_path / "Generated" / "attachments").exists()

    def test_nothing_is_copied_without_the_option(self, tmp_path):
        write_test_suites({}, config(), self.make_report(tmp_path))
        assert not (tmp_path / "Generated" / "attachments").exists()
