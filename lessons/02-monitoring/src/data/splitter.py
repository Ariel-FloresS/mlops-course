import pandas as pd
from sklearn.model_selection import train_test_split


def split_features_and_target(
    frame: pd.DataFrame, feature_columns: list[str], target_column: str
) -> tuple[pd.DataFrame, pd.Series]:
    features = frame[feature_columns]
    target = frame[target_column]
    return features, target


def split_train_test(
    features: pd.DataFrame, target: pd.Series, test_fraction: float, seed: int
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    if not 0.0 < test_fraction < 1.0:
        raise ValueError(f"test_fraction must be between 0 and 1, got {test_fraction}")
    return train_test_split(
        features, target, test_size=test_fraction, random_state=seed, stratify=target
    )
