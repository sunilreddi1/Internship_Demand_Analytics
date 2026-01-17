import streamlit as st
import sqlite3
import pandas as pd

# ✅ FIXED IMPORTS (FROM src FOLDER)
from src.resume_parser import extract_skills_from_resume
from src.recommender import compute_match_score
from src.admin_dashboard import show_admin_dashboard

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Internship Demand & Recommendation Portal",
    page_icon="🎓",
    layout="wide"
)

# ---------------- DATABASE ----------------
def get_db():
    return sqlite3.connect("users.db", check_same_thread=False)

def log_search(username, skill, location):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO search_logs (username, skill, location) VALUES (?, ?, ?)",
        (username, skill, location)
    )
    conn.commit()
    conn.close()

# ---------------- SESSION ----------------
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None

# ---------------- LOGIN / REGISTER ----------------
if not st.session_state.user:
    st.title("🎓 Internship Portal")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    role = st.selectbox("Role", ["Student", "Admin"])

    if st.button("Login / Register"):
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, password, role)
        )
        conn.commit()
        conn.close()

        st.session_state.user = username
        st.session_state.role = role
        st.success("Login successful")
        st.rerun()

# ---------------- ADMIN DASHBOARD ----------------
elif st.session_state.role == "Admin":
    show_admin_dashboard()

# ---------------- STUDENT DASHBOARD ----------------
else:
    st.title("🚀 Internship Recommendation System")

    df = pd.read_csv("adzuna_internships_raw.csv")
    df.columns = df.columns.str.lower()

    skill = st.text_input("🔍 Search Skill (Python, Data, Web)")
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
            job_skills = str(row.get("skills", "")).lower().split(",")
            score = compute_match_score(
                job_skills,
                user_skills,
                row.get("stipend", 15000)
            )

            if skill.lower() in row["title"].lower() and location.lower() in row["location"].lower():
                results.append((score, row))

        results = sorted(results, key=lambda x: x[0], reverse=True)[:10]

        for score, job in results:
            st.markdown(f"""
            ### {job['title']}
            🏢 **{job['company']}**  
            📍 {job['location']}  
            💰 ₹{job.get('stipend',15000)}  
            🎯 Match Score: **{score}%**
            """)

            if st.button(f"Apply – {job['title']}", key=job['title']):
                conn = get_db()
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO applications (username, job_id, status) VALUES (?, ?, ?)",
                    (st.session_state.user, job['title'], "Pending")
                )
                conn.commit()
                conn.close()
                st.success("Application submitted 🎉")
