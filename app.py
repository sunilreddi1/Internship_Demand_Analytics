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
if "applications" not in st.session_state:
    st.session_state.applications = {}

# =====================================================
# LOAD DATASET
# =====================================================
@st.cache_data
def load_dataset():
    df = pd.read_csv("adzuna_internships_raw.csv")
    df.columns = df.columns.str.lower()

    # Normalize column names safely
    if "job_title" in df.columns:
        df["title"] = df["job_title"]
    if "company_name" in df.columns:
        df["company"] = df["company_name"]
    if "city" in df.columns:
        df["location"] = df["city"]
    if "salary_min" in df.columns:
        df["stipend"] = df["salary_min"].fillna(15000)
    if "description" not in df.columns:
        df["description"] = "Internship opportunity"

    if "company_logo" not in df.columns and "logo" in df.columns:
        df["company_logo"] = df["logo"]

    # Fallbacks
    df["location"] = df.get("location", "India")
    df["stipend"] = df.get("stipend", 15000)

    return df

data = load_dataset()

# =====================================================
# LIVE LOCATION (IP)
# =====================================================
def get_live_location():
    try:
        r = requests.get("https://ipapi.co/json/", timeout=4).json()
        return r.get("city", "India")
    except:
        return "India"

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

def compute_match(stipend, skill_match, location_match):
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
    user = st.text_input("Username")
    role = st.selectbox("Role", ["Student", "Admin"])
    if st.button("Login"):
        if user:
            st.session_state.user = user
            st.session_state.role = role
            go("dashboard")
    st.markdown("</div>", unsafe_allow_html=True)

# =====================================================
# DASHBOARD
# =====================================================
elif st.session_state.page == "dashboard":
    city = get_live_location()

    st.markdown("""
    <div class="header">
        <h1>🚀 Internship Dashboard</h1>
        <p>Search • Match • Apply</p>
    </div>
    """, unsafe_allow_html=True)

    st.info(f"📍 Detected Location: {city}")

    skill = st.text_input("🔎 Skill (Python, Data, Web, ML)")
    resume = st.file_uploader("📄 Upload Resume (PDF)", type="pdf")

    extracted = []
    if resume:
        reader = PdfReader(resume)
        text = " ".join([p.extract_text() or "" for p in reader.pages]).lower()
        extracted = [s for s in ["python","data","ml","web","sql","java"] if s in text]
        st.success(f"Extracted Skills: {', '.join(extracted)}")

    if st.button("Search Internships"):
        st.session_state.search_skill = skill.lower()
        st.session_state.resume_skills = extracted
        st.session_state.city = city.lower()
        go("results")

# =====================================================
# RESULTS
# =====================================================
elif st.session_state.page == "results":
    st.markdown("""
    <div class="header">
        <h1>🎯 Recommended Internships</h1>
        <p>Skill & Location Based Ranking</p>
    </div>
    """, unsafe_allow_html=True)

    results = []

    for _, row in data.iterrows():
        desc = str(row["description"]).lower()
        skill_match = 1 if st.session_state.search_skill in desc else 0.5
        location_match = 1 if st.session_state.city in str(row["location"]).lower() else 0.6

        score = compute_match(
            int(row["stipend"]),
            skill_match,
            location_match
        )

        results.append({
            "title": row["title"],
            "company": row["company"],
            "location": row["location"],
            "stipend": int(row["stipend"]),
            "description": row["description"][:300] + "...",
            "logo": row.get("company_logo", ""),
            "score": score
        })

    results = sorted(results, key=lambda x: x["score"], reverse=True)[:12]

    for r in results:
        st.markdown("<div class='card'>", unsafe_allow_html=True)

        if r["logo"]:
            st.image(r["logo"], width=80)

        st.subheader(r["title"])
        st.write(f"🏢 **{r['company']}**")
        st.write(f"📍 {r['location']}")
        st.write(f"💰 ₹{r['stipend']}")
        st.write(f"🎯 Match Score: **{r['score']}%**")
        st.write(r["description"])

        job_id = f"{r['title']}@{r['company']}"
        if job_id not in st.session_state.applications:
            if st.button(f"Apply – {r['title']}", key=job_id):
                st.session_state.applications[job_id] = {
                    "student": st.session_state.user,
                    "status": "Pending"
                }
                st.success("Application submitted")
        else:
            st.info(f"Status: {st.session_state.applications[job_id]['status']}")

        st.markdown("</div>", unsafe_allow_html=True)

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
        for job, d in st.session_state.applications.items():
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.write(f"Internship: {job}")
            st.write(f"Student: {d['student']}")
            d["status"] = st.selectbox(
                "Status",
                ["Pending", "Selected"],
                index=["Pending","Selected"].index(d["status"]),
                key=job
            )
            st.markdown("</div>", unsafe_allow_html=True)
