import pandas as pd


def validate_required_columns(frame: pd.DataFrame, required_columns: list[str]) -> None:
    missing_columns = [column for column in required_columns if column not in frame.columns]
    if missing_columns:
        raise ValueError(f"missing required columns: {missing_columns}")


def validate_no_missing_values(frame: pd.DataFrame, columns: list[str]) -> None:
    columns_with_missing_values = [column for column in columns if frame[column].isna().any()]
    if columns_with_missing_values:
        raise ValueError(f"columns with missing values: {columns_with_missing_values}")


def validate_binary_target(frame: pd.DataFrame, target_column: str) -> None:
    observed_values = set(frame[target_column].unique())
    if not observed_values.issubset({0, 1}):
        raise ValueError(
            f"target column {target_column} must contain only 0 and 1, found {sorted(observed_values)}"
        )
    if len(observed_values) < 2:
        raise ValueError(f"target column {target_column} contains a single class")
