"""Clean the Bronze dataset and persist the Silver layer."""

import logging
from pathlib import Path

import pandas as pd
import yaml

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def clean_data(config_path=None):
    """Load, clean, and save the configured Bronze dataset."""
    path = Path(config_path) if config_path else PROJECT_ROOT / "config.yaml"
    with open(path, "r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)

    raw_data_path = PROJECT_ROOT / config["data"]["raw_path"]
    clean_path = PROJECT_ROOT / config["data"]["clean_path"]
    clean_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Reading raw data from %s", raw_data_path)
    df = pd.read_csv(raw_data_path)
    logger.info("Loaded %d rows", len(df))

    df = df.drop_duplicates()
    logger.info("Removed duplicates. Now have %d rows", len(df))

    df = df.dropna()
    logger.info("Removed rows with missing values. Now have %d rows", len(df))

    date_columns = ["snapshot_date", "trial_started_at"]
    for column in date_columns:
        df[column] = pd.to_datetime(df[column], errors="coerce", format="mixed")

    invalid_dates = int(df[date_columns].isna().any(axis=1).sum())
    if invalid_dates:
        logger.warning("Dropping %d rows with invalid dates", invalid_dates)
        df = df.dropna(subset=date_columns)
    logger.info("Converted date columns to datetime")

    df.to_csv(clean_path, index=False)
    logger.info("Saved %d cleaned rows to %s", len(df), clean_path)

    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    result = clean_data()
    logger.info("Silver stage complete: %d rows", len(result))
