# USER comment
Going back to trying out how to develop models on open source systems, at work I use Data Bricks so, I hope to revise dockerizing and deploying it on AWS again.

# Beam Trial Conversion Model

Predicts, from a trial's **first 3 days of behavior**, whether a 14-day Beam trial will
convert to a paid plan — early enough for the growth team to intervene on the ones that
won't.

**Status:** prototype. The offline model is validated and `model.pkl` is ready to share;
nothing is deployed or scoring live trials yet.

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

XGBoost accuracy at a 0.5 cutoff is 0.797, with balanced precision and recall on both
classes.

What matters more than AUC is whether the low-scoring group is a usable intervention list.
Scoring the test set and flagging everything below 0.35:

- 153 of 379 trials flagged
- flagged trials converted at **18.3%**
- everyone else converted at **77.0%**

That separation is what an intervention list should look like. The cutoff itself is the
lifecycle team's call, not a modeling decision — it depends on how many trials they can
actually work through in a week.

### What the model reads

Feature importance lands where the exploration suggested: total first-3-day usage
dominates, then how concentrated that usage was on day 1, then how much of it was
listening. The binge pattern is the interesting one — users who cram most of their sessions
into day 1 and then go quiet convert at 24%, against 62% for everyone else, *at the same
session total*. That interaction is why the tree model beats the linear baseline.

Derived features, all built in `add_features()`: `sessions_3d`, `active_days_3d`,
`day1_share`, `listen_share`, `avg_session_minutes`. Raw `total_minutes_3d`, `country`, and
`device_type` go in alongside them. 38 trials had zero sessions in the first 3 days; their
share/average features divide by zero and are filled with 0, since zero engagement is real
information rather than a missing value.

## Layout

```
notebooks/trial_conversion_model.ipynb   the whole analysis: load → clean → EDA → features → model → eval
trial-conversion-model-plan.md           business case, stakeholders, roadmap, out-of-scope
data/raw/                                trials_raw.csv (as pulled), trials_clean.csv (post-feature-build)
model.pkl                                pickled XGBoost classifier
src/ scripts/ tests/                     empty — placeholders for the deployment hand-off
```

The CSVs and `model.pkl` are gitignored; they are reproducible from the notebook.

## Running it

Python 3.11. There is no lockfile yet — the versions this was run against:

```
pandas 2.2.2   numpy 2.2.6   scikit-learn 1.5.2   xgboost 2.1.1
matplotlib 3.8.4   SQLAlchemy 2.0.32   psycopg2-binary   jupyter 1.1.1
```

```bash
python -m venv .venv && .venv/Scripts/activate   # Windows; use bin/activate elsewhere
pip install pandas numpy scikit-learn xgboost matplotlib sqlalchemy psycopg2-binary jupyter
jupyter notebook notebooks/trial_conversion_model.ipynb
```

Run top to bottom. Cell 4 prompts for the database password with `getpass`.

**Data source:** `ml.trial_snapshot_latest` on the Beam Postgres instance, maintained by
data engineering. One row per completed trial, carrying base aggregates from the first 3
days (sessions per day, listening sessions, total minutes); all feature work happens in the
notebook. Arrived clean — no missing values, no duplicate trials, only the date columns
needing a type fix.

Note that the notebook writes `trials_raw.csv`, `trials_clean.csv`, and `model.pkl` to
whatever directory it runs from, not to `data/raw/` — the copies committed here were moved
into place by hand. Worth tidying when this moves out of a notebook.

## Next steps

1. **Pilot with growth.** The model beats the team's current heuristic of eyeballing raw
   session counts, which was the bar for continuing past the prototype.
2. **Deploy.** To be useful it has to score trials on day 3 while they are still live,
   which means running somewhere other than a notebook. Scoping this with engineering is
   the next conversation — `src/`, `scripts/`, and `tests/` are waiting for it.
3. **Monitor and retrain.** The trial launched alongside a large marketing campaign, and
   campaign traffic behaves differently from steady-state acquisition. When monitoring
   shows the trial population has drifted from what the model was trained on, retrain on
   newer cohorts.

Out of scope for now: churn among existing paid subscribers, uplift modeling, and any
change to the trial's length, price, or eligibility rules.
