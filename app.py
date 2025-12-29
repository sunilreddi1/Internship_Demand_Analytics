import streamlit as st
import pandas as pd
import requests
import time
from PyPDF2 import PdfReader

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Internship Portal",
    page_icon="🎓",
    layout="wide"
)

# ================= SESSION =================
if "page" not in st.session_state:
    st.session_state.page = "login"
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = "Student"
if "dark" not in st.session_state:
    st.session_state.dark = False

# ================= UI THEME =================
def theme():
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
        background: {bg};
        color:{text};
    }}
    .card {{
        background:{card};
        padding:22px;
        border-radius:18px;
        margin-bottom:20px;
        box-shadow:0 15px 35px rgba(0,0,0,0.15);
    }}
    .header {{
        background:linear-gradient(90deg,#0a66c2,#6a11cb,#ff6a88);
        padding:30px;
        border-radius:20px;
        color:white;
        box-shadow:0 20px 40px rgba(0,0,0,0.3);
    }}
    </style>
    """, unsafe_allow_html=True)

theme()

# ================= HELPERS =================
def go(page):
    st.session_state.page = page
    st.rerun()

def toast(msg, icon="✨"):
    st.toast(msg, icon=icon)

# ================= SIDEBAR =================
with st.sidebar:
    st.markdown("## 🎓 Internship Portal")
    st.toggle("🌙 Dark Mode", key="dark")
    if st.session_state.user:
        st.success(f"👤 {st.session_state.user}")
        st.info(f"Role: {st.session_state.role}")
        if st.button("🚪 Logout"):
            st.session_state.user = None
            go("login")

# ================= LOGIN / REGISTER =================
if st.session_state.page == "login":
    st.markdown("<div class='header'><h1>Welcome 👋</h1><p>Find real internships smartly</p></div>", unsafe_allow_html=True)

    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        choice = st.radio("Choose", ["Login", "Register"])

        user = st.text_input("Username", key="u1")
        pwd = st.text_input("Password", type="password", key="p1")
        role = st.selectbox("Role", ["Student", "Admin"])

        if choice == "Login":
            if st.button("Login"):
                if user and pwd:
                    st.session_state.user = user
                    st.session_state.role = role
                    toast("Login Successful 🎉")
                    go("dashboard")
        else:
            if st.button("Register"):
                toast("Registered successfully 🎉")
                st.session_state.user = user
                st.session_state.role = role
                go("dashboard")

        st.markdown("</div>", unsafe_allow_html=True)

# ================= DASHBOARD =================
elif st.session_state.page == "dashboard":
    st.markdown("<div class='header'><h1>Internship Dashboard</h1></div>", unsafe_allow_html=True)

    skill = st.text_input("🔍 Skill (Python, Web, Data Science)")
    location = st.selectbox("📍 Location", ["India", "Remote"])

    resume = st.file_uploader("📄 Upload Resume (PDF)", type="pdf")

    extracted_skills = []
    if resume:
        reader = PdfReader(resume)
        text = " ".join([p.extract_text() or "" for p in reader.pages]).lower()
        for s in ["python","data","ml","web","sql","java"]:
            if s in text:
                extracted_skills.append(s)

        st.success(f"Extracted Skills: {', '.join(extracted_skills)}")

    if st.button("🔎 Search Internships"):
        toast("Fetching internships...", "🚀")
        time.sleep(1)
        go("results")

# ================= RESULTS =================
elif st.session_state.page == "results":
    st.markdown("<div class='header'><h1>Recommended Internships</h1></div>", unsafe_allow_html=True)

    internships = [
        {"title":"Python Intern","company":"Google","stipend":25000},
        {"title":"Data Analyst Intern","company":"Amazon","stipend":20000},
        {"title":"Web Intern","company":"Infosys","stipend":15000}
    ]

    # ML-like ranking
    for i in internships:
        i["score"] = i["stipend"] / 300

    internships = sorted(internships, key=lambda x: x["score"], reverse=True)

    for i in internships:
        st.markdown(f"""
        <div class='card'>
        <h3>{i['title']}</h3>
        <p>🏢 {i['company']}</p>
        <p>💰 ₹{i['stipend']}</p>
        <p>🎯 Match Score: {round(i['score']*100,2)}%</p>
        </div>
        """, unsafe_allow_html=True)

    if st.button("⬅ Back"):
        go("dashboard")

# ================= ADMIN DASHBOARD =================
if st.session_state.user and st.session_state.role == "Admin":
    st.markdown("<div class='header'><h1>Admin Analytics</h1></div>", unsafe_allow_html=True)

    df = pd.DataFrame({
        "Skill":["Python","Web","Data"],
        "Demand":[120,90,150]
    })

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.bar_chart(df.set_index("Skill"))
    st.markdown("</div>", unsafe_allow_html=True)
