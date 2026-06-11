import math

import pytest

from src.drift.psi import compute_psi


def test_identical_distributions_score_zero():
    assert compute_psi((0.5, 0.3, 0.2), (0.5, 0.3, 0.2)) == 0.0


def test_known_shift_matches_hand_computation():
    expected_psi = (0.9 - 0.5) * math.log(0.9 / 0.5) + (0.1 - 0.5) * math.log(0.1 / 0.5)
    assert compute_psi((0.5, 0.5), (0.9, 0.1)) == round(expected_psi, 4)
    assert compute_psi((0.5, 0.5), (0.9, 0.1)) == 0.8789


def test_zero_proportions_are_clipped_to_finite_psi():
    psi = compute_psi((0.5, 0.5), (1.0, 0.0))
    assert math.isfinite(psi)
    assert psi > 1.0


def test_rejects_mismatched_lengths():
    with pytest.raises(ValueError, match="differ in length"):
        compute_psi((0.5, 0.5), (1.0,))
