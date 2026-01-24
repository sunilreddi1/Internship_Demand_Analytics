import streamlit as st
import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text
from .preprocess import preprocess_data

def db():
    try:
        # Try to create and test PostgreSQL connection
        engine = create_engine(st.secrets["db"]["url"])
        # Test the connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception as e:
        # Fallback to local SQLite for development (silent fallback)
        return create_engine("sqlite:///users.db")

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import psycopg2
from sqlalchemy import create_engine, text
from .preprocess import preprocess_data
from .demand_model import train_advanced_model
import numpy as np

def db():
    try:
        # Try to create and test PostgreSQL connection
        engine = create_engine(st.secrets["db"]["url"])
        # Test the connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception as e:
        # Fallback to local SQLite for development (silent fallback)
        return create_engine("sqlite:///users.db")

def show_admin_dashboard():
    st.title("📊 Admin Dashboard – Internship Analytics")

    # Load and preprocess data
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
        st.warning(f"Could not load applications data: {e}")
        apps = pd.DataFrame()

    # Create tabs for different analytics views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Overview", "🏢 Company Analysis", "📍 Location Trends",
        "🎯 Skills Demand", "🤖 ML Insights"
    ])

    with tab1:
        show_overview_dashboard(df, apps)

    with tab2:
        show_company_analysis(df, apps)

    with tab3:
        show_location_analysis(df, apps)

    with tab4:
        show_skills_analysis(df)

    with tab5:
        show_ml_insights(df)

def show_overview_dashboard(df, apps):
    st.header("📈 Internship Market Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Internships", len(df))

    with col2:
        avg_stipend = df['stipend'].mean()
        st.metric("Average Stipend", f"₹{avg_stipend:,.0f}")

    with col3:
        remote_count = df['is_remote'].sum()
        st.metric("Remote Opportunities", remote_count)

    with col4:
        if not apps.empty:
            total_applications = len(apps)
            st.metric("Total Applications", total_applications)
        else:
            st.metric("Total Applications", "N/A")

    # Demand distribution
    st.subheader("Demand Distribution")
    fig = px.histogram(df, x='applications_count',
                      title="Distribution of Applications per Internship",
                      labels={'applications_count': 'Number of Applications'})
    st.plotly_chart(fig, use_container_width=True)

    # Stipend vs Applications scatter plot
    st.subheader("Stipend vs Application Volume")
    fig = px.scatter(df, x='stipend', y='applications_count',
                    size='company_score', color='is_remote',
                    title="Stipend vs Applications (Bubble size = Company Reputation)",
                    labels={'stipend': 'Monthly Stipend (₹)', 'applications_count': 'Applications'})
    st.plotly_chart(fig, use_container_width=True)

def show_company_analysis(df, apps):
    st.header("🏢 Company Analysis")

    # Top companies by internship count
    st.subheader("Top Companies by Internship Count")
    company_counts = df['company'].value_counts().head(10)
    fig = px.bar(company_counts, title="Internships by Company",
                labels={'value': 'Number of Internships', 'index': 'Company'})
    st.plotly_chart(fig, use_container_width=True)

    # Company reputation vs applications
    st.subheader("Company Reputation vs Application Success")
    company_stats = df.groupby('company').agg({
        'applications_count': 'mean',
        'company_score': 'first',
        'stipend': 'mean'
    }).reset_index()

    fig = px.scatter(company_stats, x='company_score', y='applications_count',
                    size='stipend', color='stipend',
                    title="Company Reputation vs Average Applications",
                    labels={'company_score': 'Company Reputation Score',
                           'applications_count': 'Average Applications'})
    st.plotly_chart(fig, use_container_width=True)

    # Most applied to companies
    if not apps.empty:
        st.subheader("Most Popular Companies (by Applications)")
        popular_companies = apps['company'].value_counts().head(10)
        fig = px.bar(popular_companies, title="Applications by Company",
                    labels={'value': 'Number of Applications', 'index': 'Company'})
        st.plotly_chart(fig, use_container_width=True)

