"""Report files are written compact and read back identically, with or without orjson."""

from enum import Enum

import pytest

from testbench2robotframework import json_codec


class Colour(Enum):
    Red = "Red"


def test_round_trip_is_compact_and_enum_aware(tmp_path):
    path = tmp_path / "x.json"
    json_codec.write_json(path, {"colour": Colour.Red, "n": 1, "text": "ä"})
    assert json_codec.read_json_file(path) == {"colour": "Red", "n": 1, "text": "ä"}
    assert "\n" not in path.read_text(encoding="utf-8")


def test_invalid_json_raises_the_standard_error():
    with pytest.raises(json_codec.JSONDecodeError):
        json_codec.loads("{not json")


def test_stdlib_fallback_matches(monkeypatch):
    monkeypatch.setattr(json_codec, "orjson", None)
    assert json_codec.loads(json_codec.dumps({"a": [1, Colour.Red]})) == {"a": [1, "Red"]}
    assert not json_codec.using_orjson()
