import streamlit as st
import sqlite3
import random
from PyPDF2 import PdfReader
import pandas as pd

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Internship Portal",
    page_icon="🎓",
    layout="wide"
)

# ---------------- DATABASE ----------------
def get_db():
    return sqlite3.connect("users.db", check_same_thread=False)

def init_db():
    conn = get_db()
    cur = conn.cursor()

    # Drop old table if exists (FIXES COLUMN ISSUE)
    cur.execute("DROP TABLE IF EXISTS users")

    cur.execute("""
    CREATE TABLE users (
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

# Run only once per session
if "db_init" not in st.session_state:
    init_db()
    st.session_state.db_init = True

# ---------------- SESSION ----------------
if "page" not in st.session_state:
    st.session_state.page = "login"
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = "Student"
if "otp" not in st.session_state:
    st.session_state.otp = None

# ---------------- THEME ----------------
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg,#f5f7fa,#e0c3fc,#8ec5fc);
}
.header {
    background: linear-gradient(90deg,#0a66c2,#6a11cb,#ff6a88);
    padding: 30px;
    border-radius: 18px;
    color: white;
    margin-bottom: 20px;
}
.card {
    background: white;
    padding: 22px;
    border-radius: 18px;
    box-shadow: 0 15px 35px rgba(0,0,0,0.15);
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- HELPERS ----------------
def go(page):
    st.session_state.page = page
    st.rerun()

def send_otp():
    otp = random.randint(100000, 999999)
    st.session_state.otp = otp
    st.info(f"📧 OTP sent (Demo): {otp}")

# ---------------- AUTH ----------------
def register_user(u, p, e, r):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT username FROM users WHERE username=?", (u,))
    if cur.fetchone():
        conn.close()
        return False

    cur.execute(
        "INSERT INTO users (username,password,email,verified,role) VALUES (?,?,?,?,?)",
        (u, p, e, 0, r)
    )
    conn.commit()
    conn.close()
    send_otp()
    return True

def verify_user(u):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE users SET verified=1 WHERE username=?", (u,))
    conn.commit()
    conn.close()

def login_user(u, p):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT role, verified FROM users WHERE username=? AND password=?",
        (u, p)
    )
    row = cur.fetchone()
    conn.close()
    return row

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.markdown("## 🎓 Internship Portal")
    if st.session_state.user:
        st.success(f"👤 {st.session_state.user}")
        st.info(f"Role: {st.session_state.role}")
        if st.button("🚪 Logout"):
            st.session_state.user = None
            go("login")

# ---------------- LOGIN / REGISTER ----------------
if st.session_state.page == "login":
    st.markdown("<div class='header'><h1>Welcome</h1></div>", unsafe_allow_html=True)
    choice = st.radio("Select", ["Login", "Register"])

    if choice == "Register":
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        e = st.text_input("Email")
        r = st.selectbox("Role", ["Student", "Admin"])

        if st.button("Register"):
            if register_user(u, p, e, r):
                st.success("Registered! Verify OTP.")
                st.session_state.temp_user = u
                go("verify")
            else:
                st.error("Username already exists")
        st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            res = login_user(u, p)
            if res:
                role, verified = res
                if not verified:
                    st.error("Please verify email")
                else:
                    st.session_state.user = u
                    st.session_state.role = role
                    go("dashboard")
            else:
                st.error("Invalid login")
        st.markdown("</div>", unsafe_allow_html=True)

# ---------------- VERIFY ----------------
elif st.session_state.page == "verify":
    st.markdown("<div class='header'><h2>Email Verification</h2></div>", unsafe_allow_html=True)
    otp = st.text_input("Enter OTP")
    if st.button("Verify"):
        if otp == str(st.session_state.otp):
            verify_user(st.session_state.temp_user)
            st.success("Verified! Login now.")
            go("login")
        else:
            st.error("Wrong OTP")

# ---------------- DASHBOARD ----------------
elif st.session_state.page == "dashboard":
    st.markdown("<div class='header'><h2>Dashboard</h2></div>", unsafe_allow_html=True)

    skill = st.text_input("Skill")
    location = st.text_input("Location", "India")

    resume = st.file_uploader("Upload Resume (PDF)", type="pdf")
    if resume:
        reader = PdfReader(resume)
        text = " ".join([p.extract_text() or "" for p in reader.pages])
        st.success("Resume processed")

    if st.button("Search Internships"):
        go("results")

# ---------------- RESULTS ----------------
elif st.session_state.page == "results":
    st.markdown("<div class='header'><h2>Recommended Internships</h2></div>", unsafe_allow_html=True)

    jobs = [
        ("Python Intern", "TechCorp", 20000),
        ("Data Analyst Intern", "DataWorks", 18000),
        ("Web Intern", "WebSolutions", 15000)
    ]

    for j in jobs:
        st.markdown(f"""
        <div class='card'>
        <h3>{j[0]}</h3>
        <p>🏢 {j[1]}</p>
        <p>💰 ₹{j[2]}</p>
        </div>
        """, unsafe_allow_html=True)

    if st.button("⬅ Back"):
        go("dashboard")

# ---------------- ADMIN ----------------
if st.session_state.user and st.session_state.role == "Admin":
    st.markdown("<div class='header'><h2>Admin Analytics</h2></div>", unsafe_allow_html=True)
    conn = get_db()
    df = pd.read_sql("SELECT skill, COUNT(*) as count FROM search_logs GROUP BY skill", conn)
    conn.close()
    if not df.empty:
        st.bar_chart(df.set_index("skill"))
