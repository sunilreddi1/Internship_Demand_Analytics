import streamlit as st
import pandas as pd
import psycopg2
import bcrypt
import re
import PyPDF2

from src.demand_model import train_model
from src.preprocess import preprocess_data

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
    "resume_skills": [],
    "dark": False
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

def current_user():
    return st.session_state.user.lower().strip()

# ================= DATABASE =================
def db():
    if not hasattr(st.session_state, "db_fallback"):
        st.session_state.db_fallback = False
    try:
        return psycopg2.connect(st.secrets["db"]["url"], sslmode="require")
    except Exception:
        if not st.session_state.db_fallback:
            st.info("🔄 Using local SQLite DB")
            st.session_state.db_fallback = True
        import sqlite3
        return sqlite3.connect("users.db")

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

    conn = db()
    cur = conn.cursor()

    try:
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        if hasattr(conn, "autocommit"):
            cur.execute(
                "INSERT INTO users (username,email,password,role) VALUES (%s,%s,%s,%s)",
                (username, email, psycopg2.Binary(hashed), role)
            )
        else:
            cur.execute(
                "INSERT INTO users (username,email,password,role) VALUES (?,?,?,?)",
                (username, email, hashed.decode(), role)
            )
        conn.commit()
        return True, "Registered successfully"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def validate_login(username, password):
    username = username.lower().strip()
    conn = db()
    cur = conn.cursor()

    if hasattr(conn, "autocommit"):
        cur.execute("SELECT password, role FROM users WHERE username=%s", (username,))
        row = cur.fetchone()
        if row and bcrypt.checkpw(password.encode(), bytes(row[0])):
            return row[1]
    else:
        cur.execute("SELECT password, role FROM users WHERE username=?", (username,))
        row = cur.fetchone()
        if row and bcrypt.checkpw(password.encode(), row[0].encode()):
            return row[1]
    return None

# ================= RESUME PARSER =================
SKILL_BANK = [
    "python","java","sql","machine learning","data science","ai","react",
    "django","flask","aws","docker","html","css","javascript"
]

def parse_resume(file):
    reader = PyPDF2.PdfReader(file)
    text = " ".join([p.extract_text() or "" for p in reader.pages]).lower()
    return [s for s in SKILL_BANK if s in text]

# ================= LOGIN =================
if not st.session_state.user:
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])

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
        if st.button("Create Account"):
            ok, msg = register_user(u, e, p, "Student")
            st.success(msg) if ok else st.error(msg)

# ================= STUDENT =================
else:
    df = preprocess_data()
    model, acc = train_model(df)
    st.info(f"📈 ML Demand Accuracy: {acc}%")

    tab1, tab2 = st.tabs(["🔎 Search Internships", "📋 My Applications"])

    # ---------- SEARCH ----------
    with tab1:
        pdf = st.file_uploader("📄 Upload Resume", type=["pdf"])
        if pdf:
            st.session_state.resume_skills = parse_resume(pdf)

        skills = st.text_input("Skills", ", ".join(st.session_state.resume_skills))

        if st.button("Find Internships"):
            keywords = [k.strip().lower() for k in skills.split(",") if k.strip()]
            results = df[df["description"].str.lower().str.contains("|".join(keywords))]

            for i, j in results.head(10).iterrows():
                st.markdown(f"""
                **{j['title']}**  
                🏢 {j['company']} | 📍 {j['location']} | 💰 ₹{int(j['stipend'])}
                """)

                if st.button("Apply 🚀", key=f"apply_{i}"):
                    conn = db()
                    cur = conn.cursor()

                    if hasattr(conn, "autocommit"):
                        cur.execute(
                            "INSERT INTO applications (username,job_title,company,location) VALUES (%s,%s,%s,%s)",
                            (current_user(), j["title"], j["company"], j["location"])
                        )
                    else:
                        cur.execute(
                            "INSERT INTO applications (username,job_title,company,location) VALUES (?,?,?,?)",
                            (current_user(), j["title"], j["company"], j["location"])
                        )

                    conn.commit()
                    conn.close()

                    st.session_state.applied_success = j["title"]

        if "applied_success" in st.session_state:
            st.success(f"🎉 Successfully applied for {st.session_state.applied_success}")
            del st.session_state.applied_success

    # ---------- APPLIED ----------
    with tab2:
        conn = db()
        if hasattr(conn, "autocommit"):
            apps = pd.read_sql(
                "SELECT job_title, company, location, applied_at FROM applications WHERE username=%s ORDER BY applied_at DESC",
                conn,
                params=(current_user(),)
            )
        else:
            apps = pd.read_sql_query(
                "SELECT job_title, company, location, applied_at FROM applications WHERE username=? ORDER BY applied_at DESC",
                conn,
                params=(current_user(),)
            )
        conn.close()

        st.dataframe(apps if not apps.empty else pd.DataFrame(columns=["No applications yet"]))
