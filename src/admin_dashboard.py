import streamlit as st
import pandas as pd
import psycopg2
from sqlalchemy import create_engine
from .preprocess import preprocess_data

def db():
    # Check if we've already shown the fallback warning this session
    if not hasattr(st.session_state, 'db_fallback_shown'):
        st.session_state.db_fallback_shown = False

    try:
        # Return SQLAlchemy engine for PostgreSQL
        return create_engine(st.secrets["db"]["url"])
    except Exception as e:
        if not st.session_state.db_fallback_shown:
            st.info("🔄 Using local database for testing. Your data will be stored locally.")
            st.session_state.db_fallback_shown = True
        # Fallback to local SQLite for development
        return create_engine("sqlite:///users.db")

def show_admin_dashboard():
    st.title("📊 Admin Dashboard – Internship Analytics")

    # Load internship data
    df = preprocess_data()

    # Load applications data
    try:
        engine = db()
        if 'postgresql' in str(engine.url):
            apps = pd.read_sql("""
                SELECT job_title, company, location, applied_at, username
                FROM applications
                ORDER BY applied_at DESC
            """, engine)
        else:  # SQLite - check schema and adapt
            with engine.connect() as conn:
                cur = conn.connection.cursor()
                cur.execute("PRAGMA table_info(applications)")
                columns = [col[1] for col in cur.fetchall()]
                
                if 'job_title' in columns:
                    apps = pd.read_sql_query("""
                        SELECT job_title, company, location, applied_at, username
                        FROM applications
                        ORDER BY applied_at DESC
                    """, engine)
                else:
                    # Use existing schema
                    apps = pd.read_sql_query("""
                        SELECT job_id as job_title, status as company, '' as location, id as applied_at, username
                        FROM applications
                        ORDER BY id DESC
                    """, engine)
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
        st.dataframe(apps.head(10), width='stretch')
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
