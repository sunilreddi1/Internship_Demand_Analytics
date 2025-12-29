import streamlit as st
import time

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Internship Portal",
    page_icon="🎓",
    layout="wide"
)

# ---------------- SESSION STATE ----------------
if "page" not in st.session_state:
    st.session_state.page = "login"

if "user" not in st.session_state:
    st.session_state.user = None

# ---------------- ADVANCED COLORFUL UI ----------------
st.markdown("""
<style>

/* ===== GLOBAL BACKGROUND ===== */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(120deg, #fdfbfb, #ebedee, #e3f2fd);
}

/* ===== ANIMATIONS ===== */
@keyframes fadeSlide {
    from {opacity:0; transform: translateY(25px);}
    to {opacity:1; transform: translateY(0);}
}
.fade {
    animation: fadeSlide 0.7s ease;
}

/* ===== HEADER ===== */
.header {
    background: linear-gradient(90deg, #0a66c2, #6a11cb, #ff6a88);
    padding: 30px;
    border-radius: 18px;
    color: white;
    box-shadow: 0 12px 32px rgba(0,0,0,0.25);
}

/* ===== CARD ===== */
.card {
    background: linear-gradient(135deg, #ffffff, #f8fbff);
    border-radius: 18px;
    padding: 20px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    margin-bottom: 18px;
    transition: all 0.3s ease;
}
.card:hover {
    transform: translateY(-6px);
    box-shadow: 0 16px 40px rgba(0,0,0,0.18);
}

/* ===== BUTTON ===== */
button {
    background: linear-gradient(90deg, #0a66c2, #00c6ff) !important;
    color: white !important;
    border-radius: 10px !important;
    font-weight: bold !important;
}

/* ===== LOGO GRID ===== */
.logo-grid img {
    width: 90px;
    margin: 14px;
    padding: 10px;
    background: white;
    border-radius: 14px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.12);
}

/* ===== SIDEBAR ===== */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #f5f7fa, #e4ecf7);
}

</style>
""", unsafe_allow_html=True)

# ---------------- HELPERS ----------------
def go(page):
    st.session_state.page = page
    st.rerun()

def toast(msg, icon="✨"):
    st.toast(msg, icon=icon)

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.markdown("## 🎓 Internship Portal")
    if st.session_state.user:
        st.success(f"👤 {st.session_state.user}")
        if st.button("🚪 Logout"):
            st.session_state.user = None
            toast("Logged out successfully")
            go("login")
    st.markdown("---")
    st.info("Inspired by LinkedIn & Internshala")

# ---------------- LOGIN PAGE ----------------
if st.session_state.page == "login":
    st.markdown("""
    <div class="fade header">
        <h1>Welcome Back 👋</h1>
        <p>Discover internships that match your skills</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='fade card'>", unsafe_allow_html=True)
    u = st.text_input("👤 Username")
    p = st.text_input("🔑 Password", type="password")

    if st.button("Login"):
        if u and p:
            st.session_state.user = u
            toast("Login successful 🎉")
            go("dashboard")
        else:
            st.error("Please enter credentials")
    st.markdown("</div>", unsafe_allow_html=True)

    st.caption("🔹 Demo: any username & password")

# ---------------- DASHBOARD ----------------
elif st.session_state.page == "dashboard":
    st.markdown("""
    <div class="fade header">
        <h1>Internship Dashboard</h1>
        <p>Search, rank & explore real opportunities</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([2,1])

    with col1:
        st.markdown("<div class='fade card'>", unsafe_allow_html=True)
        skill = st.text_input("🔍 Skill (Python, Web, Data Science)")
        location = st.selectbox("📍 Location", ["India", "Remote"])
        if st.button("Search Internships 🚀"):
            toast("Searching internships...", "🔎")
            time.sleep(1)
            go("results")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='fade card'>", unsafe_allow_html=True)
        st.markdown("### 🔥 Top Hiring Companies")
        st.markdown("""
        <div class="logo-grid">
            <img src="https://logo.clearbit.com/google.com">
            <img src="https://logo.clearbit.com/microsoft.com">
            <img src="https://logo.clearbit.com/amazon.com">
            <img src="https://logo.clearbit.com/infosys.com">
            <img src="https://logo.clearbit.com/tcs.com">
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ---------------- RESULTS ----------------
elif st.session_state.page == "results":
    st.markdown("""
    <div class="fade header">
        <h1>Recommended Internships</h1>
        <p>Sorted by relevance & demand</p>
    </div>
    """, unsafe_allow_html=True)

    internships = [
        {"title":"Python Developer Intern","company":"Google","stipend":"₹25,000","match":92},
        {"title":"Data Analyst Intern","company":"Amazon","stipend":"₹20,000","match":88},
        {"title":"Web Developer Intern","company":"Infosys","stipend":"₹15,000","match":82},
    ]

    for i in internships:
        st.markdown(f"""
        <div class="fade card">
            <h3>{i['title']}</h3>
            <p><b>🏢 Company:</b> {i['company']}</p>
            <p><b>💰 Stipend:</b> {i['stipend']}</p>
            <p><b>🎯 Match Score:</b> {i['match']}%</p>
        </div>
        """, unsafe_allow_html=True)

    if st.button("⬅ Back to Dashboard"):
        go("dashboard")
