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

# ================= SIDEBAR =================
with st.sidebar:
    if st.session_state.user:
        st.success(f"👤 {st.session_state.user}")
        st.button("🔍 Search", on_click=lambda: st.session_state.update(page="search"))
        st.button("📌 Applied", on_click=lambda: st.session_state.update(page="applied"))
        if st.session_state.role == "Admin":
            st.button("📊 Admin Analytics", on_click=lambda: st.session_state.update(page="admin"))
        if st.button("🚪 Logout"):
            st.session_state.user = None
            st.session_state.page = "search"
            st.rerun()

# ================= DATABASE =================
def db():
    return psycopg2.connect(st.secrets["db"]["url"])

def init_db():
    conn = db(); cur = conn.cursor()
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
        location TEXT,
        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit(); conn.close()

init_db()

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
    "ai","nlp","opencv","react","node","django","flask","spring",
    "aws","azure","gcp","cloud","docker","kubernetes","html","css","javascript",
    "power bi","tableau","excel","linux","git","devops","cyber security"
]

def parse_resume(file):
    reader = PyPDF2.PdfReader(file)
    text = " ".join([p.extract_text() or "" for p in reader.pages]).lower()
    return sorted(set([s for s in SKILL_BANK if s in text]))

# ================= RESUME–INTERNSHIP SIMILARITY (NEW) =================
def similarity_score(resume_skills, description):
    if not resume_skills:
        return 0
    text = description.lower()
    matches = sum(1 for s in resume_skills if s in text)
    return round((matches / len(resume_skills)) * 100, 2)

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
        if st.button("Register"):
            ok, msg = register_user(u, e, p, "Student")
            st.success(msg) if ok else st.error(msg)

    st.markdown("</div>", unsafe_allow_html=True)

# ================= STUDENT =================
elif st.session_state.page in ["search", "applied"]:
    df = pd.read_csv("adzuna_internships_raw.csv")
    df.columns = df.columns.str.lower()
    df["description"] = df["description"].fillna("")
    df = build_features(df)
    model, acc = train_model(df)

    st.info(f"📈 ML Demand Accuracy: **{acc}%**")

    if st.session_state.page == "search":
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        pdf = st.file_uploader("📄 Upload Resume (Optional)", type=["pdf"])
        if pdf:
            st.session_state.resume_skills = parse_resume(pdf)
            st.success(f"Skills detected: {', '.join(st.session_state.resume_skills)}")

        skill = st.text_input("Skill", value=", ".join(st.session_state.resume_skills))
        city = st.selectbox("Preferred City", ["All"] + sorted(df["location"].dropna().unique()))

        if st.button("Search Internships"):
            results = df.copy()
            if city != "All":
                results = results[results["location"].str.contains(city, case=False)]

            results["score"] = model.predict(
                results[["stipend","skill_count","company_score","is_remote"]]
            )

            for i, j in results.sort_values("score", ascending=False).head(10).iterrows():
                sim = similarity_score(st.session_state.resume_skills, j["description"])
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.markdown(f"""
                <div class='title'>{j['title']}</div>
                <div class='sub'>🏢 {j['company']} | 📍 {j['location']}</div>
                💰 ₹{int(j['stipend'])}
                <br>
                <span class='badge'>Demand {int(j['score'])}</span>
                <span class='badge'>Resume Match {sim}%</span>
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

# ================= ADMIN ANALYTICS (NEW) =================
elif st.session_state.page == "admin":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.title("📊 Admin Analytics Dashboard")

    conn = db()
    users = pd.read_sql("SELECT COUNT(*) FROM users", conn).iloc[0,0]
    apps = pd.read_sql("SELECT COUNT(*) FROM applications", conn).iloc[0,0]
    by_city = pd.read_sql("SELECT location, COUNT(*) cnt FROM applications GROUP BY location", conn)
    by_company = pd.read_sql("SELECT company, COUNT(*) cnt FROM applications GROUP BY company", conn)
    conn.close()

    st.metric("Total Users", users)
    st.metric("Total Applications", apps)
    st.subheader("📍 Applications by City")
    st.bar_chart(by_city.set_index("location"))
    st.subheader("🏢 Company-wise Applications")
    st.bar_chart(by_company.set_index("company"))

    st.markdown("</div>", unsafe_allow_html=True)
