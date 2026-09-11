"""Rules for 'library-regex' / 'resource-regex' patterns.

1. A named group out of SUPPORTED_NAME_GROUPS marks the name. It wins, no
   matter how many capture groups the pattern has.
2. Without such a group the pattern must have exactly one capture group, which
   is then the name.
3. Anything else is rejected with an error naming both ways out.
"""

import re

import pytest

from testbench2robotframework.testbench2rf import (
    SUPPORTED_NAME_GROUPS,
    RfTestCase,
    get_matched_name,
)

validate = RfTestCase._validate_regex_pattern

DEFAULT_LIBRARY_PATTERN = r"(?:.*\.)?(?P<resourceName>[^.]+?)\s*\[Robot-Library\].*"


def name_of(pattern, text):
    match = re.compile(pattern, re.IGNORECASE).search(text)
    assert match, f"pattern {pattern!r} did not match {text!r}"
    return get_matched_name(match)


def test_supported_names_are_a_documented_ordered_list():
    assert SUPPORTED_NAME_GROUPS == ("resourceName", "libraryName", "name")


# --- rule 1: named group wins ------------------------------------------------


@pytest.mark.parametrize("group_name", SUPPORTED_NAME_GROUPS)
def test_named_group_wins_regardless_of_its_position(group_name):
    pattern = rf"(?P<prefix>[A-Z]+)-(?P<{group_name}>\w+)"
    validate(pattern, "library")

    assert name_of(pattern, "LIB-SeleniumLibrary") == "SeleniumLibrary"


@pytest.mark.parametrize("group_name", SUPPORTED_NAME_GROUPS)
def test_named_group_also_wins_as_the_first_group(group_name):
    pattern = rf"(?P<{group_name}>\w+)\s*\((?P<version>v\d+)\)"
    validate(pattern, "resource")

    assert name_of(pattern, "SeleniumLibrary (v6)") == "SeleniumLibrary"


def test_first_supported_name_wins_when_several_are_present():
    pattern = r"(?P<name>[A-Z]+)-(?P<resourceName>\w+)"
    validate(pattern, "library")

    assert name_of(pattern, "LIB-SeleniumLibrary") == "SeleniumLibrary"


def test_named_group_that_did_not_participate_falls_back_to_group_one():
    pattern = r"(\w+)(?:-(?P<resourceName>\w+))?"

    assert name_of(pattern, "SeleniumLibrary") == "SeleniumLibrary"


# --- rule 2: exactly one capture group --------------------------------------


def test_single_unnamed_group_is_the_name():
    pattern = r"(.*?)\s*\[Robot-Library\]"
    validate(pattern, "library")

    assert name_of(pattern, "SeleniumLibrary [Robot-Library]") == "SeleniumLibrary"


def test_single_group_with_an_unsupported_name_is_still_the_name():
    pattern = r"(?P<whatever>.*?)\s*\[Robot-Library\]"
    validate(pattern, "library")

    assert name_of(pattern, "SeleniumLibrary [Robot-Library]") == "SeleniumLibrary"


def test_non_capturing_groups_do_not_count():
    pattern = r"(?:RF\.)?(\w+)"
    validate(pattern, "resource")

    assert name_of(pattern, "RF.SeleniumLibrary") == "SeleniumLibrary"


def test_shipped_default_pattern_still_works():
    validate(DEFAULT_LIBRARY_PATTERN, "library")

    assert name_of(DEFAULT_LIBRARY_PATTERN, "Sub.SeleniumLibrary [Robot-Library]") == (
        "SeleniumLibrary"
    )


# --- rule 3: everything else is rejected -------------------------------------


def test_pattern_without_any_capture_group_is_rejected():
    with pytest.raises(ValueError, match="does not tell which part is the name"):
        validate(r".*\[Robot-Library\]", "library")


def test_several_groups_without_a_supported_name_are_rejected():
    with pytest.raises(ValueError) as error:
        validate(r"([A-Z]+)-(\w+)", "resource")

    message = str(error.value)
    assert "resourceName" in message  # the error names the way out
    assert "exactly one capture group" in message
    assert "2 capture groups" in message


def test_invalid_regex_is_rejected_with_the_original_error_chained():
    with pytest.raises(ValueError, match="Invalid library regex pattern") as error:
        validate(r"(unbalanced", "library")

    assert isinstance(error.value.__cause__, re.error)


# --- configured metadata ------------------------------------------------------


