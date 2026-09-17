# Import necessary libraries
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

# Create silver layer
def clean_data():
    df_1 = pd.read_csv("data/01_raw/trials_raw.csv")

    # Remove duplicates
    df_1 = df_1.drop_duplicates()

    # Remove rows with missing values
    df_1 = df_1.dropna()

    # Fix data types
    