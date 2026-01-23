import streamlit as st
import pandas as pd
import psycopg2
import bcrypt
import numpy as np
import re
import PyPDF2
from sqlalchemy import create_engine
from src.demand_model import build_features, train_model
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
    "page": "search",
    "resume_skills": [],
    "dark": False
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

def current_user():
    return st.session_state.user.strip().lower()

# ================= THEME =================
bg = "#020617" if st.session_state.dark else "#f1f5f9"
card = "rgba(15,23,42,0.75)" if st.session_state.dark else "rgba(255,255,255,0.95)"
text = "#e5e7eb" if st.session_state.dark else "#0f172a"
sub = "#94a3b8" if st.session_state.dark else "#475569"

# ================= GLOBAL STYLE =================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

/* Base font for app */
html, body, [class*="css"], [data-testid="stAppViewContainer"] {{
    font-family: 'Inter', sans-serif !important;
}}

/* Target Streamlit app container explicitly to override theme on deploy */
[data-testid="stAppViewContainer"] {{
    background: {bg} !important;
    color: {text} !important;
}}

/* Fallback generic body rule (kept for environments without data-testid) */
body {{
    background: {bg} !important;
    color: {text} !important;
}}

.card {{
    background: {card} !important;
    padding: 28px;
    border-radius: 20px;
    margin-bottom: 24px;
    box-shadow: 0 18px 36px rgba(0,0,0,0.25);
    animation: fadeInUp 0.6s ease both;
    transition: transform .25s ease, box-shadow .25s ease;
}}

.card:hover {{
    transform: translateY(-6px);
    box-shadow: 0 26px 55px rgba(0,0,0,0.35);
}}

@keyframes fadeInUp {{
    from {{
        opacity: 0;
        transform: translateY(18px);
    }}
    to {{
        opacity: 1;
        transform: translateY(0);
    }}
}}

.title {{
    font-size: 22px;
    font-weight: 700;
}}

.sub {{
    color: {sub} !important;
}}

