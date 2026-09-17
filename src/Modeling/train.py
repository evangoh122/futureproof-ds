"""Train the trial-conversion model.

Ports the modelling half of notebooks/trial_conversion_model.ipynb: reads the
silver layer, builds features, fits a logistic-regression baseline and an
XGBoost classifier, reports test metrics, and writes model.pkl.

Run from the project root:
    python src/Modeling/train.py
"""

import pickle
import sys
from pathlib import Path

import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, confusion_matrix, classification_report
from xgboost import XGBClassifier

SRC_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = SRC_DIR.parent

# ETL/ and Feature Engineering/ are plain directories, not packages, and one of
# them has a space in its name, so they go on sys.path rather than being imported
# as modules.
sys.path.insert(0, str(SRC_DIR / "ETL"))
sys.path.insert(0, str(SRC_DIR / "Feature Engineering"))

from Silver import clean_data  # noqa: E402
from features import add_features  # noqa: E402

FEATURES = ["sessions_3d", "active_days_3d", "day1_share", "listen_share",
            "avg_session_minutes", "total_minutes_3d", "country", "device_type"]
CATEGORICAL = ["country", "device_type"]
TARGET = "converted"

TEST_SIZE = 0.25
RANDOM_STATE = 42

# Trials scored below this are the intervention list handed to the growth team.
# The cutoff is the lifecycle team's call, not a modelling decision.
FLAG_THRESHOLD = 0.35

MODEL_PATH = PROJECT_ROOT / "model.pkl"


def train_model():
    # Silver layer plus the derived features the model reads
    df = add_features(clean_data())

    features = pd.get_dummies(df[FEATURES], columns=CATEGORICAL)
    target = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        features, target, test_size=TEST_SIZE, stratify=target, random_state=RANDOM_STATE
    )
    print(f"train: {len(X_train)} trials, test: {len(X_test)} trials, "
          f"conversion rate: {target.mean().round(4)}\n")

    # Baseline: logistic regression, so the real model has something honest to beat
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    baseline = LogisticRegression(max_iter=1000)
    baseline.fit(X_train_s, y_train)
    print("logistic regression AUC:",
          round(roc_auc_score(y_test, baseline.predict_proba(X_test_s)[:, 1]), 4))

    # XGBoost
    model = XGBClassifier(
        n_estimators=400,
        max_depth=3,
        learning_rate=0.05,
        min_child_weight=8,
        subsample=0.9,
        colsample_bytree=0.9,
        eval_metric="auc",
    )
    model.fit(X_train, y_train)

    probs = model.predict_proba(X_test)[:, 1]
    preds = (probs >= 0.5).astype(int)
    print("XGBoost AUC:", round(roc_auc_score(y_test, probs), 4))

    importances = pd.Series(model.feature_importances_, index=features.columns)
    print("\nfeature importance (top 10):")
    print(importances.sort_values(ascending=False).head(10).round(4).to_string())

    # Evaluation
    print("\nconfusion matrix:")
    print(confusion_matrix(y_test, preds))
    print("\n" + classification_report(y_test, preds, digits=3))

    # The group worth intervening on: everything the model scores low
    flagged = probs < FLAG_THRESHOLD
    print(f"flagged for intervention (p < {FLAG_THRESHOLD}):",
          f"{flagged.sum()} of {len(probs)}")
    print("actual conversion rate among flagged:", round(y_test[flagged].mean(), 3))
    print("actual conversion rate among the rest:", round(y_test[~flagged].mean(), 3))

    # Save the model for the hand-off
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    print("\nsaved model to", MODEL_PATH)

    return model


if __name__ == "__main__":
    train_model()
