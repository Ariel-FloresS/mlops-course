import json
from pathlib import Path


class JsonLinesLogger:
    def __init__(self, output_path: Path):
        self.output_path = output_path

    def write_record(self, record: dict) -> None:
        if not record:
            raise ValueError("record must not be empty")
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with self.output_path.open("a") as log_file:
            log_file.write(json.dumps(record, sort_keys=True) + "\n")
