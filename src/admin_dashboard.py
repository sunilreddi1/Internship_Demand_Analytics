import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt

def show_admin_dashboard():
    st.title("📊 Admin Dashboard – Internship Analytics")

    conn = sqlite3.connect("users.db", check_same_thread=False)
    df = pd.read_sql("SELECT * FROM search_logs", conn)
    conn.close()

    if df.empty:
        st.warning("No search data available yet.")
        return

    # ---------------- METRICS ----------------
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Searches", len(df))
    col2.metric("Unique Users", df["username"].nunique())
    col3.metric("Top Skill", df["skill"].value_counts().idxmax())

    st.divider()

    # ---------------- TOP SKILLS ----------------
    st.subheader("🔥 Top Searched Skills")
    st.bar_chart(df["skill"].value_counts().head(5))

    # ---------------- TOP LOCATIONS ----------------
    st.subheader("📍 Top Locations")
    st.bar_chart(df["location"].value_counts().head(5))

    # ---------------- SEARCH TREND ----------------
    st.subheader("📈 Historical Search Trend")
    df["date"] = pd.to_datetime(df["time"]).dt.date
    daily = df.groupby("date").size()
    st.line_chart(daily)

    # ---------------- ML PREDICTION ----------------
    st.subheader("🔮 Future Internship Demand Prediction (ML)")

    # Prepare ML data
    X = np.arange(len(daily)).reshape(-1, 1)
    y = daily.values

    model = LinearRegression()
    model.fit(X, y)

    # Predict next 7 days
    future_days = 7
    future_X = np.arange(len(daily), len(daily) + future_days).reshape(-1, 1)
    future_y = model.predict(future_X)

    # Combine for plotting
    all_y = np.concatenate([y, future_y])

    fig, ax = plt.subplots()
    ax.plot(all_y, marker="o")
    ax.axvline(x=len(y)-1, linestyle="--", color="gray")
    ax.set_title("Internship Demand Prediction")
    ax.set_xlabel("Days")
    ax.set_ylabel("Number of Searches")
    ax.legend(["Predicted Demand"])

    st.pyplot(fig)

    st.success("ML-based future demand prediction generated successfully")
