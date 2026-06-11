from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class NumericFeatureProfile:
    feature_name: str
    bin_edges: tuple[float, ...]
    bin_proportions: tuple[float, ...]


@dataclass(frozen=True)
class CategoricalFeatureProfile:
    feature_name: str
    category_proportions: dict[str, float]


def compute_binned_proportions(
    values: pd.Series, bin_edges: tuple[float, ...]
) -> tuple[float, ...]:
    if values.empty:
        raise ValueError("values must not be empty")
    if not bin_edges:
        raise ValueError("bin_edges must not be empty")
    bin_indices = np.searchsorted(bin_edges, values, side="right")
    bin_counts = np.bincount(bin_indices, minlength=len(bin_edges) + 1)
    return tuple(round(float(count / len(values)), 6) for count in bin_counts)


def build_numeric_profile(
    values: pd.Series, feature_name: str, bin_count: int
) -> NumericFeatureProfile:
    if values.empty:
        raise ValueError(f"no values for feature {feature_name}")
    if bin_count < 2:
        raise ValueError(f"bin_count must be at least 2, got {bin_count}")
    inner_quantiles = np.linspace(0.0, 1.0, bin_count + 1)[1:-1]
    bin_edges = tuple(float(edge) for edge in np.unique(np.quantile(values, inner_quantiles)))
    bin_proportions = compute_binned_proportions(values, bin_edges)
    return NumericFeatureProfile(feature_name, bin_edges, bin_proportions)


def build_categorical_profile(
    values: pd.Series, feature_name: str
) -> CategoricalFeatureProfile:
    if values.empty:
        raise ValueError(f"no values for feature {feature_name}")
    normalized_counts = values.value_counts(normalize=True)
    category_proportions = {
        str(category): round(float(normalized_counts[category]), 6)
        for category in sorted(normalized_counts.index)
    }
    return CategoricalFeatureProfile(feature_name, category_proportions)
