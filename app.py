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

# ================= SESSION =================
for k, v in {
    "user": None,
    "role": None,
    "page": "search",
    "dark": False
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ================= SIDEBAR =================
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    st.session_state.dark = st.toggle("🌙 Dark Mode")

    if st.session_state.user:
        st.success(f"👤 {st.session_state.user}")
        st.divider()
        st.button("🔍 Search", on_click=lambda: st.session_state.update(page="search"))
        st.button("📌 Applied", on_click=lambda: st.session_state.update(page="applied"))
        if st.session_state.role == "Admin":
            st.button("📊 Admin", on_click=lambda: st.session_state.update(page="admin"))
        if st.button("🚪 Logout"):
            st.session_state.user = None
            st.session_state.role = None
            st.session_state.page = "search"
            st.rerun()

# ================= DATABASE =================
def db():
    return psycopg2.connect(
        host=st.secrets["db"]["host"],
        database=st.secrets["db"]["name"],
        user=st.secrets["db"]["user"],
        password=st.secrets["db"]["password"],
        port=st.secrets["db"]["port"],
        sslmode="require"  
    )


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

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    cur.execute(
        "INSERT INTO users (username,email,password,role) VALUES (%s,%s,%s,%s)",
        (username, email, hashed, role)
    )
    conn.commit()
    conn.close()
    return True, "✅ Registration successful"

def reset_password(username, new_password):
    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM users WHERE username=%s", (username,))
    if not cur.fetchone():
        conn.close()
        return False, "❌ User not found"

    hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())
    cur.execute(
        "UPDATE users SET password=%s WHERE username=%s",
        (hashed, username)
    )
    conn.commit()
    conn.close()
    return True, "✅ Password updated"

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

    # 🔥 CRITICAL FIX (memoryview → bytes)
    stored_password = bytes(row[0])

    if bcrypt.checkpw(password.encode(), stored_password):
        return row[1]

    return None

# ================= ML DEMAND MODEL =================
def build_features(df):
    df = df.copy()
    df["stipend"] = df.get("stipend", 15000).fillna(15000)
    df["skill_count"] = df["description"].apply(lambda x: len(set(x.split())))
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
    preds = model.predict(X)
    acc = r2_score(y, preds) * 100
    return model, round(acc, 2)

# ================= SKILL TREND =================
def extract_skills(text):
    skills = ["python","java","sql","ml","data","web","cloud","react"]
    return [s for s in skills if s in text.lower()]

# ================= LOGIN / REGISTER =================
if not st.session_state.user:
    st.title("🎓 Internship Demand Portal")

    tab1, tab2, tab3 = st.tabs(["Login", "Register", "Forgot Password"])

    with tab1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            role = validate_login(u, p)
            if role:
                st.session_state.user = u
                st.session_state.role = role
                st.rerun()
            else:
                st.error("❌ Invalid username or password")

    with tab2:
        u = st.text_input("New Username")
        e = st.text_input("Email")
        p = st.text_input("Password", type="password")
        role = st.selectbox("Role", ["Student", "Admin"])
        if st.button("Register"):
            ok, msg = register_user(u, e, p, role)
            st.success(msg) if ok else st.error(msg)

    with tab3:
        u = st.text_input("Username")
        npw = st.text_input("New Password", type="password")
        if st.button("Reset Password"):
            ok, msg = reset_password(u, npw)
            st.success(msg) if ok else st.error(msg)

# ================= STUDENT =================
elif st.session_state.role == "Student":
    df = pd.read_csv("adzuna_internships_raw.csv")
    df.columns = df.columns.str.lower()
    df["description"] = df["description"].fillna("")
    df = build_features(df)
    model, acc = train_model(df)

    st.info(f"📈 ML Demand Model Accuracy: **{acc}%**")

    if st.session_state.page == "search":
        skill = st.text_input("Skill")
        location = st.selectbox("Location", sorted(df["location"].dropna().unique()))

        if st.button("Search"):
            df["score"] = model.predict(
                df[["stipend", "skill_count", "company_score", "is_remote"]]
            )
            res = df[
                df["title"].str.contains(skill, case=False, na=False)
            ].sort_values("score", ascending=False).head(10)

            for _, j in res.iterrows():
                st.markdown(
                    f"### {j['title']}  \n🏢 {j['company']}  \n📍 {j['location']}"
                )

# ================= ADMIN =================
elif st.session_state.role == "Admin":
    st.title("📊 Skill Demand Trends")

    df = pd.read_csv("adzuna_internships_raw.csv")
    df["description"] = df["description"].fillna("")
    skills = df["description"].apply(extract_skills).explode().value_counts()

    st.bar_chart(skills)
