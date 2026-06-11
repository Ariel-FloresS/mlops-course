import pandas as pd
from sklearn.base import ClassifierMixin
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline


def build_model_pipeline(
    feature_encoder: ColumnTransformer, classifier: ClassifierMixin
) -> Pipeline:
    return Pipeline([("features", feature_encoder), ("classifier", classifier)])


def train_model_pipeline(
    model_pipeline: Pipeline, train_features: pd.DataFrame, train_target: pd.Series
) -> Pipeline:
    if len(train_features) == 0:
        raise ValueError("training set is empty")
    if len(train_features) != len(train_target):
        raise ValueError("features and target must have the same length")
    model_pipeline.fit(train_features, train_target)
    return model_pipeline
