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

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Searches", len(df))
    c2.metric("Unique Users", df["username"].nunique())
    c3.metric("Top Skill", df["skill"].value_counts().idxmax())

    st.subheader("🔥 Top Skills")
    st.bar_chart(df["skill"].value_counts().head(5))

    st.subheader("📍 Top Locations")
    st.bar_chart(df["location"].value_counts().head(5))

    st.subheader("📈 Search Trend")
    df["date"] = pd.to_datetime(df["time"]).dt.date
    daily = df.groupby("date").size()
    st.line_chart(daily)

    st.subheader("🔮 Demand Prediction (ML)")
    X = np.arange(len(daily)).reshape(-1, 1)
    y = daily.values
    model = LinearRegression().fit(X, y)

    future = model.predict(
        np.arange(len(y), len(y) + 7).reshape(-1, 1)
    )

    fig, ax = plt.subplots()
    ax.plot(list(y) + list(future), marker="o")
    ax.axvline(len(y)-1, linestyle="--")
    st.pyplot(fig)
