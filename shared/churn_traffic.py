import numpy as np
import pandas as pd

from shared.churn_data import generate_feature_columns


def generate_traffic_frame(request_count: int, seed: int) -> pd.DataFrame:
    if request_count <= 0:
        raise ValueError("request_count must be positive")
    rng = np.random.default_rng(seed)
    return pd.DataFrame(generate_feature_columns(rng, request_count))
