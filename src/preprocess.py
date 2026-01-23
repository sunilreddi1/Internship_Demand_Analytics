import pandas as pd
import os
from .demand_model import build_features

def preprocess_data():
    # Get the directory of this file and go up one level to find the CSV
    csv_path = os.path.join(os.path.dirname(__file__), "..", "adzuna_internships_raw.csv")
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.lower()
    df["description"] = df["description"].fillna("")
    df = build_features(df)
    return df
