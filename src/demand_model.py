import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.feature_extraction.text import TfidfVectorizer
import re
import streamlit as st

def predict_demand(stipend):
    """Legacy simple prediction for backward compatibility"""
    if stipend > 20000:
        return "High"
    elif stipend > 10000:
        return "Medium"
    return "Low"

def extract_features_from_text(text):
    """Extract features from job description"""
    text = str(text).lower()

    # Technical skills keywords
    tech_skills = ['python', 'java', 'javascript', 'sql', 'react', 'node', 'aws', 'docker',
                  'machine learning', 'data science', 'ai', 'cloud', 'git', 'linux']
    tech_count = sum(1 for skill in tech_skills if skill in text)

    # Soft skills keywords
    soft_skills = ['communication', 'leadership', 'teamwork', 'problem solving', 'analytical']
    soft_count = sum(1 for skill in soft_skills if skill in text)

    # Experience level indicators
    entry_keywords = ['fresher', 'entry level', 'beginner', 'internship', 'no experience']
    entry_level = 1 if any(keyword in text for keyword in entry_keywords) else 0

    # Company reputation indicators
    premium_keywords = ['google', 'microsoft', 'amazon', 'meta', 'apple', 'startup', 'funded']
    premium_company = 1 if any(keyword in text for keyword in premium_keywords) else 0

    return {
        'tech_skill_count': tech_count,
        'soft_skill_count': soft_count,
        'entry_level': entry_level,
        'premium_company': premium_company,
        'description_length': len(text)
    }

def build_advanced_features(df):
    """Enhanced feature engineering for better predictions"""
    # Basic features
    df["stipend"] = df.get("stipend", 15000).fillna(15000)
    df["salary_min"] = pd.to_numeric(df.get("salary_min", 0), errors='coerce').fillna(0)
    df["salary_max"] = pd.to_numeric(df.get("salary_max", 0), errors='coerce').fillna(0)

    # Location features
    df["is_remote"] = df["location"].str.contains("remote", case=False, na=False).astype(int)
    df["is_metro"] = df["location"].str.contains("delhi|mumbai|bangalore|chennai|kolkata|hyderabad|pune", case=False, na=False).astype(int)

    # Company features
    df["company_score"] = df["company"].map(df["company"].value_counts()).fillna(1)
    df["company_reputation"] = df["company_score"].apply(lambda x: 1 if x > 5 else 0)

    # Category/domain features
    df["is_tech"] = df["category"].str.contains("IT|Software|Data|Engineering", case=False, na=False).astype(int)
    df["is_finance"] = df["category"].str.contains("Finance|Accounting", case=False, na=False).astype(int)
    df["is_marketing"] = df["category"].str.contains("Marketing|Sales|PR", case=False, na=False).astype(int)

    # Extract text features from description
    text_features = df["description"].apply(extract_features_from_text)
    text_df = pd.DataFrame(list(text_features))

    # Combine all features
    df = pd.concat([df, text_df], axis=1)

    # Fill any remaining NaN values
    df = df.fillna(0)

    return df

def build_features(df):
    """Legacy function for backward compatibility"""
    return build_advanced_features(df)

@st.cache_resource
def train_advanced_model(df, target_column='applications_count', model_type='rf'):
    """
    Train advanced ML models for internship demand prediction

    Args:
        df: DataFrame with internship data
        target_column: Column to predict ('applications_count' or 'demand_score')
        model_type: 'rf' (Random Forest), 'gb' (Gradient Boosting), 'ridge' (Ridge Regression)

    Returns:
        model, scaler, feature_columns, metrics
    """
    # Prepare features
    feature_columns = [
        'stipend', 'salary_min', 'salary_max', 'is_remote', 'is_metro',
        'company_score', 'company_reputation', 'is_tech', 'is_finance', 'is_marketing',
        'tech_skill_count', 'soft_skill_count', 'entry_level', 'premium_company', 'description_length'
    ]

    X = df[feature_columns]
    y = df[target_column]

    # Handle missing target values
    valid_idx = y.notna() & (y > 0)
    X = X[valid_idx]
    y = y[valid_idx]

    if len(X) < 10:
        # Fallback to simple model if insufficient data
        return train_model(df)

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Train model based on type
    if model_type == 'rf':
        model = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10)
    elif model_type == 'gb':
        model = GradientBoostingRegressor(n_estimators=100, random_state=42, max_depth=5)
    elif model_type == 'ridge':
        model = Ridge(alpha=1.0)
    else:
        model = LinearRegression()

    model.fit(X_train_scaled, y_train)

    # Predictions
    y_pred_train = model.predict(X_train_scaled)
    y_pred_test = model.predict(X_test_scaled)

    # Calculate metrics
    metrics = {
        'train_r2': round(r2_score(y_train, y_pred_train) * 100, 2),
        'test_r2': round(r2_score(y_test, y_pred_test) * 100, 2),
        'train_mae': round(mean_absolute_error(y_train, y_pred_train), 2),
        'test_mae': round(mean_absolute_error(y_test, y_pred_test), 2),
        'train_rmse': round(np.sqrt(mean_squared_error(y_train, y_pred_train)), 2),
        'test_rmse': round(np.sqrt(mean_squared_error(y_test, y_pred_test)), 2)
    }

    return model, scaler, feature_columns, metrics

@st.cache_resource
def train_model(df):
    """Legacy function for backward compatibility"""
    X = df[["stipend","tech_skill_count","company_score","is_remote"]]
    y = df["demand_score"]  # Use demand_score instead of demand
    model = LinearRegression().fit(X, y)
    return model, round(r2_score(y, model.predict(X))*100, 2)

def predict_internship_demand(model, scaler, feature_columns, internship_data):
    """
    Predict demand for a single internship

    Args:
        model: Trained ML model
        scaler: Feature scaler
        feature_columns: List of feature column names
        internship_data: Dict with internship features

    Returns:
        predicted_demand: Float prediction
    """
    # Create feature vector
    features = []
    for col in feature_columns:
        features.append(internship_data.get(col, 0))

    # Scale and predict
    features_scaled = scaler.transform([features])
    prediction = model.predict(features_scaled)[0]

    return round(prediction, 2)