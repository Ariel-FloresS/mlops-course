import sys
from pathlib import Path

import pandas as pd

from shared.churn_data import generate_churn_frame

ORIGINAL_ROW_COUNT = 2000
ORIGINAL_SEED = 42
FRESH_ROW_COUNT = 1000
FRESH_SEED = 99


def write_churn_dataset_v2(output_path: Path) -> None:
    original_frame = generate_churn_frame(ORIGINAL_ROW_COUNT, ORIGINAL_SEED)
    fresh_frame = generate_churn_frame(FRESH_ROW_COUNT, FRESH_SEED)
    combined_frame = pd.concat([original_frame, fresh_frame], ignore_index=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    combined_frame.to_csv(output_path, index=False)
    print(f"wrote {len(combined_frame)} rows to {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise ValueError(
            "usage: uv run python -m shared.generate_churn_dataset_v2 <output_csv_path>"
        )
    write_churn_dataset_v2(Path(sys.argv[1]))
