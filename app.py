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

# ---------------- DARK MODE TOGGLE ----------------
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

with st.sidebar:
    st.markdown("## ⚙️ Settings")
    st.session_state.dark_mode = st.toggle("🌙 Dark Mode")

# ---------------- UI STYLES ----------------
bg_light = "https://images.unsplash.com/photo-1498050108023-c5249f4df085"
bg_dark = "https://images.unsplash.com/photo-1518770660439-4636190af475"

bg = bg_dark if st.session_state.dark_mode else bg_light
card_bg = "rgba(30,41,59,0.95)" if st.session_state.dark_mode else "rgba(255,255,255,0.97)"
text_color = "#e5e7eb" if st.session_state.dark_mode else "#1f2937"
accent = "#0a66c2"

st.markdown(f"""
<style>

/* ===== BACKGROUND ===== */
[data-testid="stAppViewContainer"] {{
    background-image: url("{bg}");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}}

/* ===== MAIN ===== */
.main {{
    background-color: rgba(0,0,0,0.15);
    padding: 2rem;
    border-radius: 18px;
}}

/* ===== HEADINGS ===== */
h1,h2,h3 {{
    color: {accent};
    font-weight: 800;
}}

/* ===== TEXT ===== */
p,span,label,div {{
    color: {text_color};
}}

/* ===== CARD ===== */
.card {{
    background: {card_bg};
    padding: 22px;
    border-radius: 18px;
    margin-bottom: 20px;
    box-shadow: 0 15px 35px rgba(0,0,0,0.25);
    animation: fadeIn 0.6s ease;
    transition: transform 0.3s ease;
}}
.card:hover {{
    transform: translateY(-6px);
}}

/* ===== BADGES ===== */
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

/* ===== BUTTON ===== */
button {{
    background: linear-gradient(90deg,#0a66c2,#003a75) !important;
    color:white !important;
    border-radius:10px !important;
    font-weight:600 !important;
}}

/* ===== ANIMATION ===== */
@keyframes fadeIn {{
    from {{opacity:0; transform:translateY(15px);}}
    to {{opacity:1; transform:translateY(0);}}
}}

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

# ---------------- LOGIN ----------------
if not st.session_state.user:
    st.markdown("<div class='main'>", unsafe_allow_html=True)
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    st.title("🎓 Internship Portal")
    st.caption("Internshala-style smart internship recommendations")

    username = st.text_input("👤 Username")
    password = st.text_input("🔒 Password", type="password")
    role = st.selectbox("Role", ["Student", "Admin"])

    if st.button("Login / Register"):
        if username and password:
            conn = db()
            conn.execute(
                "INSERT OR IGNORE INTO users (username,password,role) VALUES (?,?,?)",
                (username,password,role)
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
    skill = st.text_input("🔍 Skill (Python, Data, Web, ML)")
    location = st.selectbox("📍 Location", sorted(df["location"].dropna().unique()))

    resume = st.file_uploader("📄 Upload Resume", type="pdf")
    user_skills = extract_skills_from_resume(resume) if resume else []

    if user_skills:
        for s in user_skills:
            st.markdown(f"<span class='badge'>🧠 {s}</span>", unsafe_allow_html=True)

    search = st.button("🔎 Search Internships")
    st.markdown("</div>", unsafe_allow_html=True)

    if search:
        log_search(st.session_state.user, skill, location)

        results = []
        for _, row in df.iterrows():
            job_skills = row["description"].lower().split()
            score = compute_match_score(job_skills, user_skills, row.get("stipend",15000))
            if skill.lower() in row["title"].lower() and location.lower() in row["location"].lower():
                results.append((score,row))

        results = sorted(results, key=lambda x:x[0], reverse=True)[:10]

        if not results:
            st.warning("No internships found")
        else:
            for score, job in results:
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.markdown(f"""
                ### {job['title']}
                🏢 **{job['company']}**  
                📍 {job['location']}  
                <span class='badge'>💰 ₹{job.get('stipend',15000)}</span>
                <span class='badge'>🎯 {score}% Match</span>
                """, unsafe_allow_html=True)

                if st.button(f"Apply – {job['title']}", key=job['title']):
                    conn = db()
                    conn.execute(
                        "INSERT INTO applications (username,job_id,status) VALUES (?,?,?)",
                        (st.session_state.user,job['title'],"Pending")
                    )
                    conn.commit()
                    conn.close()
                    st.success("Application submitted 🎉")

                st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
