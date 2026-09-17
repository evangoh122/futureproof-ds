# Import necessary libraries
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

# Load environment variables from .env file
def load_env_variables():
    load_dotenv()
    db_host = os.getenv("Host")
    db_port = os.getenv("Port")
    db_name = os.getenv("Database")
    db_user = os.getenv("Username")
    db_password = os.getenv("Password")

    # Create bronze layer - This is where the raw data is extracted from the database and stored in a CSV file
    # In a SQL environment, this would be a SQL query to extract the data from the database and store it in a SQL or Delta Table
    engine = create_engine(f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}")

    df = pd.read_sql("SELECT * FROM ml.trial_conversion", engine)

    df.to_csv("data/01_raw/trials_raw.csv", index=False)