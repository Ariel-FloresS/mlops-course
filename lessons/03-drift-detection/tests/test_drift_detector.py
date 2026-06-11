import pandas as pd

from src.drift.drift_detector import (
    compute_categorical_feature_psi,
    compute_numeric_feature_psi,
    compute_psi_by_feature,
)
from src.drift.reference_profile import build_categorical_profile, build_numeric_profile


def test_numeric_feature_without_shift_scores_zero():
    reference_values = pd.Series(range(1, 11))
    profile = build_numeric_profile(reference_values, "tenure_months", 2)
    assert compute_numeric_feature_psi(profile, reference_values) == 0.0


def test_numeric_feature_with_total_shift_scores_high():
    reference_values = pd.Series(range(1, 11))
    profile = build_numeric_profile(reference_values, "tenure_months", 2)
    shifted_values = pd.Series([10] * 10)
    assert compute_numeric_feature_psi(profile, shifted_values) > 1.0


def test_categorical_feature_psi_matches_hand_computation():
    profile = build_categorical_profile(pd.Series(["a", "a", "b", "b"]), "contract_type")
    current_values = pd.Series(["a", "a", "a", "b"])
    assert compute_categorical_feature_psi(profile, current_values) == 0.2747


def test_psi_by_feature_covers_every_profiled_feature():
    frame = pd.DataFrame(
        {"tenure_months": range(1, 11), "contract_type": ["a", "b"] * 5}
    )
    numeric_profiles = [build_numeric_profile(frame["tenure_months"], "tenure_months", 2)]
    categorical_profiles = [build_categorical_profile(frame["contract_type"], "contract_type")]
    psi_by_feature = compute_psi_by_feature(numeric_profiles, categorical_profiles, frame)
    assert psi_by_feature == {"tenure_months": 0.0, "contract_type": 0.0}
