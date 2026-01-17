import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt

def show_admin_dashboard():
    st.title("📊 Admin Dashboard – Internship Analytics")

    conn = sqlite3.connect("users.db")
    df = pd.read_sql("SELECT * FROM search_logs", conn)
    conn.close()

    if df.empty:
        st.warning("No search data yet")
        return

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Searches", len(df))
    col2.metric("Unique Users", df["username"].nunique())
    col3.metric("Top Skill", df["skill"].value_counts().idxmax())

    st.subheader("🔥 Top Skills")
    st.bar_chart(df["skill"].value_counts().head(7))

    st.subheader("📍 Top Locations")
    st.bar_chart(df["location"].value_counts().head(7))

    st.subheader("📈 Search Trend")
    df["date"] = pd.to_datetime(df["time"]).dt.date
    daily = df.groupby("date").size()
    st.line_chart(daily)

    st.subheader("🔮 Demand Prediction (ML)")
    X = np.arange(len(daily)).reshape(-1, 1)
    y = daily.values
    model = LinearRegression().fit(X, y)

    future_X = np.arange(len(y), len(y) + 7).reshape(-1, 1)
    future_y = model.predict(future_X)

    fig, ax = plt.subplots()
    ax.plot(list(y) + list(future_y), marker="o")
    ax.axvline(len(y)-1, linestyle="--")
    st.pyplot(fig)
