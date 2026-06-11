import numpy as np
import pandas as pd

from shared.churn_data import CONTRACT_TYPES, PAYMENT_METHODS


def generate_drifted_feature_columns(
    rng: np.random.Generator, row_count: int
) -> dict[str, np.ndarray]:
    tenure_months = rng.integers(1, 25, row_count)
    monthly_charges = np.round(rng.uniform(60.0, 140.0, row_count), 2)
    total_charges = np.round(tenure_months * monthly_charges, 2)
    contract_type = rng.choice(CONTRACT_TYPES, row_count, p=(0.75, 0.15, 0.10))
    payment_method = rng.choice(PAYMENT_METHODS, row_count, p=(0.25, 0.15, 0.60))
    support_tickets = rng.poisson(3.0, row_count)
    return {
        "tenure_months": tenure_months,
        "monthly_charges": monthly_charges,
        "total_charges": total_charges,
        "contract_type": contract_type,
        "payment_method": payment_method,
        "support_tickets": support_tickets,
    }


def generate_drifted_traffic_frame(request_count: int, seed: int) -> pd.DataFrame:
    if request_count <= 0:
        raise ValueError("request_count must be positive")
    rng = np.random.default_rng(seed)
    return pd.DataFrame(generate_drifted_feature_columns(rng, request_count))
