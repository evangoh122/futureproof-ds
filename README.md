# USER comment
Going back to trying out how to develop models on open source systems, at work I use Data Bricks so, I hope to revise dockerizing and deploying it on AWS again.

# Beam Trial Conversion Model

Predicts, from a trial's **first 3 days of behavior**, whether a 14-day Beam trial will
convert to a paid plan — early enough for the growth team to intervene on the ones that
won't.

**Status:** prototype, now running as a pipeline. `python main.py` reproduces the whole
thing end to end — pull, clean, feature-build, train, save. Nothing is scoring live trials
yet; that is the deployment conversation.

## The problem

Beam launched a 14-day free trial on August 1, 2026. Roughly 250 people start one each
week, and only about half convert — the business case assumed 58%. Today the growth team
only learns how a trial went once it is over, when there is nothing left to do about it.

So the question this repo answers is:

> For a trial that started three days ago, how likely is it to convert at the end of day 14?

Day 3 is early enough to leave 11 days of runway for an intervention, and late enough that
there is real behavior to read.

Full business context, stakeholders, and value estimates:
[trial-conversion-model-plan.md](trial-conversion-model-plan.md).

## Results

Trained on 1,516 completed trials (53.2% converted). 25% held out for test, stratified.

| Model | Test AUC |
|---|---|
| Logistic regression (baseline) | 0.827 |
| **XGBoost** | **0.876** |

XGBoost accuracy at a 0.5 cutoff is 0.792, with balanced precision and recall on both
classes. Both models train on every run, so the comparison lands in the log each time
rather than being a number someone has to go and re-derive.

What matters more than AUC is whether the low-scoring group is a usable intervention list.
Scoring the test set and flagging everything below 0.35:

- 148 of 379 trials flagged
- flagged trials converted at **17.6%**
- everyone else converted at **76.2%**

That separation is what an intervention list should look like. The cutoff itself is the
lifecycle team's call, not a modeling decision — it depends on how many trials they can
actually work through in a week, so it lives in `config.yaml` as
`evaluation.flag_threshold` rather than being buried in code.

### What the model reads

Feature importance lands where the exploration suggested: total first-3-day usage
dominates, then how concentrated that usage was on day 1, then how much of it was
listening. The binge pattern is the interesting one — users who cram most of their sessions
into day 1 and then go quiet convert far below everyone else *at the same session total*.
That interaction is why the tree model beats the linear baseline.

Derived features, all built in `add_features()`: `sessions_3d`, `active_days_3d`,
`day1_share`, `listen_share`, `avg_session_minutes`. Raw `total_minutes_3d`, `country`, and
`device_type` go in alongside them. 38 trials had zero sessions in the first 3 days; their
share/average features divide by zero and are filled with 0, since zero engagement is real
information rather than a missing value.

## Layout

```
main.py                                  orchestrates the four stages in order
config.yaml                              features, hyperparameters, thresholds, paths, table
.env                                     database Username / Password only (gitignored)

src/ETL/Bronze.py                        pull from Postgres     -> data/01_raw/
src/ETL/Silver.py                        dedupe, dropna, dates  -> in memory
src/Feature Engineering/features.py      derived features       -> data/03_feature_engineering/
src/Modeling/train.py                    baseline + XGBoost     -> model.pkl, data/04_model_pred/

notebooks/trial_conversion_model.ipynb   the original analysis: load, clean, EDA, model, eval
trial-conversion-model-plan.md           business case, stakeholders, roadmap, out-of-scope
tests/test_main.py                       pipeline wiring tests (no database needed)
```

Data flows through numbered layers, medallion-style:

```
data/01_raw/trials_raw.csv                as pulled from ml.trial_snapshot_latest
data/02_processed/trials_clean.csv        post-clean
data/03_feature_engineering/features.csv  post-feature-build
data/04_model_pred/test_predictions.csv   scored test set: actual, probability, label
model.pkl                                 XGBoost classifier, saved with joblib
```

The CSVs and `model.pkl` are gitignored; they are reproducible with one command.

## Running it

Python 3.11.

```bash
pip install -r requirements.txt
```

Create `.env` from `.env.example` and fill in the two secrets:

```
Username=...
Password=...
```

The format is `KEY=value`. `python-dotenv` cannot parse `Key: value` and skips those lines
silently, so `Bronze.py` checks for it and says so explicitly rather than building a broken
connection string. Everything else about the connection — host, port, database, schema,
table — is non-secret and lives in `config.yaml` under `database:`.

Then, from the repo root:

```bash
python main.py
```

That runs Bronze, Silver, features, and train in order, and takes about 7 seconds. Each
stage logs what it did and where it wrote.

### Tests

```bash
python -m pytest
```

Use `python -m pytest`, not bare `pytest`. The `-m` form puts the repo root on `sys.path`,
which is what lets `tests/test_main.py` do `import main`. Bare `pytest` fails at collection
with `ModuleNotFoundError: No module named 'main'` unless you add an empty `conftest.py` at
the repo root.

The tests use fakes throughout and never touch the database, so they run offline in well
under a second.

### Changing what it does

Edit `config.yaml`, not the code:

| Key | Effect |
|---|---|
| `model.type` | `xgb` or `logistic_regression` |
| `xgboost.*` | hyperparameters passed straight to `XGBClassifier` |
| `data.features` / `data.categorical_features` | which columns the model sees |
| `data.test_size` / `data.random_state` | the split |
| `evaluation.flag_threshold` | the intervention cutoff |
| `database.schema` / `database.table` | the source table |

### The notebook

```bash
jupyter notebook notebooks/trial_conversion_model.ipynb
```

Still the best place to read the reasoning — the EDA, the binge-pattern finding, the plots.
It prompts for the database password with `getpass` and writes its CSVs to whatever
directory it runs from. The pipeline is the thing to run; the notebook is the thing to read.

**Data source:** `ml.trial_snapshot_latest` on the Beam Postgres instance, maintained by
data engineering. One row per completed trial, carrying base aggregates from the first 3
days (sessions per day, listening sessions, total minutes). Arrived clean — no missing
values, no duplicate trials, only the date columns needing a type fix. Bronze refetches on
every run, so `main.py` needs the database reachable.

## Next steps

1. **Pilot with growth.** The model beats the team's current heuristic of eyeballing raw
   session counts, which was the bar for continuing past the prototype.
2. **Deploy.** To be useful it has to score trials on day 3 while they are still live. The
   pipeline is the first half of that; what is missing is a scheduler, a scoring entry
   point that loads `model.pkl` instead of retraining, and somewhere for the scores to land.
3. **Monitor and retrain.** The trial launched alongside a large marketing campaign, and
   campaign traffic behaves differently from steady-state acquisition. When monitoring shows
   the trial population has drifted from what the model was trained on, retrain on newer
   cohorts.

Known rough edges: Bronze always refetches, so there is no offline mode for iterating on the
model; and the tests cover pipeline wiring only, not `add_features` or `build_design_matrix`.

Out of scope for now: churn among existing paid subscribers, uplift modeling, and any
change to the trial's length, price, or eligibility rules.
