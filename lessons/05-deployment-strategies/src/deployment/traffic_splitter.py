import numpy as np


class WeightedTrafficSplitter:
    def __init__(self, green_weight: float, seed: int):
        if not 0.0 <= green_weight <= 1.0:
            raise ValueError(f"green_weight must be between 0 and 1, got {green_weight}")
        self.green_weight = green_weight
        self.random_generator = np.random.default_rng(seed)

    def choose_target(self) -> str:
        if self.random_generator.random() < self.green_weight:
            return "green"
        return "blue"