def show_location_analysis(df, apps):
    st.header("📍 Location & Regional Trends")

    col1, col2 = st.columns(2)

    with col1:
        # Internships by location
        st.subheader("Internships by Location")
        location_counts = df['location'].value_counts().head(10)
        fig = px.pie(location_counts, values=location_counts.values,
                    names=location_counts.index, title="Internship Distribution by City")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Remote vs On-site
        st.subheader("Remote vs On-site")
        remote_stats = df['is_remote'].value_counts()
        labels = ['On-site' if x == 0 else 'Remote' for x in remote_stats.index]
        fig = px.pie(values=remote_stats.values, names=labels,
                    title="Remote Work Distribution")
        st.plotly_chart(fig, use_container_width=True)

    # Average stipend by location
    st.subheader("Average Stipend by Location")
    location_stipend = df.groupby('location')['stipend'].mean().sort_values(ascending=False).head(10)
    fig = px.bar(location_stipend, title="Average Monthly Stipend by Location",
                labels={'value': 'Average Stipend (₹)', 'location': 'Location'})
    st.plotly_chart(fig, use_container_width=True)

    # Applications by location (if data available)
    if not apps.empty:
        st.subheader("Application Volume by Location")
        location_apps = apps['location'].value_counts().head(10)
        fig = px.bar(location_apps, title="Applications by Location",
                    labels={'value': 'Number of Applications', 'index': 'Location'})
        st.plotly_chart(fig, use_container_width=True)

def show_skills_analysis(df):
    st.header("🎯 Skills Demand Analysis")

    # Extract skills from the dataset
    all_skills = []
    for skills_str in df['skills_required'].dropna():
        skills = [s.strip() for s in skills_str.split(',')]
        all_skills.extend(skills)

    if all_skills:
        skills_df = pd.DataFrame(all_skills, columns=['skill'])
        skill_counts = skills_df['skill'].value_counts().head(15)

        # Most demanded skills
        st.subheader("Most Demanded Skills")
        fig = px.bar(skill_counts, title="Top 15 Most Demanded Skills",
                    labels={'value': 'Number of Internships', 'index': 'Skill'})
        st.plotly_chart(fig, use_container_width=True)

        # Skills by category
        st.subheader("Skills Distribution by Job Category")
        category_skills = df.groupby('category')['skills_required'].apply(
            lambda x: ','.join(x.dropna())
        ).reset_index()

        # Create a skills by category visualization
        category_skill_counts = {}
        for _, row in category_skills.iterrows():
            category = row['category']
            skills_text = row['skills_required']
            skills = [s.strip() for s in skills_text.split(',') if s.strip()]
            category_skill_counts[category] = len(set(skills))

        skill_diversity = pd.Series(category_skill_counts).sort_values(ascending=False)
        fig = px.bar(skill_diversity.head(10), title="Skill Diversity by Job Category",
                    labels={'value': 'Unique Skills Required', 'index': 'Job Category'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No skills data available for analysis")

def show_ml_insights(df):
    st.header("🤖 Machine Learning Insights")

    # Train advanced model
    st.subheader("Model Training & Performance")

    try:
        model, scaler, features, metrics = train_advanced_model(df, target_column='applications_count', model_type='rf')

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Training R² Score", f"{metrics['train_r2']}%")

        with col2:
            st.metric("Test R² Score", f"{metrics['test_r2']}%")

        with col3:
            st.metric("Test MAE", f"{metrics['test_mae']:.1f}")

        # Feature importance
        if hasattr(model, 'feature_importances_'):
            st.subheader("Feature Importance")
            importance_df = pd.DataFrame({
                'feature': features,
                'importance': model.feature_importances_
            }).sort_values('importance', ascending=False)

            fig = px.bar(importance_df.head(10), x='importance', y='feature',
                        title="Top 10 Most Important Features",
                        orientation='h')
            st.plotly_chart(fig, use_container_width=True)

        # Model predictions vs actual
        st.subheader("Model Predictions Analysis")
        X = df[features].fillna(0)
        X_scaled = scaler.transform(X)
        predictions = model.predict(X_scaled)

        pred_df = pd.DataFrame({
            'Actual': df['applications_count'].fillna(0),
            'Predicted': predictions,
            'Error': abs(df['applications_count'].fillna(0) - predictions)
        })

        fig = px.scatter(pred_df, x='Actual', y='Predicted',
                        title="Predicted vs Actual Applications",
                        labels={'Actual': 'Actual Applications', 'Predicted': 'Predicted Applications'})
        fig.add_trace(go.Scatter(x=[0, pred_df['Actual'].max()],
                               y=[0, pred_df['Actual'].max()],
                               mode='lines', name='Perfect Prediction',
                               line=dict(dash='dash', color='red')))
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error training model: {e}")
        st.info("This might be due to insufficient data or missing target values. Try with more internship data.")
