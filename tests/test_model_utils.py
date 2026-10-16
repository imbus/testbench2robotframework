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
