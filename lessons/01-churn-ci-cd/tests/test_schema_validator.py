import pandas as pd
import pytest

from src.data.schema_validator import (
    validate_binary_target,
    validate_no_missing_values,
    validate_required_columns,
)


def build_valid_frame() -> pd.DataFrame:
    return pd.DataFrame({"tenure_months": [1, 24, 60], "churn": [1, 0, 0]})


def test_validate_required_columns_accepts_present_columns():
    validate_required_columns(build_valid_frame(), ["tenure_months", "churn"])


def test_validate_required_columns_rejects_missing_column():
    with pytest.raises(ValueError, match="missing required columns"):
        validate_required_columns(build_valid_frame(), ["tenure_months", "monthly_charges"])


def test_validate_no_missing_values_rejects_nan():
    frame_with_gap = pd.DataFrame({"tenure_months": [1, None, 60], "churn": [1, 0, 0]})
    with pytest.raises(ValueError, match="columns with missing values"):
        validate_no_missing_values(frame_with_gap, ["tenure_months", "churn"])


def test_validate_binary_target_rejects_non_binary_values():
    frame_with_third_class = pd.DataFrame({"churn": [0, 1, 2]})
    with pytest.raises(ValueError, match="must contain only 0 and 1"):
        validate_binary_target(frame_with_third_class, "churn")


def test_validate_binary_target_rejects_single_class():
    frame_with_one_class = pd.DataFrame({"churn": [1, 1, 1]})
    with pytest.raises(ValueError, match="contains a single class"):
        validate_binary_target(frame_with_one_class, "churn")
