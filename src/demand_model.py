import pandas as pd
import streamlit as st
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

def predict_demand(stipend):
    if stipend > 20000:
        return "High"
    elif stipend > 10000:
        return "Medium"
    return "Low"

def build_features(df):
    df["stipend"] = df.get("stipend", 15000).fillna(15000)
    df["skill_count"] = df["description"].apply(lambda x: len(set(x.lower().split())))
    df["company_score"] = df["company"].map(df["company"].value_counts()).fillna(1)
    df["is_remote"] = df["location"].str.contains("remote", case=False, na=False).astype(int)
    df["demand"] = (
        0.4 * df["stipend"] +
        20 * df["skill_count"] +
        500 * df["company_score"] +
        300 * df["is_remote"]
    )
    return df

@st.cache_resource
def train_model(df):
    X = df[["stipend","skill_count","company_score","is_remote"]]
    y = df["demand"]
    model = LinearRegression().fit(X, y)
    return model, round(r2_score(y, model.predict(X))*100, 2)