import streamlit as st
import pandas as pd
import psycopg2
import bcrypt
import numpy as np
from sklearn.linear_model import LinearRegression

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Internship Demand & Recommendation Portal",
    page_icon="🎓",
    layout="wide"
)

# ================= SESSION =================
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None
if "page" not in st.session_state:
    st.session_state.page = "search"
if "dark" not in st.session_state:
    st.session_state.dark = False

# ================= SIDEBAR =================
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    st.session_state.dark = st.toggle("🌙 Dark Mode")

    if st.session_state.user:
        st.success(f"👤 {st.session_state.user}")
        st.divider()
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

# ================= DATABASE =================
def db():
    return psycopg2.connect(
        host=st.secrets["db"]["host"],
        database=st.secrets["db"]["name"],
        user=st.secrets["db"]["user"],
        password=st.secrets["db"]["password"],
        port=st.secrets["db"]["port"]
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
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    conn = db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (username,email,password,role) VALUES (%s,%s,%s,%s)",
        (username, email, hashed, role)
    )
    conn.commit()
    conn.close()

def validate_login(username, password):
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT password, role FROM users WHERE username=%s", (username,))
    row = cur.fetchone()
    conn.close()
    if row and bcrypt.checkpw(password.encode(), row[0]):
        return row[1]
    return None

# ================= ML DEMAND MODEL =================
def build_features(df):
    df = df.copy()
    df["stipend"] = df.get("stipend", 15000).fillna(15000)
    df["skill_count"] = df["description"].apply(lambda x: len(set(x.lower().split())))
    df["is_remote"] = df["location"].str.contains("remote", case=False, na=False).astype(int)
    df["company_score"] = df["company"].map(df["company"].value_counts()).fillna(1)

    # Synthetic demand score (regression target)
    df["demand"] = (
        0.4 * df["stipend"] +
        10 * df["skill_count"] +
        500 * df["company_score"] +
        300 * df["is_remote"]
    )
    return df

@st.cache_resource
def train_demand_model(df):
    X = df[["stipend", "skill_count", "company_score", "is_remote"]]
    y = df["demand"]
    model = LinearRegression()
    model.fit(X, y)
    return model

def compute_match(job, skill, location, model, max_demand):
    skill_score = 1 if skill.lower() in job["description"].lower() else 0
    location_score = 1 if location.lower() in job["location"].lower() else 0.5

    features = pd.DataFrame([{
        "stipend": job["stipend"],
        "skill_count": job["skill_count"],
        "company_score": job["company_score"],
        "is_remote": job["is_remote"]
    }])

    demand_score = model.predict(features)[0]

    final = (
        0.4 * skill_score +
        0.3 * location_score +
        0.3 * (demand_score / max_demand)
    ) * 100

    return round(final, 2)

# ================= LOGIN =================
if not st.session_state.user:
    st.title("🎓 Internship Demand Portal")

    mode = st.radio("Action", ["Login", "Register"])
    u = st.text_input("Username")
    e = st.text_input("Email")
    p = st.text_input("Password", type="password")
    role = st.selectbox("Role", ["Student", "Admin"])

    if st.button(mode):
        if mode == "Register":
            register_user(u, e, p, role)
            st.success("Registered successfully")
        else:
            r = validate_login(u, p)
            if r:
                st.session_state.user = u
                st.session_state.role = r
                st.rerun()
            else:
                st.error("Invalid credentials")

# ================= STUDENT =================
elif st.session_state.role == "Student":

    df = pd.read_csv("adzuna_internships_raw.csv")
    df.columns = df.columns.str.lower()
    df["description"] = df["description"].fillna("")

    df = build_features(df)
    model = train_demand_model(df)
    MAX_DEMAND = df["demand"].max()

    if st.session_state.page == "search":
        st.title("🚀 Internship Recommendations")
        skill = st.text_input("Skill")
        location = st.selectbox("Location", sorted(df["location"].dropna().unique()))

        if st.button("Search"):
            ranked = []
            for _, job in df.iterrows():
                if skill.lower() in job["description"].lower():
                    score = compute_match(job, skill, location, model, MAX_DEMAND)
                    ranked.append((score, job))

            for score, job in sorted(ranked, reverse=True)[:10]:
                st.subheader(job["title"])
                st.write(f"🏢 {job['company']} | 📍 {job['location']}")
                st.progress(int(score))
                st.caption(f"Match Score: {score}%")

    elif st.session_state.page == "applied":
        st.title("📌 Applied Internships")
        conn = db()
        apps = pd.read_sql(
            "SELECT * FROM applications WHERE username=%s",
            conn,
            params=(st.session_state.user,)
        )
        conn.close()
        st.dataframe(apps)

# ================= ADMIN =================
elif st.session_state.role == "Admin":
    st.title("📊 Admin Analytics")

    df = pd.read_csv("adzuna_internships_raw.csv")
    df.columns = df.columns.str.lower()
    df["description"] = df["description"].fillna("")
    df = build_features(df)

    # 🔹 Skill-demand trend
    st.subheader("🔥 Skill Demand Trend")
    skill_demand = (
        df.assign(skill=df["description"].str.lower().str.split())
        .explode("skill")
        .groupby("skill")["demand"]
        .mean()
        .sort_values(ascending=False)
        .head(15)
    )
    st.bar_chart(skill_demand)

    # 🔹 Demand vs skill count
    st.subheader("📈 Demand vs Skill Count")
    st.line_chart(df.sort_values("skill_count")[["skill_count", "demand"]])

    # 🔹 Applications by company
    conn = db()
    apps = pd.read_sql(
        "SELECT company, COUNT(*) cnt FROM applications GROUP BY company",
        conn
    )
    conn.close()
    st.subheader("🏢 Company-wise Applications")
    st.bar_chart(apps.set_index("company"))