.badge {{
    background: linear-gradient(135deg, #0ea5e9, #38bdf8);
    color: white;
    padding: 6px 14px;
    border-radius: 999px;
    font-size: 12px;
    margin-left: 6px;
}}

/* Streamlit button targeting */
.stButton>button, button {{
    background: linear-gradient(135deg,#2563eb,#38bdf8) !important;
    color: white !important;
    border-radius: 14px !important;
    font-weight: 600 !important;
    border: none !important;
}}

.stButton>button:hover, button:hover {{
    transform: translateY(-1px);
    box-shadow: 0 8px 18px rgba(37,99,235,0.45) !important;
}}

/* Ensure main container backgrounds are transparent so .card shows through */
[data-testid="stAppViewContainer"] .css-1d391kg, /* class may vary */
[data-testid="stAppViewContainer"] .main {{
    background: transparent !important;
}}

</style>
""", unsafe_allow_html=True)

# ================= DATABASE =================
def db():
    # Check if we've already shown the fallback warning this session
    if not hasattr(st.session_state, 'db_fallback_shown'):
        st.session_state.db_fallback_shown = False

    try:
        # Return SQLAlchemy engine for PostgreSQL
        return create_engine(st.secrets["db"]["url"])
    except Exception as e:
        if not st.session_state.db_fallback_shown:
            st.info("🔄 Using local database for testing. Your data will be stored locally.")
            st.session_state.db_fallback_shown = True
        # Fallback to local SQLite for development
        return create_engine("sqlite:///users.db")

def init_db():
    try:
        engine = db()
        with engine.connect() as conn:
            # Get raw connection for cursor operations
            raw_conn = conn.connection if hasattr(conn, 'connection') else conn
            cur = raw_conn.cursor()

            # Check if it's PostgreSQL or SQLite based on engine URL
            if 'postgresql' in str(engine.url):
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
            else:  # SQLite
                cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT,
                    role TEXT
                );
                """)
                cur.execute("""
                CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                job_title TEXT,
                company TEXT,
                location TEXT,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

        conn.commit()
        conn.close()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization failed: {e}")

# Database already initialized
# init_db()

# ================= SIDEBAR =================
with st.sidebar:
    st.markdown("## 🎓 Internship Portal")
    st.caption("AI-driven internship matching")

    st.divider()

    st.session_state.dark = st.toggle(
        "🌙 Dark Mode" if not st.session_state.dark else "☀️ Light Mode",
        value=st.session_state.dark
    )

    st.divider()

    if st.session_state.user:
        st.success(f"👤 {st.session_state.user}")

        st.button("🔍  Search Internships",
                  on_click=lambda: st.session_state.update(page="search"))

        st.button("📌  Applied Internships",
                  on_click=lambda: st.session_state.update(page="applied"))

        if st.session_state.role == "Admin":
            st.button("📊  Admin Dashboard",
                      on_click=lambda: st.session_state.update(page="admin"))

        if st.button("🚪  Logout"):
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

    try:
        engine = db()
        with engine.connect() as conn:
            # Get raw connection for cursor operations
            raw_conn = conn.connection if hasattr(conn, 'connection') else conn
            cur = raw_conn.cursor()

            # Check if PostgreSQL or SQLite based on engine URL
            if 'postgresql' in str(engine.url):
                cur.execute("SELECT 1 FROM users WHERE username=%s OR email=%s", (username, email))
                if cur.fetchone():
                    return False, "User already exists"

                hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
                cur.execute(
                    "INSERT INTO users (username,email,password,role) VALUES (%s,%s,%s,%s)",
                    (username, email, psycopg2.Binary(hashed), role)
                )
            else:  # SQLite
                cur.execute("SELECT 1 FROM users WHERE username=?", (username,))
                if cur.fetchone():
                    return False, "User already exists"

                hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
                cur.execute(
                    "INSERT INTO users (username,password,role) VALUES (?,?,?)",
                    (username, hashed.decode('utf-8'), role)
                )

            raw_conn.commit()
        return True, "Registered successfully"
    except Exception as e:
        return False, f"Registration failed: {e}"

def validate_login(username, password):
    username = username.lower().strip()
    try:
        engine = db()
        with engine.connect() as conn:
            # Get raw connection for cursor operations
            raw_conn = conn.connection if hasattr(conn, 'connection') else conn
            cur = raw_conn.cursor()

            if 'postgresql' in str(engine.url):
                cur.execute("SELECT password, role FROM users WHERE username=%s", (username,))
                row = cur.fetchone()
                if row and bcrypt.checkpw(password.encode(), bytes(row[0])):
                    return row[1]
            else:  # SQLite
                cur.execute("SELECT password, role FROM users WHERE username=?", (username,))
                row = cur.fetchone()
                if row and bcrypt.checkpw(password.encode(), row[0].encode('utf-8')):
                    return row[1]
        return None
    except Exception as e:
        st.error(f"Login failed: {e}")
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

# ================= LOGIN =================
if not st.session_state.user:
    st.markdown("<div class='card'>", unsafe_allow_html=True)

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
            if ok:
                st.success(msg)
            else:
                st.error(msg)

    st.markdown("</div>", unsafe_allow_html=True)

# ================= STUDENT =================
else:
    if st.session_state.role == "Student":
        df = preprocess_data()
        model, acc = train_model(df)
        st.info(f"📈 ML Demand Accuracy: {acc}%")

        tab1, tab2 = st.tabs(["🔎 Search Internships", "📋 My Applications"])

        with tab1:
            st.markdown("<div class='card'>", unsafe_allow_html=True)

            pdf = st.file_uploader("📄 Upload Resume (PDF)", type=["pdf"])
            if pdf:
                st.session_state.resume_skills = parse_resume(pdf)

            skill = st.text_input("Skills", value=", ".join(st.session_state.resume_skills))
            city = st.selectbox("Preferred City", ["All"] + sorted(df["location"].dropna().unique()))

            # Show internships by default, filtered by search criteria
            keywords = [k.strip().lower() for k in skill.split(",") if k.strip()]
            results = df if not keywords else df[
                df["description"].str.lower().apply(lambda x: any(k in x for k in keywords))
            ]
            if city != "All":
                results = results[results["location"].str.contains(city, case=False)]

            # Get list of already applied job titles for this user
            try:
                engine = db()
                if 'postgresql' in str(engine.url):
                    applied_jobs = pd.read_sql("""
                        SELECT DISTINCT job_title
                        FROM applications
                        WHERE LOWER(username)=%(username)s
                    """, engine, params={'username': current_user()})
                else:  # SQLite
                    applied_jobs = pd.read_sql_query("""
                        SELECT DISTINCT job_title
                        FROM applications
                        WHERE LOWER(username)=LOWER(?)
                    """, engine, params=(current_user(),))
                
                applied_titles = applied_jobs['job_title'].str.lower().tolist() if not applied_jobs.empty else []
            except:
                applied_titles = []

            results = results.copy()
            results["score"] = model.predict(
                results[["stipend","skill_count","company_score","is_remote"]]
            )

            # Filter out already applied internships
            results = results[~results["title"].str.lower().isin(applied_titles)]

            if st.button("🔎 Find Internships"):
                st.markdown(f"<h3>🎯 Found {len(results)} internships matching your criteria</h3>", unsafe_allow_html=True)
            else:
                st.markdown(f"<h3>🎯 Top {min(10, len(results))} recommended internships</h3>", unsafe_allow_html=True)
            
            for i, j in results.sort_values("score", ascending=False).head(10).iterrows():
                    st.markdown("<div class='card'>", unsafe_allow_html=True)

                    st.markdown(f"""
                    <div class='title'>{j['title']}</div>
                    <div class='sub'>🏢 {j['company']} | 📍 {j['location']}</div>
                    💰 ₹{int(j['stipend'])}
                    <span class='badge'>Score {int(j['score'])}</span>
                    """, unsafe_allow_html=True)

                    if st.button("Apply 🚀", key=f"apply_{i}"):
                        try:
                            engine = db()
                            with engine.connect() as conn:
                                # Get raw connection for cursor operations
                                raw_conn = conn.connection if hasattr(conn, 'connection') else conn
                                cur = raw_conn.cursor()
                                
                                if 'postgresql' in str(engine.url):
                                    cur.execute(
                                        "INSERT INTO applications (username,job_title,company,location) VALUES (%s,%s,%s,%s)",
                                        (current_user(), j["title"], j["company"], j["location"])
                                    )
                                else:  # SQLite - check schema and adapt
                                    # Check if table has correct columns
                                    cur.execute("PRAGMA table_info(applications)")
                                    columns = [col[1] for col in cur.fetchall()]
                                    if 'job_title' in columns:
                                        cur.execute(
                                            "INSERT INTO applications (username,job_title,company,location) VALUES (?,?,?,?)",
                                            (current_user(), j["title"], j["company"], j["location"])
                                        )
                                    else:
                                        # Use existing schema
                                        cur.execute(
                                            "INSERT INTO applications (username,job_id,status) VALUES (?,?,?)",
                                            (current_user(), j["title"], "Applied")
                                        )
                                raw_conn.commit()
                            st.success("🎉 Applied successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Application failed: {e}")

                    st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        with tab2:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            try:
                engine = db()
                # Check if it's PostgreSQL or SQLite based on engine URL
                if 'postgresql' in str(engine.url):
                    apps = pd.read_sql("""
                        SELECT job_title, company, location, applied_at
                        FROM applications
                        WHERE LOWER(username)=%(username)s
                        ORDER BY applied_at DESC
                    """, engine, params={'username': current_user()})
                else:  # SQLite
                    with engine.connect() as conn:
                        cur = conn.connection.cursor()
                        cur.execute("PRAGMA table_info(applications)")
                        columns = [col[1] for col in cur.fetchall()]
                        
                        if 'job_title' in columns:
                            apps = pd.read_sql_query("""
                                SELECT job_title, company, location, applied_at
                            FROM applications
                            WHERE LOWER(username)=LOWER(?)
                            ORDER BY applied_at DESC
                        """, engine, params=(current_user(),))
                        else:
                            # Use existing schema
                            apps = pd.read_sql_query("""
                                SELECT job_id as job_title, 'Applied' as company, '' as location, id as applied_at
                            FROM applications
                            WHERE LOWER(username)=LOWER(?)
                            ORDER BY id DESC
                        """, engine, params=(current_user(),))
            except Exception as e:
                st.error(f"Failed to load applications: {e}")
                apps = pd.DataFrame()  # Empty dataframe as fallback
            st.dataframe(apps, width='stretch')

            st.markdown("</div>", unsafe_allow_html=True)

    elif st.session_state.role == "Admin":
        from src.admin_dashboard import show_admin_dashboard
        show_admin_dashboard()
