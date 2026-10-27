from dataclasses import fields, is_dataclass
from enum import Enum
from functools import cache
from types import UnionType as TypesUnion
from typing import Any, TypeVar, get_args, get_origin, get_type_hints
from typing import Union as TypingUnion

from .log import logger

T = TypeVar("T")

ERROR_NOT_A_DATACLASS = "The provided class '{dataclass}' is not a dataclass."
ERROR_UNKNOWN_TYPE_HINT_ORIGIN = "Unknown type hint origin."
ERROR_UNION_MISMATCH = "Value does not match any of the union types."
ERROR_NOT_A_LIST = "Value is not of type list."
ERROR_LIST_ARGUMENTS_MISMATCH = "List type hint must have exactly one argument, got {args}."
ERROR_UNION_WITHOUT_ARGUMENTS = "Union type hint must have at least one argument."
ERROR_NONETYPE_DATA = "Data cannot be None."


class Origin(Enum):
    NO_ORIGIN = "NO_ORIGIN"
    UNION = "UNION"
    LIST = "LIST"


PRIMITIVE_TYPES = (int, float, str, bool)
DISCRIMINATOR_FIELD = "elementType"
UNKNOWN_FIELDS_ATTRIBUTE = "_unknown_fields"

_unknown_enum_members: dict[tuple[type, Any], Enum] = {}


class ListWithUnreadItems(list):
    """A list that keeps the items of an unknown type, so 'to_dict' can write them back."""

    def __init__(self, items=(), unread_items: list | None = None) -> None:
        super().__init__(items)
        self.unread_items = unread_items or []


def get_origin_from_type_hint(type_hint):
    type_hint_origin = get_origin(type_hint)
    if type_hint_origin is None:
        return Origin("NO_ORIGIN")
    if type_hint_origin is TypesUnion or type_hint_origin is TypingUnion:
        return Origin("UNION")
    if type_hint_origin is list:
        return Origin("LIST")
    raise ValueError(ERROR_UNKNOWN_TYPE_HINT_ORIGIN)


@cache
def _type_hints_and_fields(cls: type) -> tuple[dict[str, Any], tuple, frozenset[str]]:
    """Resolved annotations and fields of a dataclass, computed once per class.

    'get_type_hints' evaluates every annotation anew on each call - with lazy
    annotations (Python 3.14) that means compiling the forward references again.
    A report holds hundreds of thousands of model objects, so this dominated the
    whole read time before it was cached.
    """
    class_fields = fields(cls)
    return get_type_hints(cls), class_fields, frozenset(f.name for f in class_fields)


def from_dict(cls: type[T], data: dict) -> T:
    if not isinstance(cls, type) or not is_dataclass(cls):
        raise ValueError(ERROR_NOT_A_DATACLASS.format(dataclass=cls.__name__))
    if data is None:
        raise ValueError(ERROR_NONETYPE_DATA)
    cls_dict = {}
    class_type_hints, class_fields, field_names = _type_hints_and_fields(cls)
    for cls_field in class_fields:
        if cls_field.name not in data:
            continue
        field_value = data.get(cls_field.name)
        field_type_hint = class_type_hints[cls_field.name]
        cls_dict[cls_field.name] = convert_value(field_value, field_type_hint)
    instance = cls(**cls_dict)
    # Fields of newer TestBench versions are kept, so 'to_dict' writes them back.
    if len(data) > len(cls_dict):
        unknown_fields = {key: value for key, value in data.items() if key not in field_names}
        object.__setattr__(instance, UNKNOWN_FIELDS_ATTRIBUTE, unknown_fields)
    return instance


def to_dict(value: Any) -> Any:
    """Like 'dataclasses.asdict', but also writes back what 'from_dict' did not know."""
    if is_dataclass(value) and not isinstance(value, type):
        result = {
            cls_field.name: to_dict(getattr(value, cls_field.name)) for cls_field in fields(value)
        }
        result.update(getattr(value, UNKNOWN_FIELDS_ATTRIBUTE, {}))
        return result
    if isinstance(value, list):
        return [to_dict(item) for item in value] + getattr(value, "unread_items", [])
    if isinstance(value, dict):
        return {key: to_dict(item) for key, item in value.items()}
    return value


def convert_value_without_origin(value: Any, type_hint: Any) -> Any:
    if value is None:
        return None
    if isinstance(type_hint, type) and is_dataclass(type_hint):
        return from_dict(type_hint, value)
    if isinstance(type_hint, type) and issubclass(type_hint, Enum):
        return _convert_enum_value(value, type_hint)
    return type_hint(value)


