import types
from dataclasses import fields, is_dataclass
from enum import Enum
from typing import Any, Optional, TypeVar, Union, get_args, get_origin, get_type_hints

from testbench2robotframework.model import UDFType, UserDefinedField

T = TypeVar("T")


def get_field_types(field_type):
    origin = get_origin(field_type)
    if origin is types.UnionType or origin is Union:
        args = get_args(field_type)
        return [arg for arg in args if arg is not type(None)]
    return [field_type]


def robot_tag_from_udf(udf: UserDefinedField) -> Optional[str]:
    if (udf.udfType == UDFType.Enumeration and udf.value) or (
        udf.udfType == UDFType.String and udf.value
    ):
        return f"{udf.name}:{udf.value}"
    if udf.udfType == UDFType.Boolean and udf.value == "true":
        return udf.name
    return None


def convert_enum_value(value, field_type):
    if (
        value is not None
        and isinstance(value, (str, int))
        and isinstance(field_type, type)
        and issubclass(field_type, Enum)
    ):
        try:
            return field_type(value)
        except ValueError:
            pass
    return value


def convert_nested_dictionary(value, field_type):
    if is_dataclass(field_type) and isinstance(value, dict):
        return from_dict(field_type, value)
    return value


def convert_list_items(value, field_type):
    origin = get_origin(field_type)
    if not (isinstance(value, list) and origin is list):
        return value
    args = get_args(field_type)
    if not (args and len(args) == 1):
        raise TypeError(f"Expected a single type argument for list, got {args} in {field_type}")
    item_type = args[0]
    if is_dataclass(item_type):
        return [from_dict(item_type, item) for item in value if isinstance(item, dict)]
    if isinstance(item_type, type) and issubclass(item_type, Enum):
        return [item_type(item) for item in value if isinstance(item, (str, int))]
    if get_origin(item_type) is types.UnionType or get_origin(item_type) is Union:
        list_items = []
        possible_types = get_args(item_type)
        for item in value:
            for possible_type in possible_types:
                try:
                    temp = from_dict(possible_type, item)
                    list_items.append(temp)
                    break
                except (TypeError, ValueError):
                    continue
                raise TypeError(
                    f"Item {item} in list does not match any of the possible types {possible_types}"
                )
        return list_items
    return value


def convert_field_value(value, type_hints):
    if value is None:
        return None
    type_hints = get_field_types(type_hints)
    for type_hint in type_hints:
        value = convert_enum_value(value, type_hint)
        value = convert_nested_dictionary(value, type_hint)
        value = convert_list_items(value, type_hint)
    return value


def from_dict(cls: type[T], data: dict) -> T:
    if not is_dataclass(cls):
        raise ValueError(f"{cls.__name__} is not a dataclass")
    type_hints = get_type_hints(cls)
    cls_dict = {}
    for field in fields(cls):
        if field.name not in data:
            continue
        field_value = data.get(field.name)
        field_type_hints = type_hints.get(field.name, Any)
        cls_dict[field.name] = convert_field_value(field_value, field_type_hints)
    return cls(**cls_dict)
