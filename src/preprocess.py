import pandas as pd
from sklearn.preprocessing import LabelEncoder

def preprocess_data():
    df = pd.read_csv("adzuna_internships_raw.csv")

    for col in ["title", "company", "location", "description"]:
        if col not in df.columns:
            df[col] = "Unknown"

    df["description"] = df["description"].fillna("")
    df["location"] = df["location"].fillna("Unknown")

    if "salary_min" in df.columns:
        df["stipend"] = df["salary_min"].fillna(df["salary_min"].median())
    else:
        df["stipend"] = 8000

    le = LabelEncoder()
    df["location_enc"] = le.fit_transform(df["location"])

    return df
