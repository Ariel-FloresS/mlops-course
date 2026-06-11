import json

import pytest

from src.serving.json_lines_logger import JsonLinesLogger


def test_writes_one_parseable_line_per_record(tmp_path):
    logger = JsonLinesLogger(tmp_path / "events.jsonl")
    logger.write_record({"status_code": 200, "latency_ms": 3.14})
    logger.write_record({"status_code": 422, "latency_ms": 1.0})
    lines = (tmp_path / "events.jsonl").read_text().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0]) == {"status_code": 200, "latency_ms": 3.14}
    assert json.loads(lines[1])["status_code"] == 422


def test_appends_to_existing_file(tmp_path):
    log_path = tmp_path / "events.jsonl"
    log_path.write_text('{"existing": true}\n')
    JsonLinesLogger(log_path).write_record({"new": True})
    assert len(log_path.read_text().splitlines()) == 2


def test_rejects_empty_record(tmp_path):
    logger = JsonLinesLogger(tmp_path / "events.jsonl")
    with pytest.raises(ValueError, match="must not be empty"):
        logger.write_record({})
