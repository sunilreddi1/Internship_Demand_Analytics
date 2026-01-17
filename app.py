import streamlit as st
import pandas as pd
import math
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
for k, v in {
    "page": "login",
    "user": None,
    "role": "Student",
    "dark": False,
    "applications": {},
    "saved": set(),
    "page_no": 1
}.items():
    st.session_state.setdefault(k, v)

# =====================================================
# LOAD DATA
# =====================================================
@st.cache_data
def load_data():
    df = pd.read_csv("adzuna_internships_raw.csv")
    df.columns = df.columns.str.lower()
    return df.fillna("")

data = load_data()

# =====================================================
# THEME & UI
# =====================================================
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg,#f3e7ff,#cce0ff);
}

.login-box {
    background:white;
    padding:40px;
    border-radius:20px;
    box-shadow:0 20px 50px rgba(0,0,0,0.15);
}

.hero {
    background: linear-gradient(135deg,#6a11cb,#2575fc,#ff6a88);
    color:white;
    padding:60px;
    border-radius:20px;
    height:100%;
}

.card {
    background:white;
    padding:20px;
    border-radius:18px;
    box-shadow:0 15px 30px rgba(0,0,0,0.15);
    margin-bottom:20px;
}

.header {
    background: linear-gradient(90deg,#0a66c2,#6a11cb,#ff6a88);
    padding:30px;
    border-radius:20px;
    color:white;
    margin-bottom:25px;
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# HELPERS
# =====================================================
def go(p):
    st.session_state.page = p
    st.rerun()

def match_score(stipend):
    try:
        return min(100, int((int(stipend) / 30000) * 100))
    except:
        return 60

# =====================================================
# SIDEBAR
# =====================================================
with st.sidebar:
    st.markdown("## 🎓 Internship Portal")
    if st.session_state.user:
        st.success(st.session_state.user)
        if st.button("Logout"):
            st.session_state.user = None
            go("login")

# =====================================================
# LOGIN PAGE (MODERN UI)
# =====================================================
if st.session_state.page == "login":
    c1, c2 = st.columns([1,1])

    with c1:
        st.markdown("""
        <div class="login-box">
        <h2>Welcome back</h2>
        <p>Login to explore internships</p>
        """, unsafe_allow_html=True)

        u = st.text_input("Username")
        p = st.text_input("Password", type="password")

        if st.button("Login"):
            if u and p:
                st.session_state.user = u
                go("dashboard")
            else:
                st.error("Enter credentials")

        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="hero">
        <h1>Internship Portal</h1>
        <p>Search • Match • Apply</p>
        <ul>
        <li>✔ Skill-based recommendations</li>
        <li>✔ Real company internships</li>
        <li>✔ Apply & track status</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

# =====================================================
# DASHBOARD
# =====================================================
elif st.session_state.page == "dashboard":
    st.markdown("""
    <div class="header">
    <h1>🚀 Internship Dashboard</h1>
    </div>
    """, unsafe_allow_html=True)

    skill = st.text_input("🔎 Search by Skill / Job Title")

    if st.button("Search"):
        st.session_state.page_no = 1
        go("results")

# =====================================================
# RESULTS WITH PAGINATION + APPLY + SAVE
# =====================================================
elif st.session_state.page == "results":
    st.markdown("""
    <div class="header">
    <h1>🎯 Recommended Internships</h1>
    </div>
    """, unsafe_allow_html=True)

    query = st.text_input("Filter", key="filter")

    df = data.copy()
    if query:
        df = df[df["title"].str.contains(query, case=False)]

    per_page = 6
    total_pages = math.ceil(len(df)/per_page)
    start = (st.session_state.page_no-1)*per_page
    end = start + per_page

    for idx, r in df.iloc[start:end].iterrows():
        jid = f"{idx}_{r['title']}"

        st.markdown(f"""
        <div class="card">
        <h3>{r['title']}</h3>
        <p><b>🏢 {r.get('company','')}</b></p>
        <p>{r.get('description','')[:180]}...</p>
        <p>💰 ₹{r.get('stipend',15000)} | 🎯 Match {match_score(r.get('stipend',15000))}%</p>
        </div>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns(2)

        if c1.button("Apply", key="a"+jid):
            st.session_state.applications[jid] = "Pending"
            st.success("Applied")

        if c2.button("Save", key="s"+jid):
            st.session_state.saved.add(jid)
            st.info("Saved")

    col1, col2, col3 = st.columns([1,2,1])
    with col1:
        if st.session_state.page_no > 1:
            if st.button("⬅ Previous"):
                st.session_state.page_no -= 1
                st.rerun()
    with col3:
        if st.session_state.page_no < total_pages:
            if st.button("Next ➡"):
                st.session_state.page_no += 1
                st.rerun()

# =====================================================
# ADMIN VIEW
# =====================================================
if st.session_state.user == "admin":
    st.markdown("<div class='header'><h1>Admin Panel</h1></div>", unsafe_allow_html=True)
    for k, v in st.session_state.applications.items():
        st.write(k, v)
