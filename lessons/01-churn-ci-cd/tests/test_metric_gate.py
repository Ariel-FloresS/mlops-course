import pytest

from src.model.metric_gate import enforce_metric_gate


def test_gate_passes_at_exact_threshold():
    enforce_metric_gate({"roc_auc": 0.85}, "roc_auc", 0.85)


def test_gate_fails_below_threshold():
    with pytest.raises(ValueError, match="metric gate failed"):
        enforce_metric_gate({"roc_auc": 0.8499}, "roc_auc", 0.85)


def test_gate_rejects_unknown_metric_name():
    with pytest.raises(ValueError, match="not in metrics"):
        enforce_metric_gate({"accuracy": 0.9}, "roc_auc", 0.85)
