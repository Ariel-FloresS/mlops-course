import pandas as pd
import pytest

from src.drift.reference_profile import (
    build_categorical_profile,
    build_numeric_profile,
    compute_binned_proportions,
)


def test_numeric_profile_splits_values_into_quantile_bins():
    values = pd.Series(range(1, 11))
    profile = build_numeric_profile(values, "tenure_months", 2)
    assert profile.bin_edges == (5.5,)
    assert profile.bin_proportions == (0.5, 0.5)


def test_numeric_profile_with_four_bins():
    values = pd.Series(range(1, 11))
    profile = build_numeric_profile(values, "tenure_months", 4)
    assert profile.bin_edges == (3.25, 5.5, 7.75)
    assert profile.bin_proportions == (0.3, 0.2, 0.2, 0.3)


def test_categorical_profile_sorts_categories_and_normalizes():
    values = pd.Series(["b", "a", "b", "b"])
    profile = build_categorical_profile(values, "contract_type")
    assert profile.category_proportions == {"a": 0.25, "b": 0.75}


def test_binned_proportions_rejects_empty_values():
    with pytest.raises(ValueError, match="must not be empty"):
        compute_binned_proportions(pd.Series([], dtype=float), (1.0,))
