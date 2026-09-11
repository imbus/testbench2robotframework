"""JSON encoding and decoding of report files - with orjson when it is installed.

orjson (Rust) parses and serializes several times faster than the standard
library, which matters for reports whose test case files reach megabytes.
It is optional: ``pip install testbench2robotframework[fast]``. Without it the
standard library is used; the files are identical apart from key order and
whitespace details neither TestBench nor this package depend on.
"""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any

try:
    import orjson
except ImportError:  # pragma: no cover - depends on the environment
    orjson = None

JSONDecodeError = json.JSONDecodeError


def _default(value: Any) -> Any:
    return value.value if isinstance(value, Enum) else str(value)


def dumps(content: Any) -> str:
    """Compact JSON, the way TestBench exports it."""
    if orjson is not None:
        return orjson.dumps(content, default=_default).decode("utf-8")
    return json.dumps(content, default=_default)


def loads(text: str | bytes) -> Any:
    """Raises 'JSONDecodeError' (the standard library's) for invalid input."""
    if orjson is not None:
        try:
            return orjson.loads(text)
        except orjson.JSONDecodeError as error:
            raise JSONDecodeError(str(error), "", 0) from error
    return json.loads(text)


def write_json(filepath: str | Path, content: Any) -> None:
    Path(filepath).write_text(dumps(content), encoding="utf-8")


def read_json_file(filepath: str | Path) -> Any:
    return loads(Path(filepath).read_bytes())


def using_orjson() -> bool:
    return orjson is not None
