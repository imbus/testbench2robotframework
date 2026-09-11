import json

import pytest

from testbench2robotframework.json_reader import TestBenchJsonReader
from testbench2robotframework.model import VerdictStatus

PROTOCOL = [
    {
        "testCaseSetKey": "1001",
        "executionKey": "2001",
        "durationMillis": 1234,
        "testCases": [
            {
                "uniqueID": "itb-TC-0815-PC-4711",
                "testCaseExecutionKey": "3001",
                "result": {
                    "status": "Performed",
                    "execStatus": "NotBlocked",
                    "verdict": "Pass",
                    "timestamp": "2026-07-23 10:00:00",
                },
                "durationMillis": 1234,
                "comments": {"html": "<b>PASS</b>"},
            }
        ],
        "comments": {"html": "<table></table>"},
    }
]


def test_read_main_protocol_returns_empty_list_without_file(tmp_path):
    assert TestBenchJsonReader(tmp_path).read_main_protocol() == []


def test_read_main_protocol_deserializes_entries(tmp_path):
    (tmp_path / "protocol.json").write_text(json.dumps(PROTOCOL), encoding="utf-8")

    protocol = TestBenchJsonReader(tmp_path).read_main_protocol()

    assert len(protocol) == 1
    assert protocol[0].testCaseSetKey == "1001"
    assert protocol[0].testCases[0].uniqueID == "itb-TC-0815-PC-4711"
    assert protocol[0].testCases[0].result.verdict is VerdictStatus.Pass


def test_read_main_protocol_exits_on_broken_file(tmp_path):
    (tmp_path / "protocol.json").write_text("{not json", encoding="utf-8")

    with pytest.raises(SystemExit):
        TestBenchJsonReader(tmp_path).read_main_protocol()
