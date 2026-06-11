import pandas as pd

from src.drift.psi import compute_psi
from src.drift.reference_profile import (
    CategoricalFeatureProfile,
    NumericFeatureProfile,
    compute_binned_proportions,
)


def compute_numeric_feature_psi(
    profile: NumericFeatureProfile, current_values: pd.Series
) -> float:
    current_proportions = compute_binned_proportions(current_values, profile.bin_edges)
    return compute_psi(profile.bin_proportions, current_proportions)


def compute_categorical_proportions(
    current_values: pd.Series, categories: tuple[str, ...]
) -> tuple[float, ...]:
    if current_values.empty:
        raise ValueError("current_values must not be empty")
    observed_counts = current_values.value_counts()
    total_count = len(current_values)
    return tuple(
        round(float(observed_counts.get(category, 0) / total_count), 6)
        for category in categories
    )


def compute_categorical_feature_psi(
    profile: CategoricalFeatureProfile, current_values: pd.Series
) -> float:
    categories = tuple(profile.category_proportions)
    expected_proportions = tuple(profile.category_proportions.values())
    current_proportions = compute_categorical_proportions(current_values, categories)
    return compute_psi(expected_proportions, current_proportions)


def compute_psi_by_feature(
    numeric_profiles: list[NumericFeatureProfile],
    categorical_profiles: list[CategoricalFeatureProfile],
    current_frame: pd.DataFrame,
) -> dict[str, float]:
    psi_by_feature = {}
    for numeric_profile in numeric_profiles:
        psi_by_feature[numeric_profile.feature_name] = compute_numeric_feature_psi(
            numeric_profile, current_frame[numeric_profile.feature_name]
        )
    for categorical_profile in categorical_profiles:
        psi_by_feature[categorical_profile.feature_name] = compute_categorical_feature_psi(
            categorical_profile, current_frame[categorical_profile.feature_name]
        )
    return psi_by_feature
