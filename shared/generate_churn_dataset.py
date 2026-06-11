import sys
from pathlib import Path

from shared.churn_data import generate_churn_frame

DATASET_ROW_COUNT = 2000
DATASET_SEED = 42


def write_churn_dataset(output_path: Path) -> None:
    frame = generate_churn_frame(DATASET_ROW_COUNT, DATASET_SEED)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_path, index=False)
    print(f"wrote {len(frame)} rows to {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise ValueError("usage: uv run python -m shared.generate_churn_dataset <output_csv_path>")
    write_churn_dataset(Path(sys.argv[1]))
