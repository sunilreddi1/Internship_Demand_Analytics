import streamlit as st
import sqlite3
import pandas as pd
import os

# ---------------- AUTO DB INIT ----------------
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

# ---------------- SESSION ----------------
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    st.session_state.dark_mode = st.toggle("🌙 Dark Mode")

# ---------------- UI COLORS & BACKGROUNDS ----------------
bg_light = "https://images.unsplash.com/photo-1521737604893-d14cc237f11d"
bg_dark  = "https://images.unsplash.com/photo-1518770660439-4636190af475"

bg = bg_dark if st.session_state.dark_mode else bg_light
card_bg = "rgba(30,41,59,0.95)" if st.session_state.dark_mode else "rgba(255,255,255,0.95)"
text_color = "#e5e7eb" if st.session_state.dark_mode else "#1f2937"
accent = "#0a66c2"

st.markdown(f"""
<style>
[data-testid="stAppViewContainer"] {{
    background-image: url("{bg}");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}}

.main {{
    background-color: rgba(0,0,0,0.15);
    padding: 2rem;
    border-radius: 18px;
}}

h1,h2,h3 {{
    color: {accent};
    font-weight: 800;
}}

p,span,label,div {{
    color: {text_color};
}}

.card {{
    background: {card_bg};
    padding: 22px;
    border-radius: 18px;
    margin-bottom: 20px;
    box-shadow: 0 15px 35px rgba(0,0,0,0.25);
    animation: fadeIn 0.6s ease;
}}

.card:hover {{
    transform: translateY(-6px);
}}

.badge {{
    display:inline-block;
    background:#e0f2fe;
    color:#0369a1;
    padding:6px 10px;
    border-radius:999px;
    font-size:12px;
    margin-right:6px;
    font-weight:600;
}}

button {{
    background: linear-gradient(90deg,#0a66c2,#003a75) !important;
    color:white !important;
    border-radius:10px !important;
    font-weight:600 !important;
}}

@keyframes fadeIn {{
    from {{opacity:0; transform:translateY(15px);}}
    to {{opacity:1; transform:translateY(0);}}
}}
</style>
""", unsafe_allow_html=True)

# ---------------- DATABASE ----------------
def db():
    return sqlite3.connect("users.db", check_same_thread=False)

# ---------------- AUTH HELPERS ----------------
def user_exists(username):
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE username=?", (username,))
    exists = cur.fetchone() is not None
    conn.close()
    return exists

def validate_login(username, password):
    conn = db()
    cur = conn.cursor()
    cur.execute(
        "SELECT role FROM users WHERE username=? AND password=?",
        (username, password)
    )
    row = cur.fetchone()
    conn.close()
    return row

# ---------------- LOGIN / REGISTER ----------------
if not st.session_state.user:
    st.markdown("<div class='main'>", unsafe_allow_html=True)
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    st.title("🎓 Internship Portal")
    mode = st.radio("Choose action", ["Login", "Register"])

    username = st.text_input("👤 Username")
    password = st.text_input("🔒 Password", type="password")
    role = st.selectbox("Role", ["Student", "Admin"])

    if st.button(mode):
        if not username or not password:
            st.error("All fields are required")
        elif mode == "Register":
            if user_exists(username):
                st.error("❌ Username already exists")
            else:
                conn = db()
                conn.execute(
                    "INSERT INTO users (username,password,role) VALUES (?,?,?)",
                    (username,password,role)
                )
                conn.commit()
                conn.close()
                st.success("✅ Registration successful! Please login.")
        else:
            result = validate_login(username, password)
            if result:
                st.session_state.user = username
                st.session_state.role = result[0]
                st.success("Login successful 🎉")
                st.rerun()
            else:
                st.error("❌ Invalid username or password")

    st.markdown("</div></div>", unsafe_allow_html=True)

# ---------------- ADMIN ----------------
elif st.session_state.role == "Admin":
    st.markdown("<div class='main'>", unsafe_allow_html=True)
    show_admin_dashboard()
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- STUDENT ----------------
else:
    st.markdown("<div class='main'>", unsafe_allow_html=True)
    st.title("🚀 Internship Recommendations")

    df = pd.read_csv("adzuna_internships_raw.csv")
    df.columns = df.columns.str.lower()
    df["description"] = df["description"].fillna("")

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    skill = st.text_input("🔍 Skill")
    location = st.selectbox("📍 Location", sorted(df["location"].dropna().unique()))

    resume = st.file_uploader("📄 Upload Resume", type="pdf")
    user_skills = extract_skills_from_resume(resume) if resume else []

    if user_skills:
        for s in user_skills:
            st.markdown(f"<span class='badge'>🧠 {s}</span>", unsafe_allow_html=True)

    if st.button("🔎 Search Internships"):
        results = []
        for _, row in df.iterrows():
            score = compute_match_score(
                row["description"].lower().split(),
                user_skills,
                row.get("stipend",15000)
            )
            if skill.lower() in row["title"].lower() and location.lower() in row["location"].lower():
                results.append((score,row))

        results = sorted(results, key=lambda x:x[0], reverse=True)[:10]

        for score, job in results:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown(f"""
            ### {job['title']}
            🏢 **{job['company']}**  
            📍 {job['location']}  
            <span class='badge'>🎯 {score}% Match</span>
            """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
