import streamlit as st
import pandas as pd
import requests
import time
from PyPDF2 import PdfReader

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Internship Demand & Recommendation Portal",
    page_icon="🎓",
    layout="wide"
)

# =====================================================
# SESSION STATE
# =====================================================
if "page" not in st.session_state:
    st.session_state.page = "login"
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = "Student"
if "dark" not in st.session_state:
    st.session_state.dark = False
if "location" not in st.session_state:
    st.session_state.location = None
if "applications" not in st.session_state:
    st.session_state.applications = {}

# =====================================================
# LOAD DATASET
# =====================================================
@st.cache_data
def load_dataset():
    df = pd.read_csv("adzuna_internships_raw.csv")
    df.columns = df.columns.str.lower()

    if "title" not in df.columns:
        df["title"] = df.get("job_title", "Internship")
    if "company" not in df.columns:
        df["company"] = df.get("company_name", "Company")
    if "location" not in df.columns:
        df["location"] = df.get("city", "India")
    if "stipend" not in df.columns:
        df["stipend"] = 15000
    if "skills" not in df.columns:
        df["skills"] = "python,data,web"

    return df

data = load_dataset()

# =====================================================
# LIVE LOCATION (IP BASED)
# =====================================================
def get_live_location():
    try:
        res = requests.get("https://ipapi.co/json/", timeout=5).json()
        return {
            "city": res.get("city", "Unknown"),
            "country": res.get("country_name", "India")
        }
    except:
        return {"city": "Unknown", "country": "India"}

