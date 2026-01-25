import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import bcrypt
import numpy as np
import re
import PyPDF2
from sqlalchemy import create_engine, text
from src.demand_model import build_features, train_model
from src.preprocess import preprocess_data

# Internship Demand Analytics App - Fixed for Streamlit Cloud deployment

# Optional imports for database
try:
    import psycopg2
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

def calculate_skill_score_only(row, user_skills):
    """Calculate pure skill matching score for display"""
    if not user_skills or pd.isna(row.get('skills_required')):
        return 0

    job_skills = set(str(row['skills_required']).split(', '))
    if not job_skills:
        return 0

    matched_skills = len(set(user_skills).intersection(job_skills))
    return (matched_skills / len(job_skills)) * 100

def current_user():
    return st.session_state.user.strip().lower()

# ================= DATABASE =================
# ================= DATABASE =================
def db():
    # Completely safe database connection - no Streamlit calls during import
    try:
        # Only try PostgreSQL if we're in a proper Streamlit runtime context
        import streamlit as st
        if hasattr(st, 'runtime') and st.runtime.exists():
            try:
                if hasattr(st, 'secrets') and 'db' in st.secrets and 'url' in st.secrets['db']:
                    from sqlalchemy import create_engine, text
                    engine = create_engine(st.secrets["db"]["url"], connect_args={
                        'connect_timeout': 10,  # 10 second timeout
                        'sslmode': 'require'
                    })
                    # Test the connection with timeout
                    with engine.connect() as conn:
                        conn.execute(text("SELECT 1"))
                    return engine
            except Exception as e:
                # Suppress verbose PostgreSQL errors - we expect this to fail and fall back to SQLite
                pass  # Fall through to SQLite
    except:
        pass  # Not in Streamlit context

    # Always fallback to local SQLite for development/safety
    from sqlalchemy import create_engine
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
                    email TEXT UNIQUE,
                    password BLOB,
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

    try:
        engine = db()
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

        # Check if it's PostgreSQL or SQLite based on engine URL
        if 'postgresql' in str(engine.url):
            with engine.connect() as conn:
                # Check if user exists
                result = conn.execute(text("""
                    SELECT username FROM users WHERE LOWER(username)=:username OR email=:email
                """), {"username": username.lower(), "email": email})
                if result.fetchone():
                    return False, "User already exists"

                # Insert new user
                conn.execute(text("""
                    INSERT INTO users (username, email, password, role)
                    VALUES (:username, :email, :password, :role)
                """), {
                    "username": username.lower().strip(),
                    "email": email,
                    "password": hashed,
                    "role": role
                })
                conn.commit()
        else:  # SQLite
            with engine.connect() as conn:
                # Check if user exists
                result = conn.execute(text("""
                    SELECT username FROM users WHERE LOWER(username)=:username OR email=:email
                """), {"username": username.lower(), "email": email})
                if result.fetchone():
                    return False, "User already exists"

                # Insert new user
                conn.execute(text("""
                    INSERT INTO users (username, email, password, role)
                    VALUES (:username, :email, :password, :role)
                """), {
                    "username": username.lower().strip(),
                    "email": email,
                    "password": hashed,
                    "role": role
                })
                conn.commit()

        return True, "Account created successfully"
    except Exception as e:
        return False, f"Registration failed: {e}"

def validate_login(username, password):
    try:
        engine = db()

        # Check if it's PostgreSQL or SQLite based on engine URL
        if 'postgresql' in str(engine.url):
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT password, role FROM users WHERE LOWER(username)=:username
                """), {"username": username.lower()})
                user_data = result.fetchone()
        else:  # SQLite
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT password, role FROM users WHERE LOWER(username)=:username
                """), {"username": username.lower()})
                user_data = result.fetchone()

        if user_data and bcrypt.checkpw(password.encode(), user_data[0] if 'postgresql' in str(engine.url) else user_data[0]):
            return user_data[1]  # Return role
        return None
    except Exception as e:
        return None

# ================= RESUME PARSER =================
def parse_resume(pdf_file):
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()

        # Extract skills using regex patterns
        skills = []
        skill_patterns = [
            r'\b(python|java|javascript|c\+\+|c#|php|ruby|go|rust|kotlin|swift|scala|perl|lua)\b',
            r'\b(html|css|react|angular|vue|node\.js|express|django|flask|spring|hibernate)\b',
            r'\b(sql|mysql|postgresql|mongodb|redis|cassandra|elasticsearch)\b',
            r'\b(aws|azure|gcp|docker|kubernetes|jenkins|git|github|gitlab)\b',
            r'\b(machine learning|deep learning|ai|nlp|computer vision|tensorflow|pytorch|scikit-learn|pandas|numpy)\b',
            r'\b(data analysis|data science|statistics|r|matlab|tableau|power bi)\b'
        ]

        for pattern in skill_patterns:
            matches = re.findall(pattern, text.lower())
            skills.extend(matches)

        return list(set(skills))  # Remove duplicates
    except Exception as e:
        st.error(f"Resume parsing failed: {e}")
        return []

# ================= INTERNSHIP CARD =================
def display_internship_card(job, key_suffix, applied_titles):
    title_lower = job["title"].lower()
    already_applied = title_lower in applied_titles

    col1, col2 = st.columns([4, 1])

    with col1:
        components.html(f"""
        <div class="card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <h3 style="font-size: 22px; font-weight: 700; letter-spacing: normal; text-align: left; margin: 0;">{job["title"][:50]}</h3>
                    <p style="color: #64748b; margin: 4px 0; font-size: 14px;">{job["company"]} • {job["location"]}</p>
                </div>
                <div style="text-align: right;">
                    <span class="badge">₹{job["stipend"]:,}</span>
                    {"<span class='badge' style='background: linear-gradient(135deg, #10b981, #34d399);'>REMOTE</span>" if job["is_remote"] else ""}
                </div>
            </div>
            <p style="margin: 12px 0; color: #64748b; white-space: normal; word-wrap: break-word; line-height: 1.5; font-size: 14px;">{job["description"][:500]}...</p>
            <div style="margin-top: 12px;">
                {f'''
                <div style="margin-bottom: 8px;">
                    <strong style="color: #374151; font-size: 12px;">Required Skills:</strong><br>
                    {"".join([f'<span class="skill-badge">{skill.strip()}</span>' for skill in str(job.get("skills_required", "")).split(", ") if skill.strip()])}
                </div>
                ''' if job.get("skills_required") and str(job.get("skills_required")).strip() else ""}
                <div style="display: flex; gap: 8px; align-items: center;">
                    {f'<span class="badge" style="background: linear-gradient(135deg, #06b6d4, #0891b2);">Skills: {job.get("skill_score", 0)}%</span>' if job.get("skill_score", 0) > 0 else ""}
                    {"<span class='badge' style='background: linear-gradient(135deg, #f59e0b, #fbbf24);'>APPLIED</span>" if already_applied else ""}
                </div>
            </div>
        </div>
        """)

    with col2:
        if not already_applied:
            if st.button("Apply Now", key=f"apply_{key_suffix}", type="primary"):
                try:
                    engine = db()
                    # Check if it's PostgreSQL or SQLite based on engine URL
                    if 'postgresql' in str(engine.url):
                        with engine.connect() as conn:
                            conn.execute(text("""
                                INSERT INTO applications (username, job_title, company, location)
                                VALUES (:username, :job_title, :company, :location)
                            """), {
                                "username": current_user(),
                                "job_title": job["title"],
                                "company": job["company"],
                                "location": job["location"]
                            })
                            conn.commit()
                    else:  # SQLite
                        with engine.connect() as conn:
                            conn.execute(text("""
                                INSERT INTO applications (username, job_title, company, location)
                                VALUES (:username, :job_title, :company, :location)
                            """), {
                                "username": current_user(),
                                "job_title": job["title"],
                                "company": job["company"],
                                "location": job["location"]
                            })
                            conn.commit()

                    st.success("Applied successfully!")
                    # Refresh applied titles cache
                    try:
                        engine = db()
                        if 'postgresql' in str(engine.url):
                            applied_jobs = pd.read_sql("""
                                SELECT DISTINCT job_title
                                FROM applications
                                WHERE LOWER(username)=%(username)s
                            """, engine, params={'username': current_user()})
                        else:
                            applied_jobs = pd.read_sql_query("""
                                SELECT DISTINCT job_title
                                FROM applications
                                WHERE LOWER(username)=LOWER(?)
                            """, engine, params=(current_user(),))
                        st.session_state.applied_titles_cache = applied_jobs['job_title'].str.lower().tolist() if not applied_jobs.empty else []
                    except:
                        pass
                    st.rerun()
                except Exception as e:
                    st.error(f"Application failed: {e}")
        else:
            st.button("Already Applied", key=f"applied_{key_suffix}", disabled=True)

# ================= RECOMMENDATION CARD =================
def display_recommendation_card(rec, idx, applied_titles):
    title_lower = rec["title"].lower()
    already_applied = title_lower in applied_titles

    col1, col2 = st.columns([4, 1])

    with col1:
        components.html(f"""
        <div class="card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <h3 style="font-size: 22px; font-weight: 700; letter-spacing: normal; text-align: left; margin: 0;">{rec["title"][:50]}</h3>
                    <p style="color: #64748b; margin: 4px 0; font-size: 14px;">{rec["company"]} • {rec["location"]}</p>
                </div>
                <div style="text-align: right;">
                    <span class="badge">₹{rec["stipend"]:,}</span>
                    {"<span class='badge' style='background: linear-gradient(135deg, #10b981, #34d399);'>REMOTE</span>" if rec["is_remote"] else ""}
                </div>
            </div>
            <p style="margin: 12px 0; color: #64748b; white-space: normal; word-wrap: break-word; line-height: 1.5; font-size: 14px;">{rec["description"][:500]}...</p>
            <div style="display: flex; gap: 8px; margin-top: 12px;">
                <span class="badge" style="background: linear-gradient(135deg, #8b5cf6, #a78bfa);">AI Match: {rec.get('recommendation_score', 'N/A')}</span>
                <span class="badge" style="background: linear-gradient(135deg, #06b6d4, #0891b2);">Skills: {rec.get('skill_score', 'N/A')}%</span>
                {"<span class='badge' style='background: linear-gradient(135deg, #f59e0b, #fbbf24);'>APPLIED</span>" if already_applied else ""}
            </div>
        </div>
        """)

    with col2:
        if not already_applied:
            if st.button("Apply Now", key=f"rec_apply_{idx}", type="primary"):
                try:
                    engine = db()
                    # Check if it's PostgreSQL or SQLite based on engine URL
                    if 'postgresql' in str(engine.url):
                        with engine.connect() as conn:
                            conn.execute(text("""
                                INSERT INTO applications (username, job_title, company, location)
                                VALUES (:username, :job_title, :company, :location)
                            """), {
                                "username": current_user(),
                                "job_title": rec["title"],
                                "company": rec["company"],
                                "location": rec["location"]
                            })
                            conn.commit()
                    else:  # SQLite
                        with engine.connect() as conn:
                            conn.execute(text("""
                                INSERT INTO applications (username, job_title, company, location)
                                VALUES (:username, :job_title, :company, :location)
                            """), {
                                "username": current_user(),
                                "job_title": rec["title"],
                                "company": rec["company"],
                                "location": rec["location"]
                            })
                            conn.commit()

                    st.success("Applied successfully!")
                    # Refresh applied titles cache
                    try:
                        engine = db()
                        if 'postgresql' in str(engine.url):
                            applied_jobs = pd.read_sql("""
                                SELECT DISTINCT job_title
                                FROM applications
                                WHERE LOWER(username)=%(username)s
                            """, engine, params={'username': current_user()})
                        else:
                            applied_jobs = pd.read_sql_query("""
                                SELECT DISTINCT job_title
                                FROM applications
                                WHERE LOWER(username)=LOWER(?)
                            """, engine, params=(current_user(),))
                        st.session_state.applied_titles_cache = applied_jobs['job_title'].str.lower().tolist() if not applied_jobs.empty else []
                    except:
                        pass
                    st.rerun()
                except Exception as e:
                    st.error(f"Application failed: {e}")
        else:
            st.button("Already Applied", key=f"rec_applied_{idx}", disabled=True)

