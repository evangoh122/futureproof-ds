import logging
from pathlib import Path

import pandas as pd
import yaml
from dotenv import dotenv_values
from sqlalchemy import create_engine

logger = logging.getLogger(__name__)

from trial_conversion.paths import ENV_PATH, CONFIG_PATH, PROJECT_ROOT

USER_KEY = "Username"
PASSWORD_KEY = "Password"


def load_config(config_path=None):
    """Read the pipeline settings that name the source table and output path."""
    path = Path(config_path) if config_path else CONFIG_PATH
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def read_credentials(env_path=None):
    """Read the database username and password from a .env file."""
    path = Path(env_path) if env_path else ENV_PATH
    if not path.exists():
        raise RuntimeError(
            f"No .env file at {path}. Copy .env.example to .env and fill in "
            f"{USER_KEY} and {PASSWORD_KEY}."
        )

    values = dotenv_values(path)
    missing = [key for key in (USER_KEY, PASSWORD_KEY) if not values.get(key)]
    if missing:
        raw = path.read_text(encoding="utf-8")
        hint = ""
        if any(f"{key}:" in raw for key in missing):
            hint = (
                " The file uses 'Key: value', but .env needs 'KEY=value'. "
                "Replace the colons with equals signs."
            )
        raise RuntimeError(
            f"{path} is missing a value for {' and '.join(missing)}.{hint}"
        )

    return values[USER_KEY], values[PASSWORD_KEY]


def build_connection_url(config, user, password):
    """Assemble the Postgres URL from config plus the two secrets."""
    database = config["database"]
    return (
        f"postgresql://{user}:{password}"
        f"@{database['host']}:{database['port']}/{database['name']}"
    )


def extract_raw_data(config_path=None):
    """Extract the raw trial data from the Postgres database and save it to disk.
    """
    config = load_config(config_path)
    database = config["database"]
    user, password = read_credentials()

    source_table = f"{database['schema']}.{database['table']}"
    raw_path = PROJECT_ROOT / config["data"]["raw_path"]
    raw_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Reading %s from %s", source_table, database["host"])
    engine = create_engine(build_connection_url(config, user, password))
    try:
        frame = pd.read_sql(f"SELECT * FROM {source_table}", engine)
    finally:
        engine.dispose()

    frame.to_csv(raw_path, index=False)
    logger.info("Saved %d raw rows to %s", len(frame), raw_path)
    return frame
