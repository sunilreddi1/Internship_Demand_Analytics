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
    "resume_skills": [],
    "dark": False
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ================= HELPERS =================
def current_user():
    return st.session_state.user.strip().lower()

# ================= THEME =================
bg = "#020617" if st.session_state.dark else "#f8fafc"
card = "#020617" if st.session_state.dark else "white"
text = "#e5e7eb" if st.session_state.dark else "#0f172a"
sub = "#94a3b8" if st.session_state.dark else "#475569"

st.markdown(f"""
<style>
body {{ background:{bg}; color:{text}; }}
.card {{
    background:{card};
    padding:26px;
    border-radius:18px;
    box-shadow:0 12px 28px rgba(0,0,0,0.25);
    margin-bottom:22px;
}}
.badge {{
    background:#0ea5e9;
    color:white;
    padding:6px 14px;
    border-radius:999px;
    font-size:13px;
}}
.title {{ font-size:22px; font-weight:700; }}
.sub {{ color:{sub}; }}
button {{
    background:#2563eb!important;
    color:white!important;
    border-radius:10px!important;
}}
</style>
""", unsafe_allow_html=True)

# ================= DATABASE =================
def db():
    return psycopg2.connect(st.secrets["db"]["url"], sslmode="require")

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
    """)

    cur.execute("""
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

# ================= SIDEBAR =================
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/3/38/Indeed_logo.svg", width=150)
    st.toggle("🌙 Dark Mode", key="dark")

    if st.session_state.user:
        st.success(f"👤 {st.session_state.user}")
        st.button("🔍 Search", on_click=lambda: st.session_state.update(page="search"))
        st.button("📌 Applied", on_click=lambda: st.session_state.update(page="applied"))
        if st.button("🚪 Logout"):
            st.session_state.clear()
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
        return False, "Weak password"

    username = username.lower().strip()
    email = email.lower().strip()

    conn = db(); cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE username=%s OR email=%s", (username, email))
    if cur.fetchone():
        conn.close()
        return False, "User already exists"

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    cur.execute(
        "INSERT INTO users (username,email,password,role) VALUES (%s,%s,%s,%s)",
        (username, email, psycopg2.Binary(hashed), role)
    )
    conn.commit(); conn.close()
    return True, "Registered"

def validate_login(username, password):
    username = username.lower().strip()
    conn = db(); cur = conn.cursor()
    cur.execute("SELECT password, role FROM users WHERE username=%s", (username,))
    row = cur.fetchone(); conn.close()
    if row and bcrypt.checkpw(password.encode(), bytes(row[0])):
        return row[1]
    return None

# ================= RESUME PARSER =================
SKILL_BANK = [
    "python","java","sql","machine learning","data science","ai","react",
    "django","flask","aws","docker","html","css","javascript","excel","git"
]

def parse_resume(file):
    reader = PyPDF2.PdfReader(file)
    text = " ".join([p.extract_text() or "" for p in reader.pages]).lower()
    return sorted(set(s for s in SKILL_BANK if s in text))

# ================= ML =================
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
    model = LinearRegression().fit(X, y)
    return model, round(r2_score(y, model.predict(X))*100, 2)

# ================= LOGIN UI =================
if not st.session_state.user:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            role = validate_login(u, p)
            if role:
                st.session_state.user = u.lower().strip()
                st.session_state.role = role
                st.rerun()
            else:
                st.error("Invalid credentials")

    with tab2:
        u = st.text_input("New Username")
        e = st.text_input("Email")
        p = st.text_input("New Password", type="password")
        if st.button("Register"):
            ok, msg = register_user(u, e, p, "Student")
            st.success(msg) if ok else st.error(msg)

    st.markdown("</div>", unsafe_allow_html=True)

# ================= STUDENT =================
else:
    df = pd.read_csv("adzuna_internships_raw.csv")
    df.columns = df.columns.str.lower()
    df["description"] = df["description"].fillna("")
    df = build_features(df)
    model, acc = train_model(df)

    st.info(f"📈 ML Demand Accuracy: {acc}%")

    if st.session_state.page == "search":
        st.markdown("<div class='card'>", unsafe_allow_html=True)

        pdf = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
        if pdf:
            st.session_state.resume_skills = parse_resume(pdf)

        skill = st.text_input("Skills", value=", ".join(st.session_state.resume_skills))
        city = st.selectbox("City", ["All"] + sorted(df["location"].dropna().unique()))

        if st.button("Search Internships"):
            keywords = [k.strip().lower() for k in skill.split(",") if k.strip()]
            results = df if not keywords else df[df["description"].str.lower().apply(lambda x: any(k in x for k in keywords))]
            if city != "All":
                results = results[results["location"].str.contains(city, case=False)]

            results = results.copy()
            results["score"] = model.predict(results[["stipend","skill_count","company_score","is_remote"]])

            for i, j in results.sort_values("score", ascending=False).head(10).iterrows():
                conn = db(); cur = conn.cursor()
                cur.execute(
                    "SELECT 1 FROM applications WHERE LOWER(username)=%s AND job_title=%s AND company=%s",
                    (current_user(), j["title"], j["company"])
                )
                applied = cur.fetchone() is not None
                conn.close()

                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.markdown(f"""
                <div class='title'>{j['title']}</div>
                <div class='sub'>🏢 {j['company']} | 📍 {j['location']}</div>
                💰 ₹{int(j['stipend'])}
                <span class='badge'>Score {int(j['score'])}</span>
                """, unsafe_allow_html=True)

                if applied:
                    st.markdown("<span class='badge'>✔ Applied</span>", unsafe_allow_html=True)
                else:
                    if st.button("Apply", key=f"apply_{i}"):
                        conn = db(); cur = conn.cursor()
                        cur.execute(
                            "INSERT INTO applications (username,job_title,company,location) VALUES (%s,%s,%s,%s)",
                            (current_user(), j["title"], j["company"], j["location"])
                        )
                        conn.commit(); conn.close()
                        st.toast("🎉 Applied successfully!", icon="✅")
                        st.session_state.page = "applied"
                        st.rerun()

                st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    elif st.session_state.page == "applied":
        st.markdown("<div class='card'>", unsafe_allow_html=True)

        conn = db()
query = """
    SELECT job_title, company, location, applied_at
    FROM applications
    WHERE username = %s
    ORDER BY applied_at DESC
"""
apps = pd.read_sql(query, conn, params=(current_user(),))
conn.close()

if apps.empty:
    st.info("You have not applied to any internships yet.")
else:
    st.dataframe(apps, use_container_width=True)
