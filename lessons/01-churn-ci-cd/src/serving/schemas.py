from typing import Literal

from pydantic import BaseModel, Field


class ChurnPredictionRequest(BaseModel):
    tenure_months: int = Field(ge=0)
    monthly_charges: float = Field(gt=0)
    total_charges: float = Field(ge=0)
    contract_type: Literal["month_to_month", "one_year", "two_year"]
    payment_method: Literal["credit_card", "bank_transfer", "electronic_check"]
    support_tickets: int = Field(ge=0)


class ChurnPredictionResponse(BaseModel):
    churn_probability: float
    churn_label: int


class HealthResponse(BaseModel):
    status: str
