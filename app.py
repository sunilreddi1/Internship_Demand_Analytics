import streamlit as st
import sqlite3
import pandas as pd

from src.resume_parser import extract_skills_from_resume
from src.recommender import compute_match_score
from src.admin_dashboard import show_admin_dashboard

st.set_page_config("Internship Demand Portal", "🎓", layout="wide")

# ---------------- DB ----------------
def db():
    return sqlite3.connect("users.db", check_same_thread=False)

def log_search(user, skill, location):
    conn = db()
    conn.execute(
        "INSERT INTO search_logs (username, skill, location) VALUES (?,?,?)",
        (user, skill, location)
    )
    conn.commit()
    conn.close()

# ---------------- SESSION ----------------
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None

# ---------------- LOGIN ----------------
if not st.session_state.user:
    st.title("🎓 Internship Portal")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    role = st.selectbox("Role", ["Student", "Admin"])

    if st.button("Login / Register"):
        conn = db()
        conn.execute(
            "INSERT OR IGNORE INTO users (username, password, role) VALUES (?,?,?)",
            (u, p, role)
        )
        conn.commit()
        conn.close()

        st.session_state.user = u
        st.session_state.role = role
        st.rerun()

# ---------------- ADMIN ----------------
elif st.session_state.role == "Admin":
    show_admin_dashboard()

# ---------------- STUDENT ----------------
else:
    st.title("🚀 Internship Recommendation System")

    df = pd.read_csv("adzuna_internships_raw.csv")
    df.columns = df.columns.str.lower()
    df["description"] = df["description"].fillna("")

    skill = st.text_input("🔍 Skill")
    location = st.selectbox(
        "📍 Location",
        sorted(df["location"].dropna().unique())
    )

    resume = st.file_uploader("📄 Upload Resume (PDF)", type="pdf")
    user_skills = extract_skills_from_resume(resume) if resume else []

    if st.button("Search Internships"):
        log_search(st.session_state.user, skill, location)

        results = []
        for _, row in df.iterrows():
            job_skills = row["description"].lower().split()
            score = compute_match_score(
                job_skills, user_skills, row.get("stipend", 15000)
            )

            if skill.lower() in row["title"].lower() and location.lower() in row["location"].lower():
                results.append((score, row))

        results = sorted(results, key=lambda x: x[0], reverse=True)[:10]

        for score, job in results:
            st.markdown(f"""
            ### {job['title']}
            🏢 {job['company']}  
            📍 {job['location']}  
            🎯 Match Score: **{score}%**
            """)

            if st.button(f"Apply – {job['title']}", key=job['title']):
                conn = db()
                conn.execute(
                    "INSERT INTO applications (username, job_id, status) VALUES (?,?,?)",
                    (st.session_state.user, job['title'], "Pending")
                )
                conn.commit()
                conn.close()
                st.success("Application submitted 🎉")
