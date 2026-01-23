import streamlit as st
import pandas as pd
import psycopg2
import bcrypt
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import re
import PyPDF2

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
    "resume_skills": []
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ================= THEME =================
st.markdown("""
<style>
body { background:#f8fafc; }
.card {
    background:white;
    padding:24px;
    border-radius:16px;
    box-shadow:0 10px 25px rgba(0,0,0,0.08);
    margin-bottom:22px;
}
.badge {
    background:#e0f2fe;
    color:#0369a1;
    padding:6px 12px;
    border-radius:999px;
    font-size:13px;
}
.title { font-size:22px; font-weight:700; }
.sub { color:#475569; }
button { background:#2563eb!important; color:white!important; }
</style>
""", unsafe_allow_html=True)

# ================= DATABASE =================
def db():
    return psycopg2.connect(st.secrets["db"]["url"])

def init_db():
    conn = db(); cur = conn.cursor()

    # USERS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE,
        email TEXT UNIQUE,
        password BYTEA,
        role TEXT
    );
    """)

    # APPLICATIONS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS applications (
        id SERIAL PRIMARY KEY,
        username TEXT,
        job_title TEXT,
        company TEXT,
        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # ✅ FIX: add location column if missing
    cur.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='applications' AND column_name='location'
        ) THEN
            ALTER TABLE applications ADD COLUMN location TEXT;
        END IF;
    END$$;
    """)

    conn.commit(); conn.close()

init_db()

# ================= SIDEBAR =================
with st.sidebar:
    if st.session_state.user:
        st.success(f"👤 {st.session_state.user}")
        st.button("🔍 Search", on_click=lambda: st.session_state.update(page="search"))
        st.button("📌 Applied", on_click=lambda: st.session_state.update(page="applied"))
        if st.session_state.role == "Admin":
            st.button("📊 Admin Dashboard", on_click=lambda: st.session_state.update(page="admin"))
        if st.button("🚪 Logout"):
            st.session_state.user = None
            st.session_state.role = None
            st.session_state.page = "search"
            st.rerun()

# ================= PASSWORD =================
def strong_password(p):
    return (
        len(p) >= 8 and
        re.search(r"[A-Z]", p) and
        re.search(r"[a-z]", p) and
        re.search(r"[0-9]", p) and
        re.search(r"[!@#$%^&*]", p)
    )

# ================= AUTH =================
def register_user(username, email, password, role):
    if not strong_password(password):
        return False, "Password must include A-Z, a-z, 0-9 & symbol"

    conn = db(); cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE username=%s OR email=%s", (username, email))
    if cur.fetchone():
        conn.close()
        return False, "Username or Email already exists"

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    cur.execute(
        "INSERT INTO users (username,email,password,role) VALUES (%s,%s,%s,%s)",
        (username, email, psycopg2.Binary(hashed), role)
    )
    conn.commit(); conn.close()
    return True, "Registration successful"

def validate_login(username, password):
    conn = db(); cur = conn.cursor()
    cur.execute("SELECT password, role FROM users WHERE username=%s", (username,))
    row = cur.fetchone(); conn.close()
    if row and bcrypt.checkpw(password.encode(), bytes(row[0])):
        return row[1]
    return None

# ================= RESUME PARSER =================
SKILL_BANK = [
    "python","java","c++","sql","machine learning","deep learning","data science",
    "ai","nlp","react","django","flask","spring","aws","azure","gcp",
    "docker","kubernetes","html","css","javascript","power bi","tableau",
    "excel","linux","git","devops","cyber security"
]

def parse_resume(file):
    reader = PyPDF2.PdfReader(file)
    text = " ".join([p.extract_text() or "" for p in reader.pages]).lower()
    return sorted(set([s for s in SKILL_BANK if s in text]))

# ================= ML MODEL =================
def build_features(df):
    df["stipend"] = df.get("stipend", 15000).fillna(15000)
    df["skill_count"] = df["description"].apply(lambda x: len(set(x.lower().split())))
    df["company_score"] = df["company"].map(df["company"].value_counts()).fillna(1)
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
    X = df[["stipend","skill_count","company_score","is_remote"]]
    y = df["demand"]
    model = LinearRegression()
    model.fit(X, y)
    acc = r2_score(y, model.predict(X)) * 100
    return model, round(acc, 2)

