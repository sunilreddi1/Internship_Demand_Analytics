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

    # REQUIRED COLUMNS HANDLING
    if "title" not in df.columns:
        df["title"] = df["job_title"]
    if "company" not in df.columns:
        df["company"] = df["company_name"]
    if "location" not in df.columns:
        df["location"] = df["city"]

    if "stipend" not in df.columns:
        df["stipend"] = 15000  # fallback stipend

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
        return {
            "city": "Unknown",
            "country": "India"
        }

# =====================================================
# THEME
# =====================================================
def apply_theme():
    if st.session_state.dark:
        bg = "#0f172a"
        card = "#1e293b"
        text = "white"
    else:
        bg = "linear-gradient(135deg,#f5f7fa,#e0c3fc,#8ec5fc)"
        card = "#ffffff"
        text = "#111827"

    st.markdown(f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background:{bg};
        color:{text};
    }}
    .header {{
        background:linear-gradient(90deg,#0a66c2,#6a11cb,#ff6a88);
        padding:30px;
        border-radius:20px;
        color:white;
        margin-bottom:25px;
    }}
    .card {{
        background:{card};
        padding:22px;
        border-radius:18px;
        margin-bottom:20px;
        box-shadow:0 15px 35px rgba(0,0,0,0.15);
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

def compute_match_score(stipend, location_match):
    stipend_score = stipend / 30000
    location_score = 1 if location_match else 0.6
    return round((0.6 * stipend_score + 0.4 * location_score) * 100, 2)

# =====================================================
# SIDEBAR
# =====================================================
with st.sidebar:
    st.markdown("## 🎓 Internship Portal")
    st.toggle("🌙 Dark Mode", key="dark")
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
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    role = st.selectbox("Role", ["Student", "Admin"])

    if st.button("Login"):
        if username and password:
            st.session_state.user = username
            st.session_state.role = role
            st.session_state.location = get_live_location()
            go("dashboard")
        else:
            st.error("Enter credentials")
    st.markdown("</div>", unsafe_allow_html=True)

# =====================================================
# DASHBOARD
# =====================================================
elif st.session_state.page == "dashboard":
    loc = st.session_state.location or get_live_location()

    st.markdown("""
    <div class="header">
        <h1>🚀 Internship Dashboard</h1>
    </div>
    """, unsafe_allow_html=True)

    st.info(f"📍 Detected Location: {loc['city']}, {loc['country']}")

    resume = st.file_uploader("📄 Upload Resume (PDF)", type="pdf")
    if resume:
        reader = PdfReader(resume)
        text = " ".join([p.extract_text() or "" for p in reader.pages]).lower()
        skills = [s for s in ["python","data","ml","web","sql","java"] if s in text]
        st.success(f"Extracted Skills: {', '.join(skills)}")

    if st.button("Search Internships"):
        go("results")

# =====================================================
# RESULTS (DATASET + LIVE LOCATION)
# =====================================================
elif st.session_state.page == "results":
    loc = st.session_state.location
    user_city = loc["city"].lower()

    st.markdown("""
    <div class="header">
        <h1>🎯 Recommended Internships</h1>
        <p>Dataset-driven + Location-aware</p>
    </div>
    """, unsafe_allow_html=True)

    internships = data.to_dict("records")

    ranked = []
    for i in internships:
        city = str(i.get("location", "")).lower()
        stipend = int(i.get("stipend", 15000))
        location_match = user_city in city
        score = compute_match_score(stipend, location_match)
        i["score"] = score
        ranked.append(i)

    ranked = sorted(ranked, key=lambda x: x["score"], reverse=True)[:10]

    for i in ranked:
        job_id = f"{i['title']}@{i['company']}"

        st.markdown(f"""
        <div class="card">
            <h3>{i['title']}</h3>
            <p>🏢 {i['company']}</p>
            <p>📍 {i.get('location','N/A')}</p>
            <p>💰 ₹{i.get('stipend',15000)}</p>
            <p>🎯 Match Score: {i['score']}%</p>
        </div>
        """, unsafe_allow_html=True)

        if job_id in st.session_state.applications:
            st.info(f"📌 Status: {st.session_state.applications[job_id]['status']}")
        else:
            if st.button(f"Apply – {i['title']}", key=job_id):
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

    for job_id, datax in st.session_state.applications.items():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.write(f"Internship: {job_id}")
        st.write(f"Student: {datax['student']}")
        status = st.selectbox(
            "Status",
            ["Pending", "Selected"],
            index=["Pending","Selected"].index(datax["status"]),
            key=job_id
        )
        st.session_state.applications[job_id]["status"] = status
        st.markdown("</div>", unsafe_allow_html=True)
