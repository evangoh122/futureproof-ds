# Beam Trial Conversion Model

This project is an exercise in building and running a machine-learning pipeline with
open-source tools. At work I use Databricks; here I am revisiting local development,
containerization, and an eventual AWS deployment.

The model predicts, from a trial user's **first three days of behavior**, whether their
14-day Beam trial will convert to a paid plan. This gives the growth team time to
intervene before the trial ends.

**Status:** prototype pipeline. One command extracts the data, cleans it, builds features,
trains the models, evaluates them, and saves the selected model and predictions. It does
not yet score live trials.

## Business problem

Beam launched a 14-day free trial on August 1, 2026. Roughly 250 people begin a trial each
week, but only about half convert; the business case assumed 58%. The growth team currently
learns the outcome after a trial ends, when it is too late to intervene.

This project asks:

> For a trial that started three days ago, how likely is it to convert at the end of day 14?

Day 3 leaves 11 days for an intervention while providing enough behavior for useful
prediction. See [trial-conversion-model-plan.md](trial-conversion-model-plan.md) for the
full business context, stakeholders, and roadmap.

## Results

The models were trained on 1,516 completed trials, of which 53.2% converted. A stratified
25% test split was held out.

| Model | Test AUC |
|---|---:|
| Logistic regression baseline | 0.827 |
| **XGBoost** | **0.876** |

At a 0.5 decision threshold, XGBoost achieved 0.792 accuracy with balanced precision and
recall. Both models train on every pipeline run so the baseline comparison appears in the
logs.

At the configured intervention threshold of 0.35:

- 148 of 379 test trials were flagged
- flagged trials converted at **17.6%**
- all other trials converted at **76.2%**

The threshold is configurable because the growth team's weekly intervention capacity is a
business decision rather than a fixed modeling assumption.

## Features

The model uses first-three-day engagement measures. Derived features include:

- `sessions_3d`
- `active_days_3d`
- `day1_share`
- `listen_share`
- `avg_session_minutes`

Raw `total_minutes_3d`, `country`, and `device_type` are included alongside them. Trials
with no sessions have their share and average features filled with zero because zero
engagement is meaningful information.

## Project structure

```text
main.py                                  orchestrates all four pipeline stages
config.yaml                              paths, database location, features, model settings
pyproject.toml                           Python project and dependency declarations
uv.lock                                  exact dependency versions resolved by uv
.python-version                          project Python version
.env                                     database credentials only; not committed

src/ETL/Bronze.py                        PostgreSQL -> data/01_raw/
src/ETL/Silver.py                        clean data -> data/02_processed/
src/Feature Engineering/features.py      build features -> data/03_feature_engineering/
src/Modeling/train.py                    train/evaluate -> model and predictions

notebooks/trial_conversion_model.ipynb   original analysis and exploration
trial-conversion-model-plan.md           business case and project roadmap
```

The pipeline follows a numbered, medallion-style data flow:

```text
data/01_raw/trials_raw.csv                extracted source data
data/02_processed/trials_clean.csv        deduplicated and cleaned data
data/03_feature_engineering/features.csv  model-ready features
data/04_model_pred/test_predictions.csv   test labels and probabilities
model.pkl                                 fitted selected model
```

Generated CSV files and `model.pkl` are ignored by Git and can be reproduced by running
the pipeline.

## Setup with uv

The project uses Python 3.13 and [uv](https://docs.astral.sh/uv/) for dependency and virtual
environment management. `pyproject.toml` declares the dependencies and `uv.lock` records
the exact resolved environment. `requirements.txt` is no longer the primary dependency
source.

From the repository root, create or synchronize the environment:

```powershell
uv sync
```

Create `.env` from `.env.example` and add the two database secrets:

```dotenv
Username=your_username
Password=your_password
```

The format must be `KEY=value`. Database host, port, name, schema, and table are non-secret
settings stored in `config.yaml`.

## Run the pipeline

From the repository root:

```powershell
uv run python main.py
```

The stages run in this order:

1. Bronze fetches `ml.trial_snapshot_latest` from PostgreSQL and saves the raw CSV.
2. Silver removes duplicate and missing rows, converts the date columns, and saves the
   cleaned CSV.
3. Feature engineering creates the configured model features.
4. Training fits the logistic-regression baseline and configured model, evaluates them,
   and saves the model and test predictions.

Every stage logs when it starts, how many rows it processed, and where it saved its output.
The database must be reachable because Bronze fetches fresh data on every full run.

To run only the Silver cleaning stage against the existing Bronze CSV:

```powershell
uv run python src/ETL/Silver.py
```

## Configuration

Change pipeline behavior in `config.yaml` rather than hard-coding settings in the Python
files.

| Key | Purpose |
|---|---|
| `database.*` | PostgreSQL host, port, database, schema, and table |
| `data.raw_path` | Bronze CSV output and Silver input |
| `data.clean_path` | Silver CSV output |
| `data.features_path` | Feature-engineered CSV output |
| `data.features` | Numeric features used for training |
| `data.categorical_features` | Categorical features to one-hot encode |
| `data.test_size` | Fraction reserved for testing |
| `data.random_state` | Reproducible train/test split seed |
| `model.type` | `xgb` or `logistic_regression` |
| `xgboost.*` | Arguments passed to `XGBClassifier` |
| `logistic_regression.*` | Arguments passed to `LogisticRegression` |
| `evaluation.decision_threshold` | Probability cutoff for class labels |
| `evaluation.flag_threshold` | Probability cutoff for intervention candidates |
| `output.*` | Saved model and prediction paths |

## Notebook

Launch the exploratory notebook inside the uv environment:

```powershell
uv run jupyter notebook notebooks/trial_conversion_model.ipynb
```

The notebook contains the original EDA, plots, and reasoning. The pipeline is the
reproducible execution path; the notebook is the exploratory record.

## Tests

Pytest is installed in the uv environment. When tests are present under `tests/`, run:

```powershell
uv run pytest
```

The repository currently has no committed test files, so adding unit tests for feature
engineering and model-matrix construction remains useful follow-up work.

## Next steps

1. Pilot the intervention list with the growth team.
2. Add a scoring entry point that loads `model.pkl` without retraining.
3. Schedule day-3 scoring and store the resulting scores.
4. Monitor population and model drift, then retrain on newer cohorts when needed.
5. Containerize the application and prepare an AWS deployment.

Out of scope for this prototype: paid-subscriber churn, uplift modeling, and changes to
trial length, price, or eligibility.
