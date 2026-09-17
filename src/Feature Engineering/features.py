import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.yaml"

SESSION_DAY_COLUMNS = ["sessions_day1", "sessions_day2", "sessions_day3"]


DIVIDED_COLUMNS = ["day1_share", "listen_share", "avg_session_minutes"]


def add_features(data, config_path=None):
    """Derive the volume, spread, concentration, and listening-mix features."""
    data = data.copy()
    data["sessions_3d"] = data[SESSION_DAY_COLUMNS].sum(axis=1)
    data["active_days_3d"] = (data[SESSION_DAY_COLUMNS] > 0).sum(axis=1)
    data["day1_share"] = data["sessions_day1"] / data["sessions_3d"]
    data["listen_share"] = data["listen_sessions_3d"] / data["sessions_3d"]
    data["avg_session_minutes"] = data["total_minutes_3d"] / data["sessions_3d"]

    no_sessions = int((data["sessions_3d"] == 0).sum())
    if no_sessions:
        logger.info("Trials with no sessions in first 3 days: %d", no_sessions)
    for column in DIVIDED_COLUMNS:
        data[column] = data[column].fillna(0)

    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    with open(path, "r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)

    features_path = PROJECT_ROOT / config["data"]["features_path"]
    features_path.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(features_path, index=False)
    logger.info("Saved engineered features to %s", features_path)

    return data
