import pytest

from src.drift.drift_gate import enforce_drift_gate


def test_all_features_below_threshold_pass():
    enforce_drift_gate({"tenure_months": 0.05, "contract_type": 0.1999}, 0.2)


def test_feature_at_threshold_fires_the_gate():
    with pytest.raises(ValueError, match="data drift detected"):
        enforce_drift_gate({"tenure_months": 0.2}, 0.2)


def test_gate_lists_only_drifted_features_and_threshold():
    with pytest.raises(ValueError) as raised:
        enforce_drift_gate({"tenure_months": 1.5, "contract_type": 0.01}, 0.2)
    message = str(raised.value)
    assert "tenure_months" in message
    assert "contract_type" not in message
    assert "0.2" in message
