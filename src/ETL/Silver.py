# Import necessary libraries
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

# Create silver layer - This is where the data is cleaned and transformed for modeling
def clean_data():
    df = pd.read_csv("data/01_raw/trials_raw.csv")

    # Remove duplicates
    df = df.drop_duplicates()

    # Remove rows with missing values
    df = df.dropna()

    # Fix date time Columns
    date_columns = ["snapshot_date", "trial_started_at"]
    df[date_columns] = df[date_columns].apply(pd.to_datetime, errors='coerce')

    return df