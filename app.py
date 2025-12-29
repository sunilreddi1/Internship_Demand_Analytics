import streamlit as st
import pandas as pd
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

# Applied jobs structure:
# { job_id : {"student": username, "status": "Pending"} }
if "applications" not in st.session_state:
    st.session_state.applications = {}

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
        box-shadow:0 20px 40px rgba(0,0,0,0.3);
    }}
    .card {{
        background:{card};
        padding:22px;
        border-radius:18px;
        margin-bottom:20px;
        box-shadow:0 15px 35px rgba(0,0,0,0.15);
        animation:fade 0.6s ease;
    }}
    @keyframes fade {{
        from {{opacity:0; transform:translateY(20px);}}
        to {{opacity:1; transform:translateY(0);}}
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

def prototype_matching_score(stipend):
    return round((stipend / 30000) * 100, 2)

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
# LOGIN / REGISTER
# =====================================================
if st.session_state.page == "login":
    st.markdown("""
    <div class="header">
        <h1>Welcome 👋</h1>
        <p>Internship Demand & Recommendation System</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    mode = st.radio("Choose", ["Login", "Register"])
    username = st.text_input("👤 Username")
    password = st.text_input("🔑 Password", type="password")
    role = st.selectbox("Role", ["Student", "Admin"])

    if st.button(mode):
        if username and password:
            st.session_state.user = username
            st.session_state.role = role
            toast(f"{mode} successful 🎉")
            go("dashboard")
        else:
            st.error("Fill all fields")
    st.markdown("</div>", unsafe_allow_html=True)

# =====================================================
# DASHBOARD
# =====================================================
elif st.session_state.page == "dashboard":
    st.markdown("""
    <div class="header">
        <h1>🚀 Internship Dashboard</h1>
        <p>Search • Match • Apply</p>
    </div>
    """, unsafe_allow_html=True)

    applied_count = sum(
        1 for a in st.session_state.applications.values()
        if a["student"] == st.session_state.user
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📨 Applications", applied_count)
    c2.metric("💰 Avg Stipend", "₹18,000")
    c3.metric("🔥 Top Skill", "Python")
    c4.metric("🎯 Avg Match", "86%")

    skill = st.text_input("🔎 Skill")
    location = st.selectbox("📍 Location", ["India", "Remote"])

    resume = st.file_uploader("📄 Upload Resume (PDF)", type="pdf")
    if resume:
        reader = PdfReader(resume)
        text = " ".join([p.extract_text() or "" for p in reader.pages]).lower()
        skills = [s for s in ["python","data","ml","web","sql","java"] if s in text]
        st.success(f"Extracted Skills: {', '.join(skills)}")

    if st.button("Search Internships 🚀"):
        go("results")

# =====================================================
# RESULTS + APPLY
# =====================================================
elif st.session_state.page == "results":
    st.markdown("""
    <div class="header">
        <h1>🎯 Recommended Internships</h1>
        <p>Apply directly from the portal</p>
    </div>
    """, unsafe_allow_html=True)

    internships = [
        {"title":"Python Intern","company":"Google","stipend":25000},
        {"title":"Data Analyst","company":"Amazon","stipend":20000},
        {"title":"Web Intern","company":"Infosys","stipend":15000},
    ]

    for i in internships:
        i["score"] = prototype_matching_score(i["stipend"])

    internships = sorted(internships, key=lambda x: x["score"], reverse=True)

    for i in internships:
        job_id = f"{i['title']}@{i['company']}"

        st.markdown(f"""
        <div class="card">
            <h3>{i['title']}</h3>
            <p>🏢 {i['company']}</p>
            <p>💰 ₹{i['stipend']}</p>
            <p>🎯 Match Score: {i['score']}%</p>
        </div>
        """, unsafe_allow_html=True)

        if job_id in st.session_state.applications:
            status = st.session_state.applications[job_id]["status"]
            st.info(f"📌 Status: {status}")
        else:
            if st.button(f"Apply Now – {i['title']}", key=job_id):
                st.session_state.applications[job_id] = {
                    "student": st.session_state.user,
                    "status": "Pending"
                }
                toast("Application submitted 🎉", "📨")

    if st.button("⬅ Back"):
        go("dashboard")

# =====================================================
# ADMIN VIEW – APPLIED STUDENTS
# =====================================================
if st.session_state.user and st.session_state.role == "Admin":
    st.markdown("""
    <div class="header">
        <h1>📊 Admin – Applications Review</h1>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.applications:
        st.info("No applications yet")
    else:
        for job_id, data in st.session_state.applications.items():
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.write(f"📌 Internship: {job_id}")
            st.write(f"👤 Student: {data['student']}")

            new_status = st.selectbox(
                "Update Status",
                ["Pending", "Selected"],
                index=["Pending","Selected"].index(data["status"]),
                key=job_id
            )

            st.session_state.applications[job_id]["status"] = new_status
            st.markdown("</div>", unsafe_allow_html=True)
