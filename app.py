import streamlit as st
import pandas as pd
import requests
from PyPDF2 import PdfReader

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Internship Portal",
    page_icon="🎓",
    layout="wide"
)

# =====================================================
# SESSION STATE
# =====================================================
defaults = {
    "page": "login",
    "user": None,
    "role": "Student",
    "applications": {},
    "bookmarks": set(),
    "page_no": 0,
    "page_size": 5
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =====================================================
# LOAD DATASET
# =====================================================
@st.cache_data
def load_data():
    df = pd.read_csv("adzuna_internships_raw.csv")
    df.columns = df.columns.str.lower()

    df["title"] = df.get("job_title", df.get("title", "Internship"))
    df["company"] = df.get("company_name", df.get("company", "Company"))
    df["location"] = df.get("city", df.get("location", "India"))
    df["stipend"] = df.get("salary_min", df.get("stipend", 15000)).fillna(15000)
    df["description"] = df.get("description", "Internship opportunity")
    df["logo"] = df.get("company_logo", df.get("logo", ""))

    return df

data = load_data()

# =====================================================
# LOCATION
# =====================================================
def get_city():
    try:
        return requests.get("https://ipapi.co/json/", timeout=4).json().get("city","India")
    except:
        return "India"

# =====================================================
# UI THEME
# =====================================================
def apply_theme():
    st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg,#f3e8ff,#ddd6fe,#bfdbfe);
        font-family: 'Segoe UI', sans-serif;
    }
    .header {
        background: linear-gradient(90deg,#2563eb,#7c3aed,#ec4899);
        padding:30px;border-radius:22px;color:white;
        margin-bottom:25px;
    }
    .card {
        background: rgba(255,255,255,0.9);
        backdrop-filter: blur(12px);
        padding:24px;border-radius:22px;
        margin-bottom:22px;
        box-shadow:0 18px 40px rgba(0,0,0,0.18);
    }
    .job { display:flex; gap:20px; }
    .logo img {
        width:70px;height:70px;
        object-fit:contain;
        background:white;
        padding:6px;border-radius:14px;
    }
    .chip {
        padding:6px 12px;
        border-radius:999px;
        background:#eef2ff;
        color:#3730a3;
        font-size:13px;
        margin-right:6px;
    }
    button {
        background:linear-gradient(90deg,#2563eb,#7c3aed)!important;
        color:white!important;
        border-radius:12px!important;
        font-weight:600!important;
    }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg,#f5f3ff,#e0e7ff);
    }
    </style>
    """, unsafe_allow_html=True)

apply_theme()

# =====================================================
# HELPERS
# =====================================================
def go(p):
    st.session_state.page = p
    st.rerun()

def score_job(stipend, city_match):
    return round((0.7*(stipend/30000) + 0.3*city_match)*100,2)

# =====================================================
# SIDEBAR
# =====================================================
with st.sidebar:
    st.markdown("## 🎓 Internship Portal")
    if st.session_state.user:
        st.success(f"👤 {st.session_state.user}")
        if st.button("👤 Profile"):
            go("profile")
        if st.button("🚪 Logout"):
            st.session_state.user = None
            go("login")

# =====================================================
# LOGIN
# =====================================================
if st.session_state.page == "login":
    st.markdown("<div class='header'><h1>Welcome 👋</h1></div>", unsafe_allow_html=True)
    u = st.text_input("Username")
    r = st.selectbox("Role", ["Student","Admin"])
    if st.button("Login") and u:
        st.session_state.user = u
        st.session_state.role = r
        st.session_state.city = get_city()
        go("dashboard")

# =====================================================
# DASHBOARD
# =====================================================
elif st.session_state.page == "dashboard":
    st.markdown("<div class='header'><h1>Internship Dashboard</h1></div>", unsafe_allow_html=True)
    st.info(f"📍 Location: {st.session_state.city}")

    skill = st.text_input("Skill (python, data, web)")
    resume = st.file_uploader("Upload Resume (PDF)", type="pdf")

    if st.button("Search"):
        st.session_state.skill = skill.lower()
        go("results")

# =====================================================
# RESULTS + PAGINATION + BOOKMARK
# =====================================================
elif st.session_state.page == "results":
    st.markdown("<div class='header'><h1>Recommended Internships</h1></div>", unsafe_allow_html=True)

    start = st.session_state.page_no * st.session_state.page_size
    end = start + st.session_state.page_size

    results = []
    for _, r in data.iterrows():
        match = 1 if st.session_state.skill in r["description"].lower() else 0.6
        city_match = 1 if st.session_state.city.lower() in str(r["location"]).lower() else 0.6
        rscore = score_job(r["stipend"], city_match)
        results.append((rscore, r))

    results = sorted(results, reverse=True, key=lambda x: x[0])
    page_jobs = results[start:end]

    for score, r in page_jobs:
        jid = f"{r['title']}@{r['company']}"
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="job">
            <div class="logo">{'<img src="'+r["logo"]+'">' if r["logo"] else ''}</div>
            <div>
                <h3>{r['title']}</h3>
                <p>{r['company']} • {r['location']}</p>
                <p>{r['description'][:200]}...</p>
                <span class="chip">₹{int(r['stipend'])}</span>
                <span class="chip">{score}% Match</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        if jid not in st.session_state.applications:
            if c1.button("Apply", key="a"+jid):
                st.session_state.applications[jid] = {"status":"Pending"}
        if jid not in st.session_state.bookmarks:
            if c2.button("🔖 Save", key="s"+jid):
                st.session_state.bookmarks.add(jid)
        st.markdown("</div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    if c1.button("⬅ Previous") and st.session_state.page_no > 0:
        st.session_state.page_no -= 1
        st.rerun()
    if c2.button("Next ➡"):
        st.session_state.page_no += 1
        st.rerun()

# =====================================================
# PROFILE PAGE
# =====================================================
elif st.session_state.page == "profile":
    st.markdown("<div class='header'><h1>User Profile</h1></div>", unsafe_allow_html=True)

    st.subheader("📌 Applied Internships")
    if not st.session_state.applications:
        st.info("No applications yet")
    for k, v in st.session_state.applications.items():
        st.write(k, "→", v["status"])

    st.subheader("🔖 Saved Internships")
    if not st.session_state.bookmarks:
        st.info("No bookmarks yet")
    for b in st.session_state.bookmarks:
        st.write(b)

    if st.button("⬅ Back"):
        go("dashboard")

# =====================================================
# ADMIN
# =====================================================
if st.session_state.user and st.session_state.role == "Admin":
    st.markdown("<div class='header'><h1>Admin Panel</h1></div>", unsafe_allow_html=True)
    for k, v in st.session_state.applications.items():
        st.write(k)
        v["status"] = st.selectbox(
            "Status", ["Pending","Selected"],
            index=["Pending","Selected"].index(v["status"]),
            key=k
        )
