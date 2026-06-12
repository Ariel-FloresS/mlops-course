import pytest

from src.deployment.traffic_splitter import WeightedTrafficSplitter


def test_weight_zero_always_routes_blue():
    splitter = WeightedTrafficSplitter(0.0, seed=1)
    assert all(splitter.choose_target() == "blue" for _ in range(100))


def test_weight_one_always_routes_green():
    splitter = WeightedTrafficSplitter(1.0, seed=1)
    assert all(splitter.choose_target() == "green" for _ in range(100))


def test_same_seed_produces_identical_assignment_sequences():
    first_splitter = WeightedTrafficSplitter(0.2, seed=13)
    second_splitter = WeightedTrafficSplitter(0.2, seed=13)
    first_sequence = [first_splitter.choose_target() for _ in range(50)]
    second_sequence = [second_splitter.choose_target() for _ in range(50)]
    assert first_sequence == second_sequence


def test_green_share_approximates_weight():
    splitter = WeightedTrafficSplitter(0.2, seed=13)
    assignments = [splitter.choose_target() for _ in range(2000)]
    green_share = assignments.count("green") / len(assignments)
    assert 0.15 <= green_share <= 0.25


def test_rejects_weight_outside_unit_interval():
    with pytest.raises(ValueError, match="between 0 and 1"):
        WeightedTrafficSplitter(1.5, seed=1)