# ================= LOGIN =================
if not st.session_state.user:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.title("🎓 Internship Portal")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        u = st.text_input("Username", key="lu")
        p = st.text_input("Password", type="password", key="lp")
        if st.button("Login"):
            r = validate_login(u, p)
            if r:
                st.session_state.user = u
                st.session_state.role = r
                st.rerun()
            else:
                st.error("Invalid credentials")

    with tab2:
        u = st.text_input("Username", key="ru")
        e = st.text_input("Email", key="re")
        p = st.text_input("Password", type="password", key="rp")
        role = st.selectbox("Role", ["Student","Admin"])
        if st.button("Register"):
            ok, msg = register_user(u, e, p, role)
            st.success(msg) if ok else st.error(msg)

    st.markdown("</div>", unsafe_allow_html=True)

# ================= STUDENT =================
elif st.session_state.role == "Student":
    df = pd.read_csv("adzuna_internships_raw.csv")
    df.columns = df.columns.str.lower()
    df["description"] = df["description"].fillna("")
    df = build_features(df)
    model, acc = train_model(df)

    st.info(f"📈 ML Demand Accuracy: **{acc}%**")

    if st.session_state.page == "search":
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        pdf = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
        if pdf:
            st.session_state.resume_skills = parse_resume(pdf)
            st.success(f"Skills detected: {', '.join(st.session_state.resume_skills)}")

        skill = st.text_input("Skill", value=", ".join(st.session_state.resume_skills))
        city = st.selectbox("Preferred City", ["All"] + sorted(df["location"].dropna().unique()))

        if st.button("Search Internships"):
            keywords = [s.strip().lower() for s in skill.split(",") if s.strip()]
            results = df[
                df["description"].str.lower().apply(
                    lambda x: any(k in x for k in keywords)
                )
            ] if keywords else df

            if city != "All":
                results = results[results["location"].str.contains(city, case=False)]

            results["score"] = model.predict(
                results[["stipend","skill_count","company_score","is_remote"]]
            )

            for i, j in results.sort_values("score", ascending=False).head(10).iterrows():
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.markdown(f"""
                <div class='title'>{j['title']}</div>
                <div class='sub'>🏢 {j['company']} | 📍 {j['location']}</div>
                💰 ₹{int(j['stipend'])}
                <span class='badge'>Demand {int(j['score'])}</span>
                """, unsafe_allow_html=True)

                if st.button("Apply", key=f"a{i}"):
                    conn = db(); cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO applications (username,job_title,company,location) VALUES (%s,%s,%s,%s)",
                        (st.session_state.user, j["title"], j["company"], j["location"])
                    )
                    conn.commit(); conn.close()
                    st.success("Applied successfully")
                st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    elif st.session_state.page == "applied":
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        conn = db()
        apps = pd.read_sql(
            "SELECT job_title, company, location, applied_at FROM applications WHERE username=%s",
            conn, params=(st.session_state.user,)
        )
        conn.close()
        st.dataframe(apps)
        st.markdown("</div>", unsafe_allow_html=True)

# ================= ADMIN =================
elif st.session_state.role == "Admin":
    st.title("📊 Admin Analytics Dashboard")

    df = pd.read_csv("adzuna_internships_raw.csv")
    df["description"] = df["description"].fillna("")
    df = build_features(df)

    # Skill trend forecasting (proxy)
    skill_counts = {}
    for desc in df["description"]:
        for s in SKILL_BANK:
            if s in desc.lower():
                skill_counts[s] = skill_counts.get(s, 0) + 1

    trend_df = pd.DataFrame(
        sorted(skill_counts.items(), key=lambda x: x[1], reverse=True),
        columns=["Skill","Demand"]
    ).head(15)

    st.subheader("🔥 Skill Demand Forecast")
    st.bar_chart(trend_df.set_index("Skill"))