# =====================================================
# THEME (EXACT BACKGROUND YOU ASKED)
# =====================================================
def apply_theme():
    if st.session_state.dark:
        bg = "linear-gradient(135deg,#0f172a,#020617)"
        card = "rgba(30,41,59,0.95)"
        text = "white"
    else:
        bg = "linear-gradient(135deg,#f3e8ff,#ddd6fe,#bfdbfe)"
        card = "rgba(255,255,255,0.88)"
        text = "#0f172a"

    st.markdown(f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background:{bg};
        color:{text};
    }}
    .header {{
        background:linear-gradient(90deg,#2563eb,#7c3aed,#ec4899);
        padding:30px;
        border-radius:22px;
        color:white;
        margin-bottom:25px;
        box-shadow:0 25px 50px rgba(0,0,0,0.25);
    }}
    .card {{
        background:{card};
        backdrop-filter: blur(10px);
        padding:22px;
        border-radius:20px;
        margin-bottom:20px;
        box-shadow:0 15px 35px rgba(0,0,0,0.18);
        animation:fadeUp 0.6s ease;
    }}
    @keyframes fadeUp {{
        from {{opacity:0; transform:translateY(18px);}}
        to {{opacity:1; transform:translateY(0);}}
    }}
    button {{
        background:linear-gradient(90deg,#2563eb,#7c3aed)!important;
        color:white!important;
        border-radius:12px!important;
        font-weight:600!important;
    }}
    section[data-testid="stSidebar"] {{
        background:linear-gradient(180deg,#f5f3ff,#e0e7ff);
    }}
    </style>
    """, unsafe_allow_html=True)

apply_theme()

# =====================================================
# HELPERS
# =====================================================
def go(page):
    st.session_state.page = page
    st.rerun()

def toast(msg, icon="✨"):
    st.toast(msg, icon=icon)

def match_score(stipend, skill_match, location_match):
    return round(
        (0.5 * (stipend / 30000) +
         0.3 * skill_match +
         0.2 * location_match) * 100, 2
    )

# =====================================================
# SIDEBAR
# =====================================================
with st.sidebar:
    st.markdown("## 🎓 Internship Portal")
    st.toggle("🌙 Dark Mode", key="dark")
    st.markdown("---")
    if st.session_state.user:
        st.success(f"👤 {st.session_state.user}")
        st.info(f"Role: {st.session_state.role}")
        if st.button("🚪 Logout"):
            st.session_state.user = None
            go("login")

# =====================================================
# LOGIN
# =====================================================
if st.session_state.page == "login":
    st.markdown("""
    <div class="header">
        <h1>Welcome 👋</h1>
        <p>Internship Demand & Recommendation System</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    username = st.text_input("👤 Username")
    password = st.text_input("🔑 Password", type="password")
    role = st.selectbox("Role", ["Student", "Admin"])

    if st.button("Login"):
        if username and password:
            st.session_state.user = username
            st.session_state.role = role
            st.session_state.location = get_live_location()
            toast("Login successful 🎉")
            go("dashboard")
        else:
            st.error("Enter credentials")
    st.markdown("</div>", unsafe_allow_html=True)

# =====================================================
# DASHBOARD
# =====================================================
elif st.session_state.page == "dashboard":
    loc = st.session_state.location

    st.markdown("""
    <div class="header">
        <h1>🚀 Internship Dashboard</h1>
        <p>Search • Match • Apply</p>
    </div>
    """, unsafe_allow_html=True)

    st.info(f"📍 Detected Location: {loc['city']}, {loc['country']}")

    skill_input = st.text_input("🔍 Enter Skill (Python, Data, Web, ML)")
    resume = st.file_uploader("📄 Upload Resume (PDF)", type="pdf")

    extracted_skills = []
    if resume:
        reader = PdfReader(resume)
        text = " ".join([p.extract_text() or "" for p in reader.pages]).lower()
        extracted_skills = [s for s in ["python","data","ml","web","sql","java"] if s in text]
        st.success(f"Extracted Skills: {', '.join(extracted_skills)}")

    if st.button("Search Internships 🚀"):
        st.session_state.search_skill = skill_input or ",".join(extracted_skills)
        go("results")

# =====================================================
# RESULTS
# =====================================================
elif st.session_state.page == "results":
    user_city = st.session_state.location["city"].lower()
    search_skill = st.session_state.get("search_skill", "").lower()

    st.markdown("""
    <div class="header">
        <h1>🎯 Recommended Internships</h1>
        <p>Skill + Location + Stipend based ranking</p>
    </div>
    """, unsafe_allow_html=True)

    results = []
    for _, i in data.iterrows():
        skill_match = 1 if search_skill in i["skills"].lower() else 0.6
        location_match = 1 if user_city in str(i["location"]).lower() else 0.6
        score = match_score(i["stipend"], skill_match, location_match)

        results.append({
            "title": i["title"],
            "company": i["company"],
            "location": i["location"],
            "stipend": i["stipend"],
            "score": score
        })

    results = sorted(results, key=lambda x: x["score"], reverse=True)[:15]

    for r in results:
        job_id = f"{r['title']}@{r['company']}"
        st.markdown(f"""
        <div class="card">
            <h3>{r['title']}</h3>
            <p>🏢 {r['company']}</p>
            <p>📍 {r['location']}</p>
            <p>💰 ₹{r['stipend']}</p>
            <p>🎯 Match Score: {r['score']}%</p>
        </div>
        """, unsafe_allow_html=True)

        if job_id in st.session_state.applications:
            st.info(f"📌 Status: {st.session_state.applications[job_id]['status']}")
        else:
            if st.button(f"Apply – {r['title']}", key=job_id):
                st.session_state.applications[job_id] = {
                    "student": st.session_state.user,
                    "status": "Pending"
                }
                toast("Application submitted 🎉")

    if st.button("⬅ Back"):
        go("dashboard")

# =====================================================
# ADMIN VIEW
# =====================================================
if st.session_state.user and st.session_state.role == "Admin":
    st.markdown("""
    <div class="header">
        <h1>📊 Admin – Applications</h1>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.applications:
        st.info("No applications yet")
    else:
        for job_id, app in st.session_state.applications.items():
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.write(f"📌 Internship: {job_id}")
            st.write(f"👤 Student: {app['student']}")
            status = st.selectbox(
                "Status",
                ["Pending", "Selected"],
                index=["Pending","Selected"].index(app["status"]),
                key=job_id
            )
            st.session_state.applications[job_id]["status"] = status
            st.markdown("</div>", unsafe_allow_html=True)
