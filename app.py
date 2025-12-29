import streamlit as st
import pandas as pd
import requests
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
# LOAD DATASET + ADD EXTRA INDIAN INTERNSHIPS
# =====================================================
@st.cache_data
def load_dataset():
    df = pd.read_csv("adzuna_internships_raw.csv")
    df.columns = df.columns.str.lower()

    # normalize
    df["title"] = df.get("title", df.get("job_title", "Internship"))
    df["company"] = df.get("company", df.get("company_name", "Company"))
    df["location"] = df.get("location", df.get("city", "India"))
    df["stipend"] = df.get("stipend", 15000)
    df["skills"] = df.get("skills", "")

    # EXTRA REALISTIC INDIAN INTERNSHIPS
    extra = pd.DataFrame([
        ["AI Intern", "TCS", "Bangalore", 18000, "python,ml,ai"],
        ["Data Science Intern", "Wipro", "Hyderabad", 20000, "python,data,ml"],
        ["Cloud Intern", "Accenture", "Pune", 22000, "cloud,aws,devops"],
        ["Web Developer Intern", "Zoho", "Chennai", 15000, "html,css,js"],
        ["Cyber Security Intern", "Tech Mahindra", "Noida", 21000, "security,network"],
        ["Software Intern", "Infosys", "Mysore", 17000, "java,python"],
        ["AI Research Intern", "IIT Madras", "Chennai", 25000, "ai,ml,python"],
        ["Product Intern", "Flipkart", "Bangalore", 23000, "product,analysis"],
        ["Mobile App Intern", "Paytm", "Noida", 19000, "android,flutter"],
        ["ML Engineer Intern", "Swiggy", "Bangalore", 24000, "ml,python,data"]
    ], columns=["title", "company", "location", "stipend", "skills"])

    df = pd.concat([df, extra], ignore_index=True)
    return df

data = load_dataset()

# =====================================================
# LIVE LOCATION (IP BASED)
# =====================================================
def get_live_location():
    try:
        res = requests.get("https://ipapi.co/json/", timeout=5).json()
        return {"city": res.get("city", "Unknown"), "country": res.get("country_name", "India")}
    except:
        return {"city": "Unknown", "country": "India"}

# =====================================================
# MATCHING SCORE
# =====================================================
def compute_score(stipend, skill_match, location_match):
    return round(
        (0.5 * skill_match + 0.3 * location_match + 0.2 * (stipend / 30000)) * 100, 2
    )

# =====================================================
# SIDEBAR
# =====================================================
with st.sidebar:
    st.markdown("## 🎓 Internship Portal")
    if st.session_state.user:
        st.success(f"👤 {st.session_state.user}")
        st.info(f"Role: {st.session_state.role}")
        if st.button("🚪 Logout"):
            st.session_state.user = None
            st.session_state.page = "login"
            st.rerun()

# =====================================================
# LOGIN
# =====================================================
if st.session_state.page == "login":
    st.title("Internship Recommendation System")

    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")
    role = st.selectbox("Role", ["Student", "Admin"])

    if st.button("Login"):
        if user and pwd:
            st.session_state.user = user
            st.session_state.role = role
            st.session_state.location = get_live_location()
            st.session_state.page = "dashboard"
            st.rerun()

# =====================================================
# DASHBOARD
# =====================================================
elif st.session_state.page == "dashboard":
    loc = st.session_state.location
    st.subheader(f"📍 Detected Location: {loc['city']}, {loc['country']}")

    # SKILL INPUT
    user_skills = st.text_input(
        "Enter skills (comma separated)",
        placeholder="python, data, ml"
    )

    # LOCATION DROPDOWN FROM INDIAN COMPANIES
    locations = sorted(data["location"].astype(str).unique())
    selected_location = st.selectbox(
        "Select Internship Location",
        ["All"] + locations
    )

    # RESUME UPLOAD
    resume = st.file_uploader("Upload Resume (PDF)", type="pdf")
    resume_skills = []
    if resume:
        text = " ".join([p.extract_text() or "" for p in PdfReader(resume).pages]).lower()
        resume_skills = [s for s in ["python","data","ml","web","java","cloud"] if s in text]
        st.success(f"Extracted skills: {', '.join(resume_skills)}")

    if st.button("Search Internships"):
        st.session_state.search = {
            "skills": user_skills.lower().split(","),
            "resume_skills": resume_skills,
            "location": selected_location
        }
        st.session_state.page = "results"
        st.rerun()

# =====================================================
# RESULTS
# =====================================================
elif st.session_state.page == "results":
    search = st.session_state.search
    user_city = st.session_state.location["city"].lower()

    st.subheader("🎯 Recommended Internships")

    results = []
    for _, r in data.iterrows():
        skills_text = str(r["skills"]).lower()

        skill_match = sum(
            s.strip() in skills_text
            for s in search["skills"] if s.strip()
        )
        skill_match = min(skill_match / max(len(search["skills"]),1), 1)

        if search["location"] != "All" and search["location"].lower() not in str(r["location"]).lower():
            continue

        location_match = 1 if user_city in str(r["location"]).lower() else 0.6
        score = compute_score(r["stipend"], skill_match, location_match)

        results.append({
            "title": r["title"],
            "company": r["company"],
            "location": r["location"],
            "stipend": r["stipend"],
            "score": score
        })

    results = sorted(results, key=lambda x: x["score"], reverse=True)[:20]

    if not results:
        st.warning("No internships found for given criteria")

    for i in results:
        job_id = f"{i['title']}@{i['company']}"

        st.markdown(f"""
        **{i['title']}**  
        🏢 {i['company']} | 📍 {i['location']} | 💰 ₹{i['stipend']}  
        🎯 Match Score: {i['score']}%
        """)

        if job_id not in st.session_state.applications:
            if st.button(f"Apply – {job_id}", key=job_id):
                st.session_state.applications[job_id] = {
                    "student": st.session_state.user,
                    "status": "Pending"
                }
        else:
            st.info(f"Status: {st.session_state.applications[job_id]['status']}")

    if st.button("⬅ Back"):
        st.session_state.page = "dashboard"
        st.rerun()

# =====================================================
# ADMIN VIEW
# =====================================================
if st.session_state.user and st.session_state.role == "Admin":
    st.subheader("📊 Admin – Applications Review")
    for job, info in st.session_state.applications.items():
        st.write(job, "→", info["student"])
        info["status"] = st.selectbox(
            "Status",
            ["Pending", "Selected"],
            index=["Pending","Selected"].index(info["status"]),
            key=job
        )

