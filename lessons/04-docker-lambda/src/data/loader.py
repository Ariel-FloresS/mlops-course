from pathlib import Path

import pandas as pd


def load_churn_frame(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        raise ValueError(f"dataset not found at {csv_path}")
    frame = pd.read_csv(csv_path)
    if frame.empty:
        raise ValueError(f"dataset at {csv_path} is empty")
    return frame
