"""Configuration is part of the public API - users build it in code.

Options added after the initial release must therefore be optional and
keyword-only, so that existing code constructing a Configuration keeps working
and the new options can be reordered later without breaking anyone.
"""

import pytest
from dataclasses import MISSING, fields

from testbench2robotframework.config import (
    AttachmentConflictBehaviour,
    CompoundKeywordLogging,
    Configuration,
    ForcedImport,
    LoggingConfig,
    ReferenceBehaviour,
    SubdivisionsMapping,
)

OPTIONS_ADDED_LATER = ["include_blocked", "merge_protocol", "clean_mode"]


def build_configuration_without_new_options() -> Configuration:
    """Builds a Configuration the way library code written before the new options did."""
    return Configuration(
        attachmentConflictBehaviour=AttachmentConflictBehaviour.USE_EXISTING,
        clean=True,
        compound_keyword_logging=CompoundKeywordLogging.GROUP,
        create_output_zip=False,
        forced_import=ForcedImport.from_dict({}),
        fully_qualified=False,
        library_regex=[],
        library_root=[],
        log_suite_numbering=False,
        loggingConfiguration=LoggingConfig.from_dict({}),
        metadata={},
        output_directory="Generated",
        phase_pattern="{testcase} : Phase {index}/{length}",
        referenceBehaviour=ReferenceBehaviour.ATTACHMENT,
        resource_directory="resources",
        resource_directory_regex="",
        resource_regex=[],
        resource_root=[],
        subdivisionsMapping=SubdivisionsMapping.from_dict({}),
        testCaseSplitPathRegEx="",
    )


def test_new_options_have_defaults():
    defaults = {
        field.name: field.default for field in fields(Configuration) if field.name in OPTIONS_ADDED_LATER
    }

    from testbench2robotframework.config import CleanMode

    assert defaults == {
        "include_blocked": False,
        "merge_protocol": True,
        "clean_mode": CleanMode.GENERATED,
    }


def test_no_new_option_is_a_required_field():
    required = [field.name for field in fields(Configuration) if field.default is MISSING]

    assert not set(OPTIONS_ADDED_LATER) & set(required)


def test_new_options_are_keyword_only():
    kw_only = {
        field.name: field.kw_only for field in fields(Configuration) if field.name in OPTIONS_ADDED_LATER
    }

    assert kw_only == {"include_blocked": True, "merge_protocol": True, "clean_mode": True}


def test_new_options_cannot_be_passed_positionally():
    with pytest.raises(TypeError):
        Configuration(*[None] * (len(fields(Configuration)) - len(OPTIONS_ADDED_LATER)), False)


def test_configuration_can_be_built_without_the_new_options():
    configuration = build_configuration_without_new_options()

    assert configuration.include_blocked is False
    assert configuration.merge_protocol is True


def test_new_options_can_be_set_by_keyword():
    configuration = build_configuration_without_new_options()
    configuration.include_blocked = True

    assert Configuration.from_dict({"include-blocked": True}).include_blocked is True
    assert Configuration.from_dict({"merge-protocol": False}).merge_protocol is False
    assert configuration.include_blocked is True
