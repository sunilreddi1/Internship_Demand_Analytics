import streamlit as st
import sqlite3
import pandas as pd

def show_admin_dashboard():
    st.title("📊 Admin Dashboard – Internship Analytics")

    conn = sqlite3.connect("users.db", check_same_thread=False)

    # ---------- SEARCH LOG DATA ----------
    df = pd.read_sql("SELECT * FROM search_logs", conn)

    if df.empty:
        st.warning("No search data available yet.")
        return

    # ---------- METRICS ----------
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Searches", len(df))
    col2.metric("Unique Users", df["username"].nunique())
    col3.metric("Top Skill", df["skill"].value_counts().idxmax())

    st.divider()

    # ---------- TOP SKILLS ----------
    st.subheader("🔥 Top Searched Skills")
    skill_counts = df["skill"].value_counts().head(5)
    st.bar_chart(skill_counts)

    # ---------- TOP LOCATIONS ----------
    st.subheader("📍 Top Locations")
    location_counts = df["location"].value_counts().head(5)
    st.bar_chart(location_counts)

    # ---------- SEARCH TREND ----------
    st.subheader("📈 Search Trend Over Time")
    df["date"] = pd.to_datetime(df["time"]).dt.date
    trend = df.groupby("date").size()
    st.line_chart(trend)

    st.divider()
    st.success("Admin analytics updated in real time")
