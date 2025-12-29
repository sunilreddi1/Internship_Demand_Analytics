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

# =====================================================
# THEME (LIGHT / DARK)
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
    .logo-grid img {{
        width:90px;
        margin:12px;
        padding:10px;
        background:white;
        border-radius:14px;
        box-shadow:0 10px 25px rgba(0,0,0,0.2);
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

def prototype_matching_score(stipend, skill_weight=1):
    """
    Undergraduate-level prototype scoring function.
    Simulates regression-style relevance prediction.
    Can be replaced with a trained ML model in future.
    """
    return round((stipend / 30000) * 100 * skill_weight, 2)

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
    st.caption("Prototype-level system (Academic use)")

# =====================================================
# LOGIN / REGISTER (DEMO)
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
            st.error("Please fill all fields")

    st.markdown("</div>", unsafe_allow_html=True)

# =====================================================
# DASHBOARD
# =====================================================
elif st.session_state.page == "dashboard":
    st.markdown("""
    <div class="header">
        <h1>🚀 Internship Dashboard</h1>
        <p>Search • Match • Analyze Opportunities</p>
    </div>
    """, unsafe_allow_html=True)

    # KPI METRICS
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📌 Internships", "1,250+")
    c2.metric("💰 Avg Stipend", "₹18,000")
    c3.metric("🔥 Top Skill", "Python")
    c4.metric("🎯 Avg Match", "86%")

    tab1, tab2, tab3, tab4 = st.tabs(
        ["🔍 Search", "⭐ Recommendations", "📊 Insights", "🏢 Companies"]
    )

    # SEARCH TAB
    with tab1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        skill = st.text_input("🔎 Skill (Python, Web, Data Science)")
        location = st.selectbox("📍 Location", ["India", "Remote"])

        resume = st.file_uploader("📄 Upload Resume (PDF)", type="pdf")
        extracted_skills = []

        if resume:
            reader = PdfReader(resume)
            text = " ".join([p.extract_text() or "" for p in reader.pages]).lower()
            for s in ["python", "data", "ml", "web", "sql", "java"]:
                if s in text:
                    extracted_skills.append(s)
            st.success(f"Extracted Skills: {', '.join(extracted_skills)}")

        if st.button("Search Internships 🚀"):
            toast("Matching internships...", "🔎")
            time.sleep(1)
            go("results")

        st.markdown("</div>", unsafe_allow_html=True)

    # RECOMMENDATIONS TAB
    with tab2:
        internships = [
            ("ML Intern", "Microsoft", 30000, 1.2),
            ("Python Intern", "Google", 25000, 1.1),
            ("Data Analyst Intern", "Amazon", 20000, 1.0),
        ]

        for title, company, stipend, weight in internships:
            score = prototype_matching_score(stipend, weight)
            st.markdown(f"""
            <div class="card">
                <h3>{title}</h3>
                <p>🏢 {company}</p>
                <p>💰 ₹{stipend}</p>
                <p>🎯 Match Score: {score}%</p>
            </div>
            """, unsafe_allow_html=True)

    # INSIGHTS TAB
    with tab3:
        df = pd.DataFrame({
            "Skill": ["Python", "Web", "Data", "AI/ML"],
            "Demand": [120, 90, 110, 70]
        })
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.bar_chart(df.set_index("Skill"))
        st.caption("Skill-wise internship demand (demo analytics)")
        st.markdown("</div>", unsafe_allow_html=True)

    # COMPANIES TAB
    with tab4:
        st.markdown("""
        <div class="card">
            <h3>Top Hiring Companies</h3>
            <div class="logo-grid">
                <img src="https://logo.clearbit.com/google.com">
                <img src="https://logo.clearbit.com/amazon.com">
                <img src="https://logo.clearbit.com/microsoft.com">
                <img src="https://logo.clearbit.com/infosys.com">
                <img src="https://logo.clearbit.com/tcs.com">
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.caption(
        "⚠️ This system demonstrates an undergraduate-level predictive prototype. "
        "Advanced machine learning models can be integrated in future work."
    )

# =====================================================
# RESULTS PAGE
# =====================================================
elif st.session_state.page == "results":
    st.markdown("""
    <div class="header">
        <h1>🎯 Recommended Internships</h1>
        <p>Ranked using prototype relevance scoring</p>
    </div>
    """, unsafe_allow_html=True)

    internships = [
        {"title": "Python Intern", "company": "Google", "stipend": 25000},
        {"title": "Data Analyst Intern", "company": "Amazon", "stipend": 20000},
        {"title": "Web Intern", "company": "Infosys", "stipend": 15000},
    ]

    for i in internships:
        i["score"] = prototype_matching_score(i["stipend"])

    internships = sorted(internships, key=lambda x: x["score"], reverse=True)

    for i in internships:
        st.markdown(f"""
        <div class="card">
            <h3>{i['title']}</h3>
            <p>🏢 {i['company']}</p>
            <p>💰 ₹{i['stipend']}</p>
            <p>🎯 Match Score: {i['score']}%</p>
        </div>
        """, unsafe_allow_html=True)

    if st.button("⬅ Back to Dashboard"):
        go("dashboard")

# =====================================================
# ADMIN DASHBOARD
# =====================================================
if st.session_state.user and st.session_state.role == "Admin":
    st.markdown("""
    <div class="header">
        <h1>📊 Admin Analytics Dashboard</h1>
    </div>
    """, unsafe_allow_html=True)

    df = pd.DataFrame({
        "Skill": ["Python", "Web", "Data", "AI"],
        "Demand": [140, 90, 120, 80]
    })
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.bar_chart(df.set_index("Skill"))
    st.markdown("</div>", unsafe_allow_html=True)