def test_configured_metadata_reaches_the_suite(tmp_path):
    """The 'metadata' option was silently ignored once; guard the fix."""
    from testbench2robotframework.config import Configuration
    from testbench2robotframework.json_reader import TestCaseSet
    from testbench2robotframework.model import (
        TestCaseSetDetails,
        TestCaseSetExecutionSummary,
        TestCaseSetSpecificationSummary,
    )
    from testbench2robotframework.model_utils import from_dict
    from testbench2robotframework.testbench2rf import RobotSuiteFileBuilder

    details = from_dict(
        TestCaseSetDetails,
        {
            "key": "300",
            "numbering": "1.1",
            "path": "Set",
            "uniqueID": "itb-TC-1",
            "name": "Set",
            "spec": {
                "key": "301",
                "description": "",
                "reviewComment": "",
                "status": "NotPlanned",
                "priority": "Middle",
                "preConditions": [],
                "postConditions": [],
                "udfs": [],
                "tags": [],
                "references": [],
                "requirements": [],
            },
            "testCases": [],
            "testSequence": [],
            "parameters": [],
            "keywords": [],
        },
    )
    config = Configuration.from_dict({"metadata": {"MyKey": "MyValue", "UniqueID": "evil"}})
    builder = RobotSuiteFileBuilder(TestCaseSet(details, {}), "1__Set", config)

    metadata = {
        statement.tokens[2].value: statement.tokens[4].value
        for statement in builder._create_setting_section().body
        if statement.__class__.__name__ == "Metadata"
    }

    assert metadata["MyKey"] == "MyValue"
    assert metadata["UniqueID"] == "itb-TC-1"  # reserved name is not overridden


def test_metadata_placeholders_are_interpolated():
    """Issue #5: metadata values may pull data out of the test case set model."""
    from testbench2robotframework.utils import interpolate_metadata_value

    class Node:
        def __init__(self, **kw):
            self.__dict__.update(kw)

    tcs = Node(spec=Node(responsible=Node(name="R. Rohlfing"), status="Released"))

    value = interpolate_metadata_value(
        "Responsible: {$tcs.spec.responsible.name} ({$tcs.spec.status})", {"tcs": tcs}
    )

    assert value == "Responsible: R. Rohlfing (Released)"


def test_broken_metadata_placeholder_stays_literal():
    from testbench2robotframework.utils import interpolate_metadata_value

    class Node:
        spec = None

    assert (
        interpolate_metadata_value("{$tcs.spec.missing}", {"tcs": Node()})
        == "{$tcs.spec.missing}"
    )


def test_metadata_placeholders_cannot_call_or_compute():
    """The evaluator only walks attributes and constant subscripts."""
    from testbench2robotframework.utils import interpolate_metadata_value

    dangerous = interpolate_metadata_value("{$tcs.__class__}", {"tcs": object()})
    call = interpolate_metadata_value("{$tcs.spec.udfs.pop()}", {"tcs": object()})

    assert dangerous == "{$tcs.__class__}"  # private attributes refused
    assert call == "{$tcs.spec.udfs.pop()}"  # calls refused


def test_group_names_with_consecutive_spaces_survive_parsing():
    """Issue #17: 'GROUP    Expand  Panel' parses as two arguments and fails."""
    try:
        from robot.parsing.model.statements import GroupHeader  # noqa: F401
    except ImportError:
        pytest.skip("GROUP syntax needs Robot Framework >= 7.2")
    from robot.api import TestSuite

    from testbench2robotframework.testbench2rf import escape_consecutive_spaces

    for original in ("Expand  Panel", "Drei   Spaces", "Vier    Spaces"):
        escaped = escape_consecutive_spaces(original)
        source = f"*** Test Cases ***\nTC\n    GROUP    {escaped}\n        Log    x\n    END\n"

        group = TestSuite.from_string(source).tests[0].body[0]

        # One single argument again, and the escape resolves back to the name.
        assert group.name.replace("\\ ", " ") == original


# --- resource-directory-regex: marker pattern ---------------------------------


def make_rf_test_case(config):
    from types import SimpleNamespace as Node

    from testbench2robotframework.testbench2rf import RfTestCase

    details = Node(uniqueID="itb-TC-1-PC-1", testSequence=[], keywords=[], spec=Node(tags=[], udfs=[]))
    return RfTestCase(details, config)


def test_invalid_resource_directory_regex_is_rejected_at_startup():
    from testbench2robotframework.config import Configuration

    config = Configuration.from_dict({"resource-directory-regex": "(unbalanced"})

    with pytest.raises(ValueError, match="resource-directory-regex") as error:
        make_rf_test_case(config)

    assert isinstance(error.value.__cause__, re.error)


def test_marker_pattern_needs_no_capture_group():
    """Unlike library-regex/resource-regex, the marker only locates a segment."""
    from testbench2robotframework.config import Configuration

    make_rf_test_case(Configuration.from_dict({"resource-directory-regex": r"\[Robot-Resources\]"}))


def test_marker_pattern_matches_anywhere_in_the_segment():
    """re.search semantics: no '.*' prefix needed to hit mid-segment."""
    from testbench2robotframework.config import Configuration
    from testbench2robotframework.testbench2rf import RobotSuiteFileBuilder

    class Builder(RobotSuiteFileBuilder):
        def __init__(self, config):
            self.config = config

    config = Configuration.from_dict(
        {"resource-directory-regex": r"\[Robot-Resources\]", "resource-directory": "res"}
    )

    path = Builder(config)._create_resource_path("Root [Robot-Resources].Sub.Common [Robot-Resource]")

    assert path.replace("\\", "/").endswith("res/Sub/Common.resource")
