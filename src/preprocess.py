import pandas as pd
import os
from .demand_model import build_features

def preprocess_data():
    # Get the directory of this file and go up one level to find the CSV
    csv_path = os.path.join(os.path.dirname(__file__), "..", "adzuna_internships_raw.csv")

    # Load only essential columns to reduce memory usage
    essential_columns = [
        'title', 'company', 'location', 'category', 'salary_min', 'salary_max',
        'contract_type', 'description', 'stipend', 'skills_required',
        'is_remote', 'demand_score', 'applications_count'
    ]

    # Load data in chunks and sample to reduce memory usage
    df = pd.read_csv(csv_path, usecols=essential_columns)

    # Optimize data types to reduce memory
    df['stipend'] = df['stipend'].astype('int32')
    df['is_remote'] = df['is_remote'].astype('int8')
    df['demand_score'] = df['demand_score'].astype('float32')
    df['applications_count'] = df['applications_count'].astype('int32')

    # Truncate long descriptions to reduce memory
    df['description'] = df['description'].fillna("").astype(str).str[:500]  # Limit to 500 chars

    df.columns = df.columns.str.lower()
    df = build_features(df)
    return df

