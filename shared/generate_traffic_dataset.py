import sys
from pathlib import Path

from shared.churn_traffic import generate_traffic_frame

TRAFFIC_REQUEST_COUNT = 200
TRAFFIC_SEED = 7


def write_traffic_dataset(output_path: Path) -> None:
    frame = generate_traffic_frame(TRAFFIC_REQUEST_COUNT, TRAFFIC_SEED)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_path, index=False)
    print(f"wrote {len(frame)} rows to {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise ValueError("usage: uv run python -m shared.generate_traffic_dataset <output_csv_path>")
    write_traffic_dataset(Path(sys.argv[1]))
