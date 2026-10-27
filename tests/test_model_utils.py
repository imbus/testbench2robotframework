import copy
import json
import logging
from dataclasses import asdict, dataclass
from enum import Enum

import pytest

from testbench2robotframework import json_codec
from testbench2robotframework.json_codec import dumps
from testbench2robotframework.log import logger
from testbench2robotframework.model_utils import from_dict, to_dict


@pytest.fixture
def warnings_of_logger():
    messages = []
    handler = logging.Handler(logging.WARNING)
    handler.emit = lambda record: messages.append(record.getMessage())
    logger.addHandler(handler)
    yield messages
    logger.removeHandler(handler)


class Status(Enum):
    Released = "Released"


@dataclass
class Inner:
    name: str | None = None


@dataclass
class Outer:
    key: str
    status: Status | None = None
    inner: Inner | None = None


def test_unknown_fields_are_ignored():
    data = {
        "key": "1",
        "status": "Released",
        "inner": {"name": "a", "newInnerField": 1},
        "newField": "value",
    }

    result = from_dict(Outer, data)

    assert result == Outer(key="1", status=Status.Released, inner=Inner(name="a"))


def test_unknown_enum_value_is_kept():
    result = from_dict(Outer, {"key": "1", "status": "NewStatus"})

    assert isinstance(result.status, Status)
    assert result.status.value == "NewStatus"
    assert result.status != Status.Released
    assert from_dict(Outer, {"key": "2", "status": "NewStatus"}).status is result.status


def test_unknown_enum_value_is_warned_once(warnings_of_logger):
    from_dict(Outer, {"key": "1", "status": "OtherStatus"})
    from_dict(Outer, {"key": "2", "status": "OtherStatus"})

    assert len(warnings_of_logger) == 1
    assert "OtherStatus" in warnings_of_logger[0]


def test_unknown_fields_are_written_back():
    data = {
        "key": "1",
        "status": "NewStatus",
        "inner": {"name": "a", "newInnerField": 1},
        "newField": "value",
    }

    assert json.loads(dumps(to_dict(from_dict(Outer, data)))) == data


def test_unchanged_dataclass_is_written_like_asdict():
    result = Outer(key="1", status=Status.Released, inner=Inner(name="a"))

    assert to_dict(result) == asdict(result)


@dataclass
class Root:
    elementType: str
    base: str


@dataclass
class Theme:
    elementType: str
    base: str
    spec: str | None = None


@dataclass
class Tree:
    nodes: list[Root | Theme]


def test_union_member_is_selected_by_element_type():
    data = {"nodes": [{"elementType": "Root", "base": "r"}, {"elementType": "Theme", "base": "t"}]}

    result = from_dict(Tree, data)

    assert result.nodes == [Root(elementType="Root", base="r"), Theme(elementType="Theme", base="t")]


def test_list_item_with_unknown_element_type_is_skipped(warnings_of_logger):
    data = {"nodes": [{"elementType": "Root", "base": "r"}, {"elementType": "Future", "base": "f"}]}

    result = from_dict(Tree, data)

    assert result.nodes == [Root(elementType="Root", base="r")]
    assert any("Future" in message for message in warnings_of_logger)


def test_skipped_list_items_are_written_back():
    data = {"nodes": [{"elementType": "Root", "base": "r"}, {"elementType": "Future", "base": "f"}]}

    assert to_dict(from_dict(Tree, data)) == data


@dataclass
class TovOptions:
    root: str | None = None


@dataclass
class CycleOptions:
    root: str | None = None
    mode: str | None = None


@dataclass
class Job:
    options: TovOptions | CycleOptions


def test_union_member_with_most_matching_fields_is_selected():
    result = from_dict(Job, {"options": {"root": "1", "mode": "Execute", "newField": 1}})

    assert result.options == CycleOptions(root="1", mode="Execute")


def test_unknown_enum_value_is_no_member_of_the_enum():
    from_dict(Outer, {"key": "1", "status": "YetAnotherStatus"})

    assert list(Status) == [Status.Released]
    assert "YetAnotherStatus" not in Status.__members__
    with pytest.raises(ValueError, match="YetAnotherStatus"):
        Status("YetAnotherStatus")


def test_unknown_enum_value_works_as_dict_key_and_copy():
    status = from_dict(Outer, {"key": "1", "status": "KeyStatus"}).status

    assert {status: 1}[status] == 1
    assert copy.deepcopy(status) is status


@dataclass
class Statuses:
    values: list[Status]


def test_unknown_enum_value_in_a_list_is_kept():
    result = from_dict(Statuses, {"values": ["Released", "ListStatus"]})

    assert result.values[0] is Status.Released
    assert result.values[1].value == "ListStatus"


def test_unknown_enum_value_is_written_without_orjson(monkeypatch):
    monkeypatch.setattr(json_codec, "orjson", None)
    result = from_dict(Outer, {"key": "1", "status": "PlainJsonStatus"})

    assert json.loads(json_codec.dumps(to_dict(result)))["status"] == "PlainJsonStatus"


@dataclass
class Roots:
    nodes: list[Root]


def test_element_type_is_only_checked_for_unions():
    result = from_dict(Roots, {"nodes": [{"elementType": "Other", "base": "r"}]})

    assert result.nodes == [Root(elementType="Other", base="r")]


def test_deepcopy_keeps_what_from_dict_did_not_know():
    data = {"nodes": [{"elementType": "Root", "base": "r", "new": None}, {"elementType": "Future"}]}

    copied = copy.deepcopy(from_dict(Tree, data))

    assert to_dict(copied) == data


def test_unknown_field_with_null_value_is_written_back():
    data = {"key": "1", "newField": None}

    assert to_dict(from_dict(Outer, data))["newField"] is None
    assert "newField" in to_dict(from_dict(Outer, data))
