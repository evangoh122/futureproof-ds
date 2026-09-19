# Import necessary libraries
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from pathlib import Path
import yaml
import logging
from trial_conversion.paths import PROJECT_ROOT

load_dotenv()

logger = logging.getLogger(__name__)



# Create silver layer - This is where the data is cleaned and transformed for modeling
def clean_data(config_path=None):
    """
    Load the raw data and clean it and save it to disk
    """
    path = Path(config_path) if config_path else PROJECT_ROOT / "config.yaml"
    with open(path, "r") as f:
        config = yaml.safe_load(f)

    raw_data_path = PROJECT_ROOT /config["data"]["raw_path"]
    clean_path =  PROJECT_ROOT /config["data"]["clean_path"]
    clean_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Reading raw data from %s", raw_data_path)
    df = pd.read_csv(raw_data_path)
    logger.info("Loaded %d rows", len(df))  
    
    # Remove duplicates
    df = df.drop_duplicates()


    # Remove rows with missing values
    df = df.dropna()
    

    # Fix date time Columns
    date_columns = ["snapshot_date", "trial_started_at"]
    df[date_columns] = df[date_columns].apply(pd.to_datetime, errors='coerce')
   

    # Save Silver layer to CSV
    df.to_csv(clean_path, index=False)
    logger.info("Saved %d cleaned rows to %s", len(df), clean_path)

    return df