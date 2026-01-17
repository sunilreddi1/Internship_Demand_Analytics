import streamlit as st
import sqlite3
import pandas as pd
import os
import bcrypt
import random
import psycopg2

# =====================================================
# DATABASE (POSTGRESQL OR SQLITE FALLBACK)
# =====================================================
def get_db():
    db_url = os.getenv("DATABASE_URL")  # for Streamlit Cloud
    if db_url:
        return psycopg2.connect(db_url)
    return sqlite3.connect("users.db", check_same_thread=False)

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config("Internship Demand Portal", "🎓", layout="wide")

# =====================================================
# SESSION
# =====================================================
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None
if "otp" not in st.session_state:
    st.session_state.otp = None
if "otp_verified" not in st.session_state:
    st.session_state.otp_verified = False

# =====================================================
# UI
# =====================================================
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background-image: url("https://images.unsplash.com/photo-1521737604893-d14cc237f11d");
    background-size: cover;
}
.card {
    background: rgba(255,255,255,0.95);
    padding: 22px;
    border-radius: 16px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.25);
}
button {
    background: linear-gradient(90deg,#0a66c2,#003a75) !important;
    color: white !important;
    font-weight: 600 !important;
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# HELPERS
# =====================================================
def hash_password(pw):
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def check_password(pw, hashed):
    return bcrypt.checkpw(pw.encode(), hashed.encode())

def generate_otp():
    return str(random.randint(100000, 999999))

# =====================================================
# LOGIN / REGISTER
# =====================================================
if not st.session_state.user:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.title("🎓 Internship Portal")

    mode = st.radio("Choose", ["Login", "Register"])
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    email = st.text_input("Email (for OTP)")

    conn = get_db()
    cur = conn.cursor()

    if mode == "Register":
        if st.button("Register"):
            if not username or not password or not email:
                st.error("All fields required")
            else:
                cur.execute("SELECT 1 FROM users WHERE username=%s" if "psycopg2" in str(type(conn))
                            else "SELECT 1 FROM users WHERE username=?", (username,))
                if cur.fetchone():
                    st.error("Username already exists")
                else:
                    st.session_state.otp = generate_otp()
                    st.info(f"OTP Generated (demo): {st.session_state.otp}")
                    st.session_state.pending_user = (username, password, email)

    if st.session_state.otp:
        otp_input = st.text_input("Enter OTP")
        if st.button("Verify OTP"):
            if otp_input == st.session_state.otp:
                u, p, e = st.session_state.pending_user
                hashed = hash_password(p)
                cur.execute(
                    "INSERT INTO users (username,password,role,email) VALUES (%s,%s,%s,%s)"
                    if "psycopg2" in str(type(conn))
                    else "INSERT INTO users VALUES (?,?,?,?)",
                    (u, hashed, "Student", e)
                )
                conn.commit()
                st.success("Registration successful! Please login.")
                st.session_state.otp = None
            else:
                st.error("Invalid OTP")

    if mode == "Login":
        if st.button("Login"):
            cur.execute(
                "SELECT password,role FROM users WHERE username=%s"
                if "psycopg2" in str(type(conn))
                else "SELECT password,role FROM users WHERE username=?",
                (username,)
            )
            row = cur.fetchone()
            if row and check_password(password, row[0]):
                st.session_state.user = username
                st.session_state.role = row[1]
                st.success("Login successful 🎉")
                st.rerun()
            else:
                st.error("Invalid credentials")

    conn.close()
    st.markdown("</div>", unsafe_allow_html=True)

# =====================================================
# DASHBOARD
# =====================================================
else:
    st.success(f"Welcome {st.session_state.user}")
    st.info("Now you have: ✔ bcrypt ✔ OTP ✔ PostgreSQL-ready DB")
