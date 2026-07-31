# Beam trial conversion model

Beam launched a 14-day free trial on August 1, 2026, and the growth team wants to know, while a trial is still live, which trials are unlikely to convert to a paid plan. This repository contains the first version of that model: a notebook that predicts conversion from a trial's first 3 days of behavior, which leaves 11 days of runway for the growth team to intervene on trials that look like they will not convert.

The repository contains three files. `trial-conversion-model-plan.md` is the planning document written after the growth team's request, and it explains the business case, who will use the model, and how it should eventually be delivered. `trial_conversion_model.ipynb` is the model notebook, covering exploration, features, an XGBoost model, and evaluation. `trial_snapshot.csv` is the extract of completed trials that the notebook trains on, pulled from the `ml.trial_snapshot` table.

To run the notebook, install the dependencies with `pip install pandas numpy matplotlib scikit-learn xgboost jupyter`, then open it and run all cells.
