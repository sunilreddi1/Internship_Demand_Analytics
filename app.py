import streamlit as st
import pandas as pd
import psycopg2
import bcrypt
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import re

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
    "page": "search"
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ================= THEME =================
st.markdown("""
<style>
body { background:#f8fafc; }
.card {
    background:white;
    padding:22px;
    border-radius:14px;
    box-shadow:0 6px 20px rgba(0,0,0,0.06);
    margin-bottom:20px;
}
.badge {
    background:#e0f2fe;
    color:#0369a1;
    padding:6px 10px;
    border-radius:999px;
}
button { background:#2563eb!important; color:white!important; }
</style>
""", unsafe_allow_html=True)

# ================= SIDEBAR =================
with st.sidebar:
    if st.session_state.user:
        st.success(f"👤 {st.session_state.user}")
        st.button("🔍 Search", on_click=lambda: st.session_state.update(page="search"))
        st.button("📌 Applied", on_click=lambda: st.session_state.update(page="applied"))
        if st.button("🚪 Logout"):
            st.session_state.user = None
            st.session_state.role = None
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
        return False, "Weak password"

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

# ================= LOGIN UI =================
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
        role = st.selectbox("Role", ["Student"], key="rr")
        if st.button("Register"):
            ok, msg = register_user(u, e, p, role)
            st.success(msg) if ok else st.error(msg)

    st.markdown("</div>", unsafe_allow_html=True)

# ================= STUDENT =================
else:
    df = pd.read_csv("adzuna_internships_raw.csv")
    df.columns = df.columns.str.lower()
    df["description"] = df["description"].fillna("")
    df = build_features(df)
    model, acc = train_model(df)

    st.info(f"📈 ML Demand Accuracy: **{acc}%**")

    if st.session_state.page == "search":
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("🔍 Find & Apply Internships")

        skill = st.text_input("Skill (Python, Java, ML...)")
        location = st.selectbox("Preferred Location", sorted(df["location"].dropna().unique()))

        if st.button("Recommend Best Internships"):
            df["score"] = df.apply(
                lambda r: model.predict(pd.DataFrame([[
                    r["stipend"], r["skill_count"],
                    r["company_score"], r["is_remote"]
                ]]))[0], axis=1
            )

            recs = df[
                df["description"].str.contains(skill, case=False) &
                df["location"].str.contains(location, case=False)
            ].sort_values("score", ascending=False).head(10)

            for i, j in recs.iterrows():
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.markdown(f"""
                ### {j['title']}
                🏢 **{j['company']}**  
                📍 {j['location']}  
                💰 Stipend: ₹{int(j['stipend'])}
                <span class='badge'>Demand Score: {int(j['score'])}</span>
                """, unsafe_allow_html=True)

                if st.button("Apply", key=f"apply_{i}"):
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
        st.subheader("📌 Applied Internships")
        conn = db()
        apps = pd.read_sql(
            "SELECT job_title, company, location, applied_at FROM applications WHERE username=%s ORDER BY applied_at DESC",
            conn, params=(st.session_state.user,)
        )
        conn.close()
        st.dataframe(apps)
        st.markdown("</div>", unsafe_allow_html=True)
