from dataclasses import dataclass
from enum import Enum

import pytest

from testbench2robotframework.model_utils import from_dict


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


def test_unknown_enum_value_is_rejected():
    with pytest.raises(TypeError):
        from_dict(Outer, {"key": "1", "status": "NewStatus"})


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
