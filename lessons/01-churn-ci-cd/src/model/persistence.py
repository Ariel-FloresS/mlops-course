import json
from pathlib import Path

import joblib
from sklearn.pipeline import Pipeline


def save_model_pipeline(model_pipeline: Pipeline, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model_pipeline, output_path)


def load_model_pipeline(model_path: Path) -> Pipeline:
    if not model_path.exists():
        raise ValueError(f"model artifact not found at {model_path}")
    return joblib.load(model_path)


def save_metrics(metrics: dict[str, float], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n")