# ================= MAIN APP =================
def main():
    # ================= PAGE CONFIG =================
    st.set_page_config(
        page_title="Internship Demand & Recommendation Portal",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # ================= WELCOME BANNER =================
    with st.container():
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; padding: 3rem; text-align: center; margin-bottom: 2rem; color: white; width: 100%;">
            <h1 style="font-size: 3rem; margin-bottom: 1rem; font-weight: 700;">Welcome to Internship Portal</h1>
            <p style="font-size: 1.2rem; margin: 0; opacity: 0.9;">Find your perfect internship match with AI-powered recommendations</p>
        </div>
        """, unsafe_allow_html=True)

    # Set default server port to 8502
    import os
    os.environ['STREAMLIT_SERVER_PORT'] = '8502'
    os.environ['STREAMLIT_SERVER_ADDRESS'] = 'localhost'

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
        min-height: 200px;
        width: 100%;
        border: 2px solid transparent;
        background: linear-gradient(135deg, {card}, {card}) padding-box,
                    linear-gradient(135deg, #667eea 0%, #764ba2 100%) border-box;
    }}

    .card:hover {{
        transform: translateY(-6px);
        box-shadow: 0 26px 55px rgba(0,0,0,0.35);
        border-color: #667eea;
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
        letter-spacing: normal !important;
        text-align: left;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}

    .sub {{
        color: {sub} !important;
    }}

    .description {{
        margin: 12px 0;
        color: #64748b;
        white-space: normal;
        word-wrap: break-word;
    }}

    .badge {{
        background: linear-gradient(135deg, #f59e0b, #f97316);
        color: white;
        padding: 6px 14px;
        border-radius: 999px;
        font-size: 12px;
        margin-left: 6px;
        box-shadow: 0 4px 8px rgba(245, 158, 11, 0.3);
    }}

    .skill-badge {{
        background: linear-gradient(135deg, #10b981, #059669);
        color: white;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 11px;
        margin: 2px;
        display: inline-block;
        box-shadow: 0 2px 4px rgba(16, 185, 129, 0.2);
    }}

    /* Streamlit button targeting */
    .stButton>button, button {{
        background: linear-gradient(135deg,#2563eb,#38bdf8) !important;
        color: white !important;
        border-radius: 14px !important;
        font-weight: 600 !important;
        border: none !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3) !important;
    }}

    .stButton>button:hover, button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 18px rgba(37,99,235,0.45) !important;
        background: linear-gradient(135deg,#1d4ed8,#0ea5e9) !important;
    }}

    /* Secondary buttons (like back button) */
    button[kind="secondary"] {{
        background: linear-gradient(135deg,#6b7280,#9ca3af) !important;
        box-shadow: 0 4px 12px rgba(107, 114, 128, 0.3) !important;
    }}

    button[kind="secondary"]:hover {{
        background: linear-gradient(135deg,#4b5563,#6b7280) !important;
        box-shadow: 0 6px 16px rgba(107, 114, 128, 0.4) !important;
    }}

    /* Success buttons */
    button[kind="primary"] {{
        background: linear-gradient(135deg,#10b981,#059669) !important;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3) !important;
    }}

    button[kind="primary"]:hover {{
        background: linear-gradient(135deg,#059669,#047857) !important;
        box-shadow: 0 6px 16px rgba(16, 185, 129, 0.4) !important;
    }}

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background: rgba(255,255,255,0.05);
        padding: 8px;
        border-radius: 12px;
    }}

    .stTabs [data-baseweb="tab"] {{
        background: transparent;
        border-radius: 8px;
        color: {text};
        transition: all 0.3s ease;
    }}

    .stTabs [data-baseweb="tab"][aria-selected="true"] {{
        background: linear-gradient(135deg,#667eea,#764ba2) !important;
        color: white !important;
    }}

    /* Sidebar styling */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {card}, rgba(102, 126, 234, 0.1)) !important;
        border-right: 3px solid #667eea;
    }}

    /* Progress bars */
    .stProgress > div > div > div > div {{
        background: linear-gradient(90deg, #667eea, #764ba2) !important;
    }}

    /* Input fields */
    .stTextInput input, .stSelectbox select {{
        border-radius: 12px !important;
        border: 2px solid #e5e7eb !important;
        transition: border-color 0.3s ease !important;
    }}

    .stTextInput input:focus, .stSelectbox select:focus {{
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
    }}

    /* File uploader */
    .stFileUploader {{
        border: 2px dashed #667eea !important;
        border-radius: 12px !important;
        background: rgba(102, 126, 234, 0.05) !important;
    }}

    /* Success messages */
    .stSuccess {{
        background: linear-gradient(135deg, #10b981, #059669) !important;
        color: white !important;
        border-radius: 12px !important;
        border: none !important;
    }}

    /* Error messages */
    .stError {{
        background: linear-gradient(135deg, #ef4444, #dc2626) !important;
        color: white !important;
        border-radius: 12px !important;
        border: none !important;
    }}

    /* Info messages */
    .stInfo {{
        background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
        color: white !important;
        border-radius: 12px !important;
        border: none !important;
    }}

    /* Warning messages */
    .stWarning {{
        background: linear-gradient(135deg, #f59e0b, #d97706) !important;
        color: white !important;
        border-radius: 12px !important;
        border: none !important;
    }}

    /* Ensure main container backgrounds are transparent so .card shows through */
    [data-testid="stAppViewContainer"] .css-1d391kg, /* class may vary */
    [data-testid="stAppViewContainer"] .main {{
        background: transparent !important;
    }}

    </style>
    """, unsafe_allow_html=True)
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

            if st.session_state.role == "Admin":
                st.button("📊  Admin Dashboard",
                          on_click=lambda: st.session_state.update(page="admin"))

            if st.button("🚪  Logout"):
                st.session_state.clear()
                st.rerun()

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
            @st.cache_data
            def load_data():
                return preprocess_data()

            df = load_data()
            from src.recommender import get_personalized_recommendations

            tab1, tab2, tab3 = st.tabs(["🔎 Smart Search", "🎯 AI Recommendations", "📋 My Applications"])

            with tab1:
                st.markdown("<div class='card'>", unsafe_allow_html=True)

                pdf = st.file_uploader("📄 Upload Resume (PDF)", type=["pdf"])
                if pdf:
                    st.session_state.resume_skills = parse_resume(pdf)

                skill = st.text_input("Skills", value=", ".join(st.session_state.resume_skills))
                city = st.selectbox("Preferred City", ["All"] + sorted(df["location"].dropna().unique()))

                # Initialize search state in session
                if 'search_performed' not in st.session_state:
                    st.session_state.search_performed = False
                if 'search_results' not in st.session_state:
                    st.session_state.search_results = pd.DataFrame()
                if 'applied_titles_cache' not in st.session_state:
                    st.session_state.applied_titles_cache = []

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
                    st.session_state.applied_titles_cache = applied_titles
                except:
                    applied_titles = st.session_state.applied_titles_cache

                results = results.copy()
                # Enhanced scoring for search results including skill matching
                user_skills = st.session_state.resume_skills if st.session_state.resume_skills else []

                def calculate_search_score(row):
                    base_score = row["stipend"] * 0.01 + row["company_score"] * 10 + row["is_remote"] * 5

                    # Add skill matching score if user has skills
                    skill_score = 0
                    if user_skills and pd.notna(row.get('skills_required')):
                        job_skills = set(str(row['skills_required']).split(', '))
                        matched_skills = len(set(user_skills).intersection(job_skills))
                        total_job_skills = len(job_skills)
                        if total_job_skills > 0:
                            skill_score = (matched_skills / total_job_skills) * 50  # Up to 50 points for perfect skill match

                    return base_score + skill_score

                results["score"] = results.apply(calculate_search_score, axis=1)
                results["skill_score"] = results.apply(
                    lambda row: round(calculate_skill_score_only(row, user_skills), 2) if user_skills else 0,
                    axis=1
                )

                # Filter out already applied internships
                results = results[~results["title"].str.lower().isin(applied_titles)]

                # Show top internships
                results = results.sort_values("score", ascending=False)

                # Handle search button click
                search_clicked = st.button("🔎 Find Internships", key="search_button")

                if search_clicked or st.session_state.search_performed:
                    if search_clicked:
                        # New search - perform the search and store results
                        st.session_state.search_performed = True
                        st.session_state.current_page = 0

                        # Perform the search
                        keywords = [k.strip().lower() for k in skill.split(",") if k.strip()]
                        results = df if not keywords else df[
                            df["description"].str.lower().apply(lambda x: any(k in x for k in keywords))
                        ]
                        if city != "All":
                            results = results[results["location"].str.contains(city, case=False)]

                        # Enhanced scoring for search results including skill matching
                        user_skills = st.session_state.resume_skills if st.session_state.resume_skills else []

                        def calculate_search_score(row):
                            base_score = row["stipend"] * 0.01 + row["company_score"] * 10 + row["is_remote"] * 5

                            # Add skill matching score if user has skills
                            skill_score = 0
                            if user_skills and pd.notna(row.get('skills_required')):
                                job_skills = set(str(row['skills_required']).split(', '))
                                matched_skills = len(set(user_skills).intersection(job_skills))
                                total_job_skills = len(job_skills)
                                if total_job_skills > 0:
                                    skill_score = (matched_skills / total_job_skills) * 50  # Up to 50 points for perfect skill match

                            return base_score + skill_score

                        results = results.copy()
                        results["score"] = results.apply(calculate_search_score, axis=1)
                        results["skill_score"] = results.apply(
                            lambda row: round(calculate_skill_score_only(row, user_skills), 2) if user_skills else 0,
                            axis=1
                        )

                        # Filter out already applied internships
                        results = results[~results["title"].str.lower().isin(applied_titles)]

                        # Store results in session state
                        st.session_state.search_results = results.sort_values("score", ascending=False)

                    # Use stored results for display
                    display_results = st.session_state.search_results

                    st.markdown(f"<h3>🎯 Found {len(display_results)} internships matching your criteria</h3>", unsafe_allow_html=True)

                    # Pagination setup
                    items_per_page = 10
                    total_pages = (len(display_results) + items_per_page - 1) // items_per_page  # Ceiling division

                    if 'current_page' not in st.session_state:
                        st.session_state.current_page = 0

                    # Ensure current_page is within bounds
                    if st.session_state.current_page >= total_pages:
                        st.session_state.current_page = max(0, total_pages - 1)
                    if st.session_state.current_page < 0:
                        st.session_state.current_page = 0

                    # Display internships for current page
                    start_idx = st.session_state.current_page * items_per_page
                    end_idx = start_idx + items_per_page
                    page_results = display_results.iloc[start_idx:end_idx]

                    for i, j in page_results.iterrows():
                        display_internship_card(j, f"{st.session_state.current_page}_{i}", st.session_state.applied_titles_cache)

                    # Pagination controls at the bottom
                    if total_pages > 1:
                        st.markdown("---")  # Separator
                        col1, col2, col3 = st.columns([1, 2, 1])
                        with col1:
                            if st.button("⬅️ Previous", disabled=st.session_state.current_page == 0, key="prev_page"):
                                st.session_state.current_page -= 1
                                st.rerun()
                        with col2:
                            st.markdown(f"**Page {st.session_state.current_page + 1} of {total_pages}**")
                        with col3:
                            if st.button("Next ➡️", disabled=st.session_state.current_page >= total_pages - 1, key="next_page"):
                                st.session_state.current_page += 1
                                st.rerun()

                        # Page number buttons
                        cols = st.columns(min(10, total_pages))  # Max 10 buttons
                        for i in range(total_pages):
                            if i < 10:  # Only show first 10 pages
                                with cols[i % len(cols)]:
                                    if st.button(f"{i+1}", key=f"page_{i}", help=f"Go to page {i+1}"):
                                        st.session_state.current_page = i
                                        st.rerun()

                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<h3>🔍 Enter skills and click 'Find Internships' to search</h3>", unsafe_allow_html=True)

            with tab2:
                # Back button for recommendations
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("⬅️ Back to Search", type="secondary", use_container_width=True, key="back_to_search_from_recommendations"):
                        # Switch to search tab (tab1)
                        st.rerun()  # This will refresh and user can click the search tab
                with col2:
                    st.markdown("### 🤖 AI-Powered Recommendations")
                    st.caption("Get personalized internship matches based on your skills and preferences")

                st.markdown("<div class='card'>", unsafe_allow_html=True)

                # User preferences form
                col1, col2 = st.columns(2)

                with col1:
                    pref_location = st.selectbox("Preferred Location",
                                               ["Any"] + sorted(df["location"].dropna().unique()),
                                               key="pref_location")
                    pref_domain = st.selectbox("Preferred Domain",
                                             ["Any", "Technology", "Finance", "Marketing", "HR", "Operations"],
                                             key="pref_domain")
                    min_stipend = st.slider("Minimum Stipend (₹)", 0, 50000, 5000, key="min_stipend")

                with col2:
                    remote_pref = st.checkbox("Prefer Remote Work", key="remote_pref")
                    experience_level = st.selectbox("Experience Level",
                                                  ["Entry Level", "Intermediate", "Advanced"],
                                                  key="experience_level")

                # Get user skills
                user_skills = st.session_state.resume_skills
                if not user_skills:
                    st.warning("⚠️ Please upload your resume in the Search tab to get better recommendations.")
                    user_skills = []

                # Get applications history for collaborative filtering
                try:
                    engine = db()
                    if 'postgresql' in str(engine.url):
                        user_apps = pd.read_sql("""
                            SELECT job_title, company, location
                            FROM applications
                            WHERE LOWER(username)=%(username)s
                        """, engine, params={'username': current_user()})
                    else:
                        user_apps = pd.read_sql_query("""
                            SELECT job_title, company, location
                            FROM applications
                            WHERE LOWER(username)=LOWER(?)
                        """, engine, params=(current_user(),))
                except:
                    user_apps = pd.DataFrame()

                if st.button("🎯 Get AI Recommendations", type="primary"):
                    with st.spinner("🤖 Analyzing your profile and finding best matches..."):
                        # Create user profile
                        user_preferences = {
                            'location': pref_location if pref_location != "Any" else "",
                            'domain': pref_domain if pref_domain != "Any" else "",
                            'min_stipend': min_stipend,
                            'max_stipend': 100000,  # High upper limit
                            'remote': remote_pref,
                            'experience': experience_level.lower().replace(" ", "_")
                        }

                        # Get personalized recommendations
                        recommendations = get_personalized_recommendations(
                            user_skills, user_preferences, df, user_apps
                        )

                        if not recommendations.empty:
                            st.success(f"🎉 Found {len(recommendations)} personalized recommendations!")

                            # Pagination for recommendations
                            rec_items_per_page = 10
                            rec_total_pages = (len(recommendations) + rec_items_per_page - 1) // rec_items_per_page

                            if 'rec_current_page' not in st.session_state:
                                st.session_state.rec_current_page = 0

                            # Ensure rec_current_page is within bounds
                            if st.session_state.rec_current_page >= rec_total_pages:
                                st.session_state.rec_current_page = rec_total_pages - 1
                            if st.session_state.rec_current_page < 0:
                                st.session_state.rec_current_page = 0

                            # Display recommendations for current page
                            rec_start_idx = st.session_state.rec_current_page * rec_items_per_page
                            rec_end_idx = rec_start_idx + rec_items_per_page
                            page_recommendations = recommendations.iloc[rec_start_idx:rec_end_idx]

                            for idx, rec in page_recommendations.iterrows():
                                display_recommendation_card(rec, f"rec_{st.session_state.rec_current_page}_{idx}", applied_titles)

                            # Pagination controls at the bottom for recommendations
                            if rec_total_pages > 1:
                                st.markdown("---")  # Separator
                                col1, col2, col3 = st.columns([1, 2, 1])
                                with col1:
                                    if st.button("⬅️ Previous", disabled=st.session_state.rec_current_page == 0, key="rec_prev_page"):
                                        st.session_state.rec_current_page -= 1
                                        st.rerun()
                                with col2:
                                    st.markdown(f"**Page {st.session_state.rec_current_page + 1} of {rec_total_pages}**")
                                with col3:
                                    if st.button("Next ➡️", disabled=st.session_state.rec_current_page >= rec_total_pages - 1, key="rec_next_page"):
                                        st.session_state.rec_current_page += 1
                                        st.rerun()

                                # Page number buttons for recommendations
                                rec_cols = st.columns(min(10, rec_total_pages))
                                for i in range(rec_total_pages):
                                    if i < 10:  # Only show first 10 pages
                                        with rec_cols[i % len(rec_cols)]:
                                            if st.button(f"{i+1}", key=f"rec_page_{i}", help=f"Go to page {i+1}"):
                                                st.session_state.rec_current_page = i
                                                st.rerun()
                        else:
                            st.info("🤔 No recommendations found. Try adjusting your preferences or upload a resume with more skills.")

                st.markdown("</div>", unsafe_allow_html=True)

            with tab3:
                # Back button for applications
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("⬅️ Back to Search", type="secondary", use_container_width=True, key="back_to_search_from_applications"):
                        # Switch to search tab (tab1)
                        st.rerun()  # This will refresh and user can click the search tab
                with col2:
                    st.markdown("### 📋 My Applications")
                    st.caption("Track all your internship applications")

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

                if not apps.empty:
                    st.markdown(f"<h3>📋 Your Applications ({len(apps)} total)</h3>", unsafe_allow_html=True)
                    st.dataframe(apps, width='stretch')

                    # Application statistics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Applied", len(apps))
                    with col2:
                        unique_companies = apps['company'].nunique()
                        st.metric("Companies Applied To", unique_companies)
                    with col3:
                        if 'applied_at' in apps.columns:
                            latest_app = pd.to_datetime(apps['applied_at']).max()
                            st.metric("Last Application", latest_app.strftime('%Y-%m-%d'))
                else:
                    st.info("📝 You haven't applied to any internships yet. Start exploring opportunities!")

                st.markdown("</div>", unsafe_allow_html=True)

        # ================= ADMIN =================
        elif st.session_state.role == "Admin":
            from src.admin_dashboard import show_admin_dashboard
            show_admin_dashboard()

# ================= MAIN GUARD =================
if __name__ == "__main__":
    main()
