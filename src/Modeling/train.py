import logging
from pathlib import Path

import joblib
import pandas as pd
import yaml
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, confusion_matrix, classification_report
from xgboost import XGBClassifier

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.yaml"


def load_config(config_path=None):
    """Read the pipeline settings that drive feature choice and training."""
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def build_design_matrix(data, config):
    """One-hot the categoricals and return the model matrix with its target."""
    data_config = config["data"]
    numeric_features = list(data_config["features"])
    categorical_features = list(data_config["categorical_features"])

    missing = [
        column
        for column in numeric_features + categorical_features + [data_config["target_col"]]
        if column not in data.columns
    ]
    if missing:
        raise KeyError(
            "Featured data is missing columns required for training: "
            f"{', '.join(missing)}."
        )

    features = pd.get_dummies(
        data[numeric_features + categorical_features],
        columns=categorical_features,
    )
    target = data[data_config["target_col"]]
    return features, target


def train_baseline(X_train, X_test, y_train, y_test, config):
    """Fit the logistic regression baseline the XGBoost model has to beat."""
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    baseline = LogisticRegression(**config["logistic_regression"])
    baseline.fit(X_train_scaled, y_train)

    probabilities = baseline.predict_proba(X_test_scaled)[:, 1]
    auc = roc_auc_score(y_test, probabilities)
    logger.info("Logistic regression AUC: %.4f", auc)
    return baseline, scaler, probabilities, auc


def train_xgboost(X_train, X_test, y_train, y_test, config):
    """Fit the gradient-boosted model and log which features carried it."""
    model = XGBClassifier(**config["xgboost"])
    model.fit(X_train, y_train)

    probabilities = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, probabilities)
    logger.info("XGBoost AUC: %.4f", auc)

    importances = pd.Series(model.feature_importances_, index=X_train.columns)
    top_features = importances.sort_values(ascending=False).head(10)
    logger.info(
        "Top features: %s",
        ", ".join(f"{name}={value:.4f}" for name, value in top_features.items()),
    )
    return model, probabilities, auc


def evaluate(y_test, probabilities, config):
    """Report standard metrics plus the low-score group worth intervening on."""
    evaluation_config = config.get("evaluation", {})
    decision_threshold = evaluation_config.get("decision_threshold", 0.5)
    flag_threshold = evaluation_config.get("flag_threshold", 0.35)

    predictions = (probabilities >= decision_threshold).astype(int)
    logger.info("Confusion matrix:\n%s", confusion_matrix(y_test, predictions))
    logger.info(
        "Classification report:\n%s",
        classification_report(y_test, predictions, digits=3),
    )

    flagged = probabilities < flag_threshold
    logger.info(
        "Flagged for intervention (p < %.2f): %d of %d",
        flag_threshold,
        flagged.sum(),
        len(probabilities),
    )
    if flagged.any():
        logger.info(
            "Conversion rate among flagged: %.3f",
            y_test[flagged].mean(),
        )
    if (~flagged).any():
        logger.info(
            "Conversion rate among the rest: %.3f",
            y_test[~flagged].mean(),
        )
    return predictions


def save_outputs(model, probabilities, predictions, y_test, config):
    """Persist the fitted model and the scored test set for the hand-off."""
    output_config = config.get("output", {})
    model_path = PROJECT_ROOT / output_config.get("model_path", "model.pkl")
    predictions_path = PROJECT_ROOT / output_config.get(
        "predictions_path", "data/04_model_pred/test_predictions.csv"
    )

    model_path.parent.mkdir(parents=True, exist_ok=True)
    predictions_path.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(model, model_path)
    pd.DataFrame(
        {
            "actual": y_test.to_numpy(),
            "predicted_probability": probabilities,
            "predicted_label": predictions,
        },
        index=y_test.index,
    ).to_csv(predictions_path, index_label=y_test.index.name or "row_id")

    logger.info("Saved model to %s", model_path)
    logger.info("Saved test predictions to %s", predictions_path)


def train_model(featured_data, config_path=None):
    """Train the configured model on the engineered features and return it."""
    config = load_config(config_path)
    data_config = config["data"]
    model_type = config["model"]["type"]

    features, target = build_design_matrix(featured_data, config)
    X_train, X_test, y_train, y_test = train_test_split(
        features,
        target,
        test_size=data_config["test_size"],
        stratify=target,
        random_state=data_config["random_state"],
    )
    logger.info(
        "Training on %d rows, testing on %d rows, %d features.",
        len(X_train),
        len(X_test),
        X_train.shape[1],
    )

    # The baseline always runs so every training log carries the comparison the
    # notebook made: XGBoost is only worth its complexity if it beats this.
    baseline, scaler, baseline_probabilities, _ = train_baseline(
        X_train, X_test, y_train, y_test, config
    )

    if model_type == "xgb":
        model, probabilities, _ = train_xgboost(
            X_train, X_test, y_train, y_test, config
        )
    elif model_type == "logistic_regression":
        model, probabilities = baseline, baseline_probabilities
    else:
        raise ValueError(
            f"Unknown model.type {model_type!r} in config; "
            "expected 'xgb' or 'logistic_regression'."
        )

    logger.info("Selected model: %s", model_type)
    predictions = evaluate(y_test, probabilities, config)

    # The logistic regression is useless without the scaler that fed it, so the
    # two travel together when it is the selected model.
    persisted = {"model": model, "scaler": scaler} if model is baseline else model
    save_outputs(persisted, probabilities, predictions, y_test, config)
    return model
