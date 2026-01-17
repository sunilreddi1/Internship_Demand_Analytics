import streamlit as st
import sqlite3
import pandas as pd
import os

# ---------------- AUTO DB INIT (STREAMLIT CLOUD SAFE) ----------------
if not os.path.exists("users.db"):
    import init_db

from src.resume_parser import extract_skills_from_resume
from src.recommender import compute_match_score
from src.admin_dashboard import show_admin_dashboard

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Internship Demand Portal",
    page_icon="🎓",
    layout="wide"
)

# ---------------- UI STYLES (LINKEDIN STYLE) ----------------
st.markdown("""
<style>

/* ===== BACKGROUND IMAGE ===== */
[data-testid="stAppViewContainer"] {
    background-image: url("https://images.unsplash.com/photo-1522202176988-66273c2fd55f");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}

/* ===== MAIN OVERLAY ===== */
.main {
    background-color: rgba(255,255,255,0.88);
    padding: 2rem;
    border-radius: 18px;
}

/* ===== HEADINGS ===== */
h1, h2, h3 {
    color: #0a66c2;
    font-weight: 700;
}

/* ===== CARD ===== */
.card {
    background: rgba(255,255,255,0.95);
    padding: 22px;
    border-radius: 18px;
    margin-bottom: 20px;
    box-shadow: 0 12px 30px rgba(0,0,0,0.15);
}

/* ===== BUTTONS ===== */
button {
    background: linear-gradient(90deg,#0a66c2,#004182) !important;
    color: white !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}

/* ===== INPUTS ===== */
input, select {
    border-radius: 8px !important;
}

</style>
""", unsafe_allow_html=True)

# ---------------- DATABASE ----------------
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

# ---------------- LOGIN / REGISTER ----------------
if not st.session_state.user:
    st.markdown("<div class='main'>", unsafe_allow_html=True)
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    st.title("🎓 Internship Demand & Recommendation Portal")
    st.caption("Find internships that match your skills and market demand")

    username = st.text_input("👤 Username")
    password = st.text_input("🔑 Password", type="password")
    role = st.selectbox("Role", ["Student", "Admin"])

    if st.button("Login / Register"):
        if username and password:
            conn = db()
            conn.execute(
                "INSERT OR IGNORE INTO users (username, password, role) VALUES (?,?,?)",
                (username, password, role)
            )
            conn.commit()
            conn.close()

            st.session_state.user = username
            st.session_state.role = role
            st.success("Login successful 🎉")
            st.rerun()
        else:
            st.error("Please fill all fields")

    st.markdown("</div></div>", unsafe_allow_html=True)

# ---------------- ADMIN DASHBOARD ----------------
elif st.session_state.role == "Admin":
    st.markdown("<div class='main'>", unsafe_allow_html=True)
    show_admin_dashboard()
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- STUDENT DASHBOARD ----------------
else:
    st.markdown("<div class='main'>", unsafe_allow_html=True)
    st.title("🚀 Internship Recommendation System")

    # Load dataset
    df = pd.read_csv("adzuna_internships_raw.csv")
    df.columns = df.columns.str.lower()
    df["description"] = df["description"].fillna("")

    # Search inputs
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    skill = st.text_input("🔍 Skill (Python, Data, Web, ML)")
    location = st.selectbox(
        "📍 Location",
        sorted(df["location"].dropna().unique())
    )

    resume = st.file_uploader("📄 Upload Resume (PDF)", type="pdf")
    user_skills = extract_skills_from_resume(resume) if resume else []

    if user_skills:
        st.success(f"Detected Skills: {', '.join(user_skills)}")

    search = st.button("Search Internships 🚀")
    st.markdown("</div>", unsafe_allow_html=True)

    # ---------------- SEARCH RESULTS ----------------
    if search:
        log_search(st.session_state.user, skill, location)

        results = []
        for _, row in df.iterrows():
            job_skills = row["description"].lower().split()
            score = compute_match_score(
                job_skills,
                user_skills,
                row.get("stipend", 15000)
            )

            if skill.lower() in row["title"].lower() and location.lower() in row["location"].lower():
                results.append((score, row))

        results = sorted(results, key=lambda x: x[0], reverse=True)[:10]

        if not results:
            st.warning("No matching internships found")
        else:
            for score, job in results:
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.markdown(f"""
                ### {job['title']}
                🏢 **{job['company']}**  
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

                st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
