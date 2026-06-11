from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def build_feature_encoder(
    numeric_columns: list[str], categorical_columns: list[str]
) -> ColumnTransformer:
    if not numeric_columns and not categorical_columns:
        raise ValueError("at least one feature column is required")
    return ColumnTransformer(
        [
            ("numeric", StandardScaler(), numeric_columns),
            ("categorical", OneHotEncoder(handle_unknown="error"), categorical_columns),
        ]
    )
