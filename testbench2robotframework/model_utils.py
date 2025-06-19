from dataclasses import fields, is_dataclass
from enum import Enum
from types import UnionType as TypesUnion
from typing import Any, Optional, TypeVar, get_args, get_origin, get_type_hints
from typing import Union as TypingUnion

from testbench2robotframework.model import UDFType, UserDefinedField

T = TypeVar("T")


class Origin(Enum):
    NO_ORIGIN = "NO_ORIGIN"
    UNION = "UNION"
    LIST = "LIST"


def get_origin_from_type_hint(type_hint):
    type_hint_origin = get_origin(type_hint)
    if type_hint_origin is None:
        return Origin("NO_ORIGIN")
    if type_hint_origin is TypesUnion or type_hint_origin is TypingUnion:
        return Origin("UNION")
    if type_hint_origin is list:
        return Origin("LIST")
    raise ValueError("Unknown type hint origin.")


def from_dict(cls: type[T], data: dict) -> T:
    if not is_dataclass(cls):
        raise ValueError(f"{cls.__name__} is not a dataclass.")
    cls_dict = {}
    class_type_hints = get_type_hints(cls)
    for cls_field in fields(cls):
        if cls_field.name not in data:
            continue
        field_value = data.get(cls_field.name)
        field_type_hint = class_type_hints[cls_field.name]
        cls_dict[cls_field.name] = convert_value(field_value, field_type_hint)
    return cls(**cls_dict)


def convert_value_without_origin(value: Any, type_hint: Any) -> Any:
    if is_dataclass(type_hint):
        return from_dict(type_hint, value)
    return type_hint(value)


def convert_value_with_union_type(value: Any, type_hint: Any) -> Any:
    args = get_args(type_hint)
    if value is None:
        if args and type(None) in args:
            return None
        raise TypeError("Value does not match any of the union types.")
    if len(args) == 0:
        raise TypeError("Union type has no arguments.")
    for arg in args:
        try:
            return convert_value(value, arg)
        except (TypeError, ValueError):
            continue
    raise TypeError("Value does not match any of the union types.")


def convert_value_with_list_type(value: Any, type_hint: Any) -> Any:
    if not isinstance(value, list):
        raise TypeError("Value is not of type list.")
    args = get_args(type_hint)
    if len(args) != 1:
        raise TypeError(f"List type hint must have exactly one argument, got {args}.")
    list_item_type_hint = args[0]
    return [convert_value(item, list_item_type_hint) for item in value]


def convert_value(value: Any, type_hint: Any) -> Any:
    origin = get_origin_from_type_hint(type_hint)
    if origin is Origin.NO_ORIGIN:
        return convert_value_without_origin(value, type_hint)
    if origin is Origin.UNION:
        return convert_value_with_union_type(value, type_hint)
    return convert_value_with_list_type(value, type_hint)

def robot_tag_from_udf(udf: UserDefinedField) -> Optional[str]:
    if (udf.udfType == UDFType.Enumeration and udf.value) or (
        udf.udfType == UDFType.String and udf.value
    ):
        return f"{udf.name}:{udf.value}"
    if udf.udfType == UDFType.Boolean and udf.value == "true":
        return udf.name
    return None