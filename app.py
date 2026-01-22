import streamlit as st
import pandas as pd
import psycopg2
import bcrypt
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Internship Demand & Recommendation Portal",
    page_icon="🎓",
    layout="wide"
)

# ================= DATABASE =================
DATABASE_URL = (
    "postgresql://neondb_owner:npg_Oigm2nBb0Jqk"
    "@ep-orange-band-ah7k9fu3-pooler.c-3.us-east-1.aws.neon.tech:5432"
    "/neondb?sslmode=require"
)

def db():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = db()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE,
        email TEXT UNIQUE,
        password BYTEA,
        role TEXT
    );
    CREATE TABLE IF NOT EXISTS applications (
        id SERIAL PRIMARY KEY,
        username TEXT,
        job_title TEXT,
        company TEXT,
        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    conn.close()

init_db()

# ================= SESSION =================
for k, v in {
    "user": None,
    "role": None,
    "page": "search"
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ================= AUTH =================
def register_user(username, email, password, role):
    conn = db()
    cur = conn.cursor()

    cur.execute(
        "SELECT 1 FROM users WHERE username=%s OR email=%s",
        (username, email)
    )
    if cur.fetchone():
        conn.close()
        return False, "❌ Username or Email already exists"

    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    cur.execute(
        "INSERT INTO users (username,email,password,role) VALUES (%s,%s,%s,%s)",
        (username, email, hashed, role)
    )
    conn.commit()
    conn.close()
    return True, "✅ Registration successful"

def validate_login(username, password):
    conn = db()
    cur = conn.cursor()
    cur.execute(
        "SELECT password, role FROM users WHERE username=%s",
        (username,)
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    hashed_pw = bytes(row[0])   # 🔥 FIXES bcrypt memoryview crash
    if bcrypt.checkpw(password.encode("utf-8"), hashed_pw):
        return row[1]

    return None

def reset_password(username, new_password):
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE username=%s", (username,))
    if not cur.fetchone():
        conn.close()
        return False, "❌ User not found"

    hashed = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())
    cur.execute(
        "UPDATE users SET password=%s WHERE username=%s",
        (hashed, username)
    )
    conn.commit()
    conn.close()
    return True, "✅ Password updated"

# ================= ML MODEL =================
def build_features(df):
    df = df.copy()
    df["stipend"] = df.get("stipend", 15000).fillna(15000)
    df["skill_count"] = df["description"].str.split().apply(len)
    df["company_score"] = df["company"].map(df["company"].value_counts())
    df["is_remote"] = df["location"].str.contains("remote", case=False, na=False).astype(int)

    df["demand"] = (
        0.4 * df["stipend"] +
        20 * df["skill_count"] +
        500 * df["company_score"] +
        300 * df["is_remote"]
    )
    return df

@st.cache_resource
def train_model(df):
    X = df[["stipend", "skill_count", "company_score", "is_remote"]]
    y = df["demand"]
    model = LinearRegression()
    model.fit(X, y)
    acc = r2_score(y, model.predict(X)) * 100
    return model, round(acc, 2)

# ================= SKILL TREND =================
def extract_skills(text):
    skills = ["python","java","sql","ml","data","web","cloud","react"]
    return [s for s in skills if s in text.lower()]

# ================= UI =================
if not st.session_state.user:
    st.title("🎓 Internship Demand Portal")
    t1, t2, t3 = st.tabs(["Login", "Register", "Forgot Password"])

    with t1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            role = validate_login(u, p)
            if role:
                st.session_state.user = u
                st.session_state.role = role
                st.rerun()
            else:
                st.error("Invalid credentials")

    with t2:
        u = st.text_input("New Username")
        e = st.text_input("Email")
        p = st.text_input("Password", type="password")
        r = st.selectbox("Role", ["Student", "Admin"])
        if st.button("Register"):
            ok, msg = register_user(u, e, p, r)
            st.success(msg) if ok else st.error(msg)

    with t3:
        u = st.text_input("Username for reset")
        npw = st.text_input("New Password", type="password")
        if st.button("Reset Password"):
            ok, msg = reset_password(u, npw)
            st.success(msg) if ok else st.error(msg)

# ================= STUDENT =================
elif st.session_state.role == "Student":
    df = pd.read_csv("adzuna_internships_raw.csv")
    df["description"] = df["description"].fillna("")
    df = build_features(df)
    model, acc = train_model(df)

    st.success(f"📈 ML Demand Accuracy: **{acc}%**")

    skill = st.text_input("Skill")
    if st.button("Search"):
        df["score"] = model.predict(
            df[["stipend","skill_count","company_score","is_remote"]]
        )
        res = df[df["title"].str.contains(skill, case=False)].sort_values(
            "score", ascending=False
        ).head(10)

        for _, j in res.iterrows():
            st.markdown(
                f"### {j['title']}\n🏢 {j['company']}  \n📍 {j['location']}"
            )

# ================= ADMIN =================
elif st.session_state.role == "Admin":
    st.title("📊 Skill Demand Trends")

    df = pd.read_csv("adzuna_internships_raw.csv")
    df["description"] = df["description"].fillna("")
    skills = df["description"].apply(extract_skills).explode().value_counts()

    st.bar_chart(skills)
