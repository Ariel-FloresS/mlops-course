import json
from pathlib import Path


def read_json_lines(log_path: Path) -> list[dict]:
    if not log_path.exists():
        raise ValueError(f"log file not found at {log_path}")
    lines = log_path.read_text().splitlines()
    if not lines:
        raise ValueError(f"log file at {log_path} is empty")
    records = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            raise ValueError(f"blank line {line_number} in {log_path}")
        records.append(json.loads(line))
    return records
