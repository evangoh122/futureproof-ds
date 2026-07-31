# Beam trial conversion model

Predicts, from a trial's first 3 days of behavior, whether the user will convert to a paid plan at the end of Beam's 14-day trial. Day-3 scoring leaves 11 days of runway for growth to intervene on trials that look like they won't convert.

- `trial_conversion_model.ipynb`: the model notebook (EDA, features, XGBoost, evaluation)
- `trial_snapshot.csv`: extract of completed trials from `ml.trial_snapshot`

To run: `pip install pandas numpy matplotlib scikit-learn xgboost jupyter`, then open the notebook and run all cells.
