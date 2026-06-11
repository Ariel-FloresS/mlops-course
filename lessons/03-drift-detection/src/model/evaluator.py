import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score
from sklearn.pipeline import Pipeline


def evaluate_classifier(
    model_pipeline: Pipeline, test_features: pd.DataFrame, test_target: pd.Series
) -> dict[str, float]:
    predicted_labels = model_pipeline.predict(test_features)
    predicted_probabilities = model_pipeline.predict_proba(test_features)[:, 1]
    return {
        "accuracy": round(float(accuracy_score(test_target, predicted_labels)), 4),
        "precision": round(float(precision_score(test_target, predicted_labels)), 4),
        "recall": round(float(recall_score(test_target, predicted_labels)), 4),
        "roc_auc": round(float(roc_auc_score(test_target, predicted_probabilities)), 4),
    }
