import pandas as pd


def validate_required_columns(frame: pd.DataFrame, required_columns: list[str]) -> None:
    # TODO: collect every column from required_columns that is absent from frame.columns
    # TODO: if any are missing, raise ValueError with a message that starts with
    #       "missing required columns:" and lists them
    raise NotImplementedError


def validate_no_missing_values(frame: pd.DataFrame, columns: list[str]) -> None:
    # TODO: collect every column whose series contains at least one NaN
    #       (hint: frame[column].isna().any())
    # TODO: if any are found, raise ValueError with a message that starts with
    #       "columns with missing values:" and lists them
    raise NotImplementedError


def validate_binary_target(frame: pd.DataFrame, target_column: str) -> None:
    # TODO: build the set of unique values observed in the target column
    # TODO: raise ValueError containing "must contain only 0 and 1" if any other value appears
    # TODO: raise ValueError containing "contains a single class" if only one value appears
    raise NotImplementedError
