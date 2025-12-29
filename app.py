import streamlit as st
import sqlite3
import random
import time
from PyPDF2 import PdfReader
import pandas as pd

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Internship Portal",
    page_icon="🎓",
    layout="wide"
)

# ================= DATABASE =================
def get_db():
    return sqlite3.connect("users.db", check_same_thread=False)

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        email TEXT,
        verified INTEGER,
        role TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS search_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        skill TEXT,
        location TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ================= SESSION =================
if "page" not in st.session_state:
    st.session_state.page = "login"
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = "Student"
if "otp" not in st.session_state:
    st.session_state.otp = None
if "pending_email" not in st.session_state:
    st.session_state.pending_email = None
if "dark" not in st.session_state:
    st.session_state.dark = False

# ================= THEME =================
def apply_theme():
    if st.session_state.dark:
        bg = "#0f172a"
        card = "#1e293b"
        text = "#ffffff"
    else:
        bg = "linear-gradient(135deg,#f5f7fa,#e0c3fc,#8ec5fc)"
        card = "#ffffff"
        text = "#111827"

    st.markdown(f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background: {bg};
        color: {text};
    }}
    .header {{
        background: linear-gradient(90deg,#0a66c2,#6a11cb,#ff6a88);
        padding: 30px;
        border-radius: 20px;
        color: white;
        margin-bottom: 20px;
    }}
    .card {{
        background: {card};
        padding: 22px;
        border-radius: 18px;
        box-shadow: 0 15px 35px rgba(0,0,0,0.15);
        margin-bottom: 20px;
    }}
    </style>
    """, unsafe_allow_html=True)

apply_theme()

# ================= HELPERS =================
def go(page):
    st.session_state.page = page
    st.rerun()

def send_otp(email):
    otp = random.randint(100000, 999999)
    st.session_state.otp = otp
    st.session_state.pending_email = email
    st.info(f"📧 Verification email sent to {email} (OTP: {otp})")

# ================= AUTH FUNCTIONS =================
def register_user(username, password, email, role):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE username=?", (username,))
    if cur.fetchone():
        conn.close()
        return False

    cur.execute(
        "INSERT INTO users VALUES (?,?,?,?,?)",
        (username, password, email, 0, role)
    )
    conn.commit()
    conn.close()
    send_otp(email)
    return True

def verify_user(otp_entered):
    if st.session_state.otp == otp_entered:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET verified=1 WHERE email=?",
            (st.session_state.pending_email,)
        )
        conn.commit()
        conn.close()
        return True
    return False

def login_user(username, password):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT role, verified FROM users WHERE username=? AND password=?",
        (username, password)
    )
    row = cur.fetchone()
    conn.close()
    return row

# ================= SIDEBAR =================
with st.sidebar:
    st.markdown("## 🎓 Internship Portal")
    st.toggle("🌙 Dark Mode", key="dark")
    if st.session_state.user:
        st.success(f"👤 {st.session_state.user}")
        st.info(f"Role: {st.session_state.role}")
        if st.button("🚪 Logout"):
            st.session_state.user = None
            go("login")

# ================= LOGIN / REGISTER =================
if st.session_state.page == "login":
    st.markdown("<div class='header'><h1>Welcome</h1><p>Login or Register</p></div>", unsafe_allow_html=True)

    choice = st.radio("Choose", ["Login", "Register"])

    if choice == "Register":
        with st.container():
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            e = st.text_input("Email")
            r = st.selectbox("Role", ["Student", "Admin"])

            if st.button("Register"):
                if register_user(u, p, e, r):
                    st.success("Registered! Verify your email.")
                    go("verify")
                else:
                    st.error("Username already exists")
            st.markdown("</div>", unsafe_allow_html=True)

    else:
        with st.container():
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")

            if st.button("Login"):
                res = login_user(u, p)
                if res:
                    role, verified = res
                    if not verified:
                        st.error("Email not verified")
                    else:
                        st.session_state.user = u
                        st.session_state.role = role
                        go("dashboard")
                else:
                    st.error("Invalid credentials")
            st.markdown("</div>", unsafe_allow_html=True)

# ================= EMAIL VERIFICATION =================
elif st.session_state.page == "verify":
    st.markdown("<div class='header'><h2>Email Verification</h2></div>", unsafe_allow_html=True)
    otp = st.text_input("Enter OTP", type="password")
    if st.button("Verify"):
        if verify_user(int(otp)):
            st.success("Email verified! Login now.")
            go("login")
        else:
            st.error("Invalid OTP")

# ================= DASHBOARD =================
elif st.session_state.page == "dashboard":
    st.markdown("<div class='header'><h2>Internship Dashboard</h2></div>", unsafe_allow_html=True)

    skill = st.text_input("Skill (Python, Data, Web)")
    location = st.text_input("Location", "India")

    resume = st.file_uploader("Upload Resume (PDF)", type="pdf")
    skills = []
    if resume:
        reader = PdfReader(resume)
        text = " ".join([p.extract_text() or "" for p in reader.pages]).lower()
        for s in ["python","data","ml","web","sql","java"]:
            if s in text:
                skills.append(s)
        st.success(f"Extracted Skills: {', '.join(skills)}")

    if st.button("🔍 Search Internships"):
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO search_logs (username, skill, location) VALUES (?,?,?)",
            (st.session_state.user, skill, location)
        )
        conn.commit()
        conn.close()
        go("results")

# ================= RESULTS =================
elif st.session_state.page == "results":
    st.markdown("<div class='header'><h2>Recommended Internships</h2></div>", unsafe_allow_html=True)

    internships = [
        {"title":"Python Intern","company":"TechCorp","stipend":20000},
        {"title":"Data Analyst Intern","company":"DataWorks","stipend":18000},
        {"title":"Web Developer Intern","company":"WebSolutions","stipend":15000},
    ]

    for job in internships:
        job["score"] = job["stipend"]/1000 + len(job["title"])

    internships = sorted(internships, key=lambda x: x["score"], reverse=True)

    for job in internships:
        st.markdown(f"""
        <div class='card'>
        <h3>{job['title']}</h3>
        <p>🏢 {job['company']}</p>
        <p>💰 ₹{job['stipend']}</p>
        <p>🎯 Match Score: {int(job['score'])}%</p>
        </div>
        """, unsafe_allow_html=True)

    if st.button("⬅ Back"):
        go("dashboard")

# ================= ADMIN DASHBOARD =================
if st.session_state.user and st.session_state.role == "Admin":
    st.markdown("<div class='header'><h2>Admin Analytics</h2></div>", unsafe_allow_html=True)
    conn = get_db()
    df = pd.read_sql("SELECT skill, COUNT(*) as count FROM search_logs GROUP BY skill", conn)
    conn.close()
    if not df.empty:
        st.bar_chart(df.set_index("skill"))
