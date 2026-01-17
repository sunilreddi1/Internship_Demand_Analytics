import streamlit as st
import sqlite3
import pandas as pd
import os
import matplotlib.pyplot as plt

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
if "page" not in st.session_state:
    st.session_state.page = "search"

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    st.session_state.dark_mode = st.toggle("🌙 Dark Mode")

    if st.session_state.user:
        st.divider()
        if st.session_state.role == "Student":
            st.button("🔍 Search Internships", on_click=lambda: st.session_state.update(page="search"))
            st.button("📌 Applied Internships", on_click=lambda: st.session_state.update(page="applied"))
        if st.session_state.role == "Admin":
            st.button("📊 Admin Analytics", on_click=lambda: st.session_state.update(page="admin"))
        st.divider()
        if st.button("🚪 Logout"):
            st.session_state.user = None
            st.session_state.role = None
            st.session_state.page = "search"
            st.rerun()

# ---------------- UI COLORS & BACKGROUNDS ----------------
bg_light = "https://images.unsplash.com/photo-1522202176988-66273c2fd55f"
bg_dark  = "https://images.unsplash.com/photo-1519389950473-47ba0277781c"

bg = bg_dark if st.session_state.dark_mode else bg_light
card_bg = "rgba(30,41,59,0.95)" if st.session_state.dark_mode else "rgba(255,255,255,0.94)"
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
    background: linear-gradient(rgba(0,0,0,0.35), rgba(0,0,0,0.35));
    padding: 2.5rem;
    border-radius: 18px;
}}

h1,h2,h3 {{ color: {accent}; font-weight: 800; }}
p,span,label,div {{ color: {text_color}; }}

.card {{
    background: {card_bg};
    padding: 22px;
    border-radius: 18px;
    margin-bottom: 20px;
    box-shadow: 0 15px 35px rgba(0,0,0,0.25);
    animation: fadeIn 0.6s ease;
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
    ok = cur.fetchone() is not None
    conn.close()
    return ok

def validate_login(username, password):
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT role FROM users WHERE username=? AND password=?", (username,password))
    row = cur.fetchone()
    conn.close()
    return row

# ---------------- LOGIN / REGISTER ----------------
if not st.session_state.user:
    st.markdown("<div class='main'><div class='card'>", unsafe_allow_html=True)
    st.title("🎓 Internship Portal")

    mode = st.radio("Choose action", ["Login", "Register"])
    u = st.text_input("👤 Username")
    p = st.text_input("🔒 Password", type="password")
    role = st.selectbox("Role", ["Student","Admin"])

    if st.button(mode):
        if not u or not p:
            st.error("All fields required")
        elif mode == "Register":
            if user_exists(u):
                st.error("Username already exists")
            else:
                conn = db()
                conn.execute("INSERT INTO users VALUES (?,?,?)",(u,p,role))
                conn.commit(); conn.close()
                st.success("Registered successfully")
        else:
            r = validate_login(u,p)
            if r:
                st.session_state.user = u
                st.session_state.role = r[0]
                st.rerun()
            else:
                st.error("Invalid credentials")
    st.markdown("</div></div>", unsafe_allow_html=True)

# ========================= STUDENT =========================
elif st.session_state.role == "Student":

    df = pd.read_csv("adzuna_internships_raw.csv")
    df.columns = df.columns.str.lower()
    df["description"] = df["description"].fillna("")

    logo_col = "company_logo" if "company_logo" in df.columns else None

    # -------- SEARCH PAGE --------
    if st.session_state.page == "search":
        st.markdown("<div class='main'>", unsafe_allow_html=True)
        st.title("🚀 Internship Recommendations")

        st.markdown("<div class='card'>", unsafe_allow_html=True)
        skill = st.text_input("🔍 Skill")
        location = st.selectbox("📍 Location", sorted(df["location"].dropna().unique()))
        resume = st.file_uploader("📄 Upload Resume", type="pdf")
        user_skills = extract_skills_from_resume(resume) if resume else []

        for s in user_skills:
            st.markdown(f"<span class='badge'>🧠 {s}</span>", unsafe_allow_html=True)

        if st.button("Search"):
            results=[]
            for _,row in df.iterrows():
                score = compute_match_score(row["description"].split(), user_skills, row.get("stipend",15000))
                if skill.lower() in row["title"].lower() and location.lower() in row["location"].lower():
                    results.append((score,row))

            for score,job in sorted(results,reverse=True)[:10]:
                st.markdown("<div class='card'>", unsafe_allow_html=True)

                if logo_col and pd.notna(job[logo_col]):
                    st.image(job[logo_col], width=80)

                st.markdown(f"""
                ### {job['title']}
                🏢 **{job['company']}**  
                📍 {job['location']}  
                <span class='badge'>🎯 {score}% Match</span>
                """, unsafe_allow_html=True)

                if st.button(f"Apply – {job['title']}", key=f"a_{job['title']}"):
                    conn=db()
                    conn.execute(
                        "INSERT INTO applications VALUES (?,?,?,?)",
                        (st.session_state.user, job["title"], job["company"], "Pending")
                    )
                    conn.commit(); conn.close()
                    st.success("Applied successfully")

                st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # -------- APPLIED PAGE --------
    elif st.session_state.page == "applied":
        st.markdown("<div class='main'>", unsafe_allow_html=True)
        st.title("📌 Applied Internships")

        conn=db()
        apps=pd.read_sql(
            "SELECT * FROM applications WHERE username=?",
            conn, params=(st.session_state.user,)
        )
        conn.close()

        if apps.empty:
            st.info("No applications yet")
        else:
            for _,a in apps.iterrows():
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.markdown(f"""
                ### {a['job_id']}
                🏢 **{a['company']}**  
                <span class='badge'>📌 {a['status']}</span>
                """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ========================= ADMIN =========================
elif st.session_state.role == "Admin":
    st.markdown("<div class='main'>", unsafe_allow_html=True)
    st.title("📊 Admin Analytics")

    conn=db()
    apps=pd.read_sql("SELECT * FROM applications",conn)
    conn.close()

    if not apps.empty:
        st.subheader("Applications by Company")
        st.bar_chart(apps["company"].value_counts())

        st.subheader("Application Status")
        st.bar_chart(apps["status"].value_counts())
    else:
        st.info("No application data yet")

    st.markdown("</div>", unsafe_allow_html=True)
