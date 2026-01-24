import streamlit as st
import pandas as pd
import psycopg2
import bcrypt
import numpy as np
import re
import PyPDF2
from sqlalchemy import create_engine, text
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
    try:
        # Try to create and test PostgreSQL connection
        engine = create_engine(st.secrets["db"]["url"])
        # Test the connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception as e:
        # Fallback to local SQLite for development (silent fallback)
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

def display_internship_card(job_data, index, applied_titles):
    """Display a single internship card with apply functionality"""
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    st.markdown(f"""
    <div class='title'>{job_data['title']}</div>
    <div class='sub'>🏢 {job_data['company']} | 📍 {job_data['location']}</div>
    💰 ₹{int(job_data['stipend'])}
    <span class='badge'>Match Score {int(job_data['score'])}</span>
    """, unsafe_allow_html=True)

    # Show skills if available
    if 'skills_required' in job_data and job_data['skills_required']:
        skills = job_data['skills_required'][:100] + "..." if len(job_data['skills_required']) > 100 else job_data['skills_required']
        st.caption(f"🎯 Skills: {skills}")

    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("📖 View Details", key=f"details_{index}"):
            with st.expander("Job Details", expanded=True):
                st.write("**Description:**")
                st.write(job_data.get('description', 'No description available')[:500] + "...")
                if 'category' in job_data:
                    st.write(f"**Category:** {job_data['category']}")
                if 'is_remote' in job_data:
                    st.write(f"**Remote Work:** {'Yes' if job_data['is_remote'] else 'No'}")

    with col2:
        if st.button("Apply 🚀", key=f"apply_{index}"):
            apply_for_job(job_data)

    st.markdown("</div>", unsafe_allow_html=True)

def display_recommendation_card(job_data, index, applied_titles):
    """Display a recommendation card with enhanced information"""
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    # Recommendation score indicator
    score = job_data.get('recommendation_score', 0)
    if score >= 80:
        score_color = "🟢"
        score_text = "Excellent Match"
    elif score >= 60:
        score_color = "🟡"
        score_text = "Good Match"
    else:
        score_color = "🟠"
        score_text = "Fair Match"

    st.markdown(f"""
    <div class='title'>{job_data['title']}</div>
    <div class='sub'>🏢 {job_data['company']} | 📍 {job_data['location']}</div>
    💰 ₹{int(job_data.get('stipend', 0))} | {score_color} {score_text}
    <span class='badge'>AI Score: {score:.1f}/100</span>
    """, unsafe_allow_html=True)

    # Show why this recommendation
    content_score = job_data.get('content_score', 0)
    collab_score = job_data.get('collaborative_score', 0)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption(f"🎯 Skills Match: {content_score:.1f}")
    with col2:
        st.caption(f"👥 Popularity: {collab_score:.1f}")
    with col3:
        if st.button("Apply 🚀", key=f"rec_apply_{index}"):
            apply_for_job(job_data)

    st.markdown("</div>", unsafe_allow_html=True)

def apply_for_job(job_data):
    """Handle job application"""
    try:
        engine = db()
        with engine.connect() as conn:
            # Get raw connection for cursor operations
            raw_conn = conn.connection if hasattr(conn, 'connection') else conn
            cur = raw_conn.cursor()

            if 'postgresql' in str(engine.url):
                cur.execute(
                    "INSERT INTO applications (username,job_title,company,location) VALUES (%s,%s,%s,%s)",
                    (current_user(), job_data["title"], job_data["company"], job_data["location"])
                )
            else:  # SQLite - check schema and adapt
                # Check if table has correct columns
                cur.execute("PRAGMA table_info(applications)")
                columns = [col[1] for col in cur.fetchall()]
                if 'job_title' in columns:
                    cur.execute(
                        "INSERT INTO applications (username,job_title,company,location) VALUES (?,?,?,?)",
                        (current_user(), job_data["title"], job_data["company"], job_data["location"])
                    )
                else:
                    # Use existing schema
                    cur.execute(
                        "INSERT INTO applications (username,job_id,status) VALUES (?,?,?)",
                        (current_user(), job_data["title"], "Applied")
                    )
            raw_conn.commit()
        st.success("🎉 Applied successfully!")
        st.rerun()
    except Exception as e:
        st.error(f"Application failed: {e}")

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
        from src.recommender import get_personalized_recommendations

        tab1, tab2, tab3 = st.tabs(["🔎 Smart Search", "🎯 AI Recommendations", "📋 My Applications"])

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
            # Use basic scoring for search results
            results["score"] = results["stipend"] * 0.01 + results["company_score"] * 10 + results["is_remote"] * 5

            # Filter out already applied internships
            results = results[~results["title"].str.lower().isin(applied_titles)]

            if st.button("🔎 Find Internships"):
                st.markdown(f"<h3>🎯 Found {len(results)} internships matching your criteria</h3>", unsafe_allow_html=True)
            else:
                st.markdown(f"<h3>🎯 Showing internships ({len(results)} total)</h3>", unsafe_allow_html=True)

            # Pagination
            items_per_page = 10
            total_pages = (len(results) + items_per_page - 1) // items_per_page  # Ceiling division

            if 'current_page' not in st.session_state:
                st.session_state.current_page = 0

            if total_pages > 1:
                col1, col2, col3 = st.columns([1, 2, 1])
                with col1:
                    if st.button("⬅️ Previous", disabled=st.session_state.current_page == 0):
                        st.session_state.current_page -= 1
                        st.rerun()
                with col2:
                    st.markdown(f"**Page {st.session_state.current_page + 1} of {total_pages}**")
                with col3:
                    if st.button("Next ➡️", disabled=st.session_state.current_page >= total_pages - 1):
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
            else:
                st.session_state.current_page = 0

            start_idx = st.session_state.current_page * items_per_page
            end_idx = start_idx + items_per_page
            page_results = results.sort_values("score", ascending=False).iloc[start_idx:end_idx]

            for i, j in page_results.iterrows():
                display_internship_card(j, f"{st.session_state.current_page}_{i}", applied_titles)

            st.markdown("</div>", unsafe_allow_html=True)

        with tab2:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("### 🤖 AI-Powered Recommendations")
            st.markdown("Get personalized internship matches based on your skills, preferences, and application history.")

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

                        # Display recommendations
                        for idx, rec in recommendations.iterrows():
                            display_recommendation_card(rec, idx, applied_titles)
                    else:
                        st.info("🤔 No recommendations found. Try adjusting your preferences or upload a resume with more skills.")

            st.markdown("</div>", unsafe_allow_html=True)

        with tab3:
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
if st.session_state.role == "Admin":
    from src.admin_dashboard import show_admin_dashboard
    show_admin_dashboard()
