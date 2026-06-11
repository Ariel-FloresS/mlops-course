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
    # TODO: raise ValueError if values or bin_edges are empty
    # TODO: assign each value to a bin with np.searchsorted(bin_edges, values, side="right")
    # TODO: count values per bin with np.bincount(..., minlength=len(bin_edges) + 1)
    # TODO: return counts / len(values) as a tuple of floats rounded to 6 decimals
    raise NotImplementedError


def build_numeric_profile(
    values: pd.Series, feature_name: str, bin_count: int
) -> NumericFeatureProfile:
    # TODO: raise ValueError on empty values; raise ValueError if bin_count < 2
    # TODO: compute the INNER quantiles (exclude 0.0 and 1.0):
    #       np.linspace(0.0, 1.0, bin_count + 1)[1:-1]
    # TODO: bin_edges = np.unique(np.quantile(values, inner_quantiles)) as floats
    # TODO: bin_proportions = compute_binned_proportions(values, bin_edges)
    # TODO: return the profile
    raise NotImplementedError


def build_categorical_profile(
    values: pd.Series, feature_name: str
) -> CategoricalFeatureProfile:
    # TODO: raise ValueError on empty values
    # TODO: build {category: proportion} with value_counts(normalize=True),
    #       keys sorted alphabetically, proportions rounded to 6 decimals
    # TODO: return the profile
    raise NotImplementedError