def _convert_enum_value(value: Any, enum_type: type[Enum]) -> Enum:
    """Keeps values a newer TestBench version added as a pseudo member of the enum.

    The pseudo member has '.value' like a real one but equals none of them.
    """
    try:
        return enum_type(value)
    except ValueError:
        pass
    member = _unknown_enum_members.get((enum_type, value))
    if member is None:
        logger.warning(
            f"Unknown value '{value}' of '{enum_type.__name__}' in the TestBench report. "
            "It is kept as is."
        )
        member = object.__new__(enum_type)
        member._name_ = str(value)
        member._value_ = value
        # Python 3.10 deep-copies enum members by value, which fails for a pseudo member.
        member.__deepcopy__ = lambda memo: member
        _unknown_enum_members[(enum_type, value)] = member
    return member


def convert_value_with_union_type(value: Any, type_hint: Any) -> Any:
    args = get_args(type_hint)
    if value is None:
        if args and type(None) in args:
            return None
        raise TypeError(ERROR_UNION_MISMATCH)
    if len(args) == 0:
        raise TypeError(ERROR_UNION_WITHOUT_ARGUMENTS)
    if isinstance(value, dict):
        dataclass_args = [arg for arg in args if isinstance(arg, type) and is_dataclass(arg)]
        if dataclass_args:
            return _convert_dict_to_union_member(value, dataclass_args)
    primitive_args = []
    for arg in args:
        if arg in PRIMITIVE_TYPES:
            primitive_args.append(arg)
            continue
        try:
            return convert_value(value, arg)
        except (TypeError, ValueError):
            continue
    for arg in primitive_args:
        try:
            return convert_value(value, arg)
        except (TypeError, ValueError):
            continue
    raise TypeError(ERROR_UNION_MISMATCH)


def _convert_dict_to_union_member(value: dict, dataclass_args: list[type]) -> Any:
    """Pick the union member a dict belongs to.

    Unknown fields are ignored, so several members may accept the same dict.
    The 'elementType' discriminator decides if present, otherwise the member
    that leaves the fewest keys unused wins.
    """
    element_type = value.get(DISCRIMINATOR_FIELD)
    for arg in dataclass_args:
        if arg.__name__ == element_type:
            return from_dict(arg, value)
    best_match, fewest_unused_keys = None, None
    for arg in dataclass_args:
        try:
            candidate = from_dict(arg, value)
        except (TypeError, ValueError):
            continue
        field_names = _type_hints_and_fields(arg)[2]
        unused_keys = len(value.keys() - field_names)
        if fewest_unused_keys is None or unused_keys < fewest_unused_keys:
            best_match, fewest_unused_keys = candidate, unused_keys
        if unused_keys == 0:
            break
    if best_match is None:
        raise TypeError(ERROR_UNION_MISMATCH)
    return best_match


def convert_value_with_list_type(value: Any, type_hint: Any) -> Any:
    if not isinstance(value, list):
        raise TypeError(ERROR_NOT_A_LIST)
    args = get_args(type_hint)
    if len(args) != 1:
        raise TypeError(ERROR_LIST_ARGUMENTS_MISMATCH.format(args=len(args)))
    list_item_type_hint = args[0]
    items, unread_items = [], []
    for item in value:
        if _has_unknown_element_type(item, list_item_type_hint):
            logger.warning(
                f"Skipped an element of the unknown type '{item[DISCRIMINATOR_FIELD]}' "
                "in the TestBench report."
            )
            unread_items.append(item)
            continue
        items.append(convert_value(item, list_item_type_hint))
    return ListWithUnreadItems(items, unread_items) if unread_items else items


def _has_unknown_element_type(item: Any, type_hint: Any) -> bool:
    """True for a list item whose 'elementType' names no member of the union.

    That is e.g. a node type a newer TestBench version added to the test structure tree.
    """
    if not isinstance(item, dict) or DISCRIMINATOR_FIELD not in item:
        return False
    if get_origin_from_type_hint(type_hint) is not Origin.UNION:
        return False
    dataclass_names = {arg.__name__ for arg in get_args(type_hint) if is_dataclass(arg)}
    return bool(dataclass_names) and item[DISCRIMINATOR_FIELD] not in dataclass_names


def convert_value(value: Any, type_hint: Any) -> Any:
    origin = get_origin_from_type_hint(type_hint)
    if origin is Origin.NO_ORIGIN:
        return convert_value_without_origin(value, type_hint)
    if origin is Origin.UNION:
        return convert_value_with_union_type(value, type_hint)
    return convert_value_with_list_type(value, type_hint)
