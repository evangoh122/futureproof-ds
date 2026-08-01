# Beam trial conversion model

Beam launched a 14-day free trial about two months ago, and the growth team wants to know, while a trial is still live, which trials are unlikely to convert to a paid plan. This repository contains the first version of that model: a notebook that predicts conversion from a trial's first 3 days of behavior, which leaves 11 days of runway for the growth team to intervene on trials that look like they will not convert.

The repository contains two files. `trial-conversion-model-plan.md` is the planning document written after the growth team's request, and it explains the business case, who will use the model, and how it should eventually be delivered. `trial_conversion_model.ipynb` is the model notebook, covering exploration, features, an XGBoost model, and evaluation.

The notebook pulls its data directly from the `ml.trial_snapshot_latest` view in the analytics database. When you run it, a prompt asks for the database password; use the read-only credentials from the course's Tools & Setup lesson. No data or credentials are stored in this repository.

The notebook runs anywhere Jupyter runs. In Google Colab it works out of the box; locally, install the dependencies first with `pip install pandas numpy matplotlib scikit-learn xgboost sqlalchemy psycopg2-binary jupyter`.
