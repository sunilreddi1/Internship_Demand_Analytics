import streamlit as st
import pandas as pd
import psycopg2
from .preprocess import preprocess_data

def db():
    try:
        return psycopg2.connect(st.secrets["db"]["url"], sslmode="require")
    except Exception as e:
        st.warning(f"Database connection failed: {e}. Using local SQLite for testing.")
        import sqlite3
        return sqlite3.connect("users.db")

def show_admin_dashboard():
    st.title("📊 Admin Dashboard – Internship Analytics")

    # Load internship data
    df = preprocess_data()

    # Load applications data
    try:
        conn = db()
        if hasattr(conn, 'autocommit'):  # PostgreSQL
            apps = pd.read_sql("""
                SELECT job_title, company, location, applied_at, username
                FROM applications
                ORDER BY applied_at DESC
            """, conn)
        else:  # SQLite
            apps = pd.read_sql_query("""
                SELECT job_title, company, location, applied_at, username
                FROM applications
                ORDER BY applied_at DESC
            """, conn)
        conn.close()
    except Exception as e:
        st.error(f"Failed to load applications data: {e}")
        apps = pd.DataFrame()  # Empty dataframe as fallback

    # Metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Internships", len(df))
    c2.metric("Total Applications", len(apps))
    c3.metric("Unique Students", apps["username"].nunique() if not apps.empty else 0)
    c4.metric("Avg Stipend", f"₹{int(df['stipend'].mean())}")

    st.divider()

    # Applications Overview
    st.subheader("📋 Recent Applications")
    if not apps.empty:
        st.dataframe(apps.head(10), use_container_width=True)
    else:
        st.info("No applications yet")

    # Popular Companies
    st.subheader("🏢 Popular Companies")
    if not apps.empty:
        company_counts = apps["company"].value_counts().head(10)
        st.bar_chart(company_counts)
    else:
        st.bar_chart(df["company"].value_counts().head(10))

    # Location Distribution
    st.subheader("📍 Location Distribution")
    if not apps.empty:
        location_counts = apps["location"].value_counts().head(10)
        st.bar_chart(location_counts)
    else:
        st.bar_chart(df["location"].value_counts().head(10))

    # Skill Demand Analysis
    st.subheader("🔥 Skill Demand Analysis")
    skill_counts = {}
    for desc in df["description"].fillna(""):
        for skill in ["python","java","sql","machine learning","data science","ai","react","django","flask","aws","docker","html","css","javascript"]:
            if skill in desc.lower():
                skill_counts[skill] = skill_counts.get(skill, 0) + 1

    if skill_counts:
        skill_df = pd.DataFrame(list(skill_counts.items()), columns=["Skill","Count"]).sort_values("Count", ascending=False)
        st.bar_chart(skill_df.set_index("Skill"))
    else:
        st.info("No skill data available")

    # Stipend Distribution
    st.subheader("💰 Stipend Distribution")
    stipend_bins = pd.cut(df["stipend"], bins=[0,5000,10000,15000,20000,50000], labels=["<5K","5-10K","10-15K","15-20K","20K+"])
    st.bar_chart(stipend_bins.value_counts().sort_index())
