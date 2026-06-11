import numpy as np
import pandas as pd

CONTRACT_TYPES = ("month_to_month", "one_year", "two_year")
PAYMENT_METHODS = ("credit_card", "bank_transfer", "electronic_check")


def generate_feature_columns(rng: np.random.Generator, row_count: int) -> dict[str, np.ndarray]:
    tenure_months = rng.integers(1, 73, row_count)
    monthly_charges = np.round(rng.uniform(20.0, 120.0, row_count), 2)
    total_charges = np.round(tenure_months * monthly_charges, 2)
    contract_type = rng.choice(CONTRACT_TYPES, row_count, p=(0.5, 0.3, 0.2))
    payment_method = rng.choice(PAYMENT_METHODS, row_count, p=(0.4, 0.3, 0.3))
    support_tickets = rng.poisson(1.5, row_count)
    return {
        "tenure_months": tenure_months,
        "monthly_charges": monthly_charges,
        "total_charges": total_charges,
        "contract_type": contract_type,
        "payment_method": payment_method,
        "support_tickets": support_tickets,
    }


def compute_churn_logit(
    tenure_months: np.ndarray,
    monthly_charges: np.ndarray,
    support_tickets: np.ndarray,
    contract_type: np.ndarray,
    payment_method: np.ndarray,
) -> np.ndarray:
    return (
        -0.5
        + 2.2 * (contract_type == "month_to_month")
        + 1.1 * (payment_method == "electronic_check")
        - 0.09 * tenure_months
        + 0.022 * (monthly_charges - 70.0)
        + 0.55 * support_tickets
    )


def generate_churn_frame(row_count: int, seed: int) -> pd.DataFrame:
    if row_count <= 0:
        raise ValueError("row_count must be positive")
    rng = np.random.default_rng(seed)
    feature_columns = generate_feature_columns(rng, row_count)
    churn_logit = compute_churn_logit(
        feature_columns["tenure_months"],
        feature_columns["monthly_charges"],
        feature_columns["support_tickets"],
        feature_columns["contract_type"],
        feature_columns["payment_method"],
    )
    churn_probability = 1.0 / (1.0 + np.exp(-churn_logit))
    churn = rng.binomial(1, churn_probability)
    return pd.DataFrame({**feature_columns, "churn": churn})
