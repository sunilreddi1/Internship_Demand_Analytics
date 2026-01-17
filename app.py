import streamlit as st
import pandas as pd
import sqlite3
import re
import matplotlib.pyplot as plt

# ---------------- CONFIG ----------------
st.set_page_config("Internship Demand Portal", "🎓", layout="wide")

DATASET_SKILLS = [
    "Python","Java","C","SQL","MySQL","PostgreSQL",
    "React","Node.js","Express","FastAPI",
    "Data Analysis","Data Science","Machine Learning",
    "NLP","AI","Artificial Intelligence",
    "AWS","Excel","Communication","Leadership"
]

# ---------------- DB ----------------
def get_db():
    return sqlite3.connect("users.db", check_same_thread=False)

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data():
    df = pd.read_csv("adzuna_internships_raw.csv")
    df.columns = df.columns.str.lower()
    df["description"] = df["description"].fillna("")
    df["skills"] = df["description"].apply(extract_skills)
    df["stipend"] = df.get("stipend", 15000)
    return df

def extract_skills(text):
    found = []
    for skill in DATASET_SKILLS:
        if re.search(rf"\b{re.escape(skill.lower())}\b", text.lower()):
            found.append(skill)
    return found

data = load_data()

# ---------------- SESSION ----------------
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "login"

# ---------------- LOGIN ----------------
def login_page():
    st.title("🎓 Internship Portal Login")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?", (u,p))
        if cur.fetchone():
            st.session_state.user = u
            st.session_state.page = "dashboard"
            st.rerun()
        else:
            st.error("Invalid login")

    st.markdown("---")
    st.subheader("New User Registration")

    ru = st.text_input("New Username")
    rp = st.text_input("New Password", type="password")

    if st.button("Register"):
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)",
                        (ru,rp,"Student"))
            conn.commit()
            st.success("User registered successfully")
        except:
            st.error("Username already exists")

# ---------------- DASHBOARD ----------------
def dashboard():
    st.sidebar.success(f"👤 {st.session_state.user}")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.page = "login"
        st.rerun()

    st.title("🚀 Internship Dashboard")

    skill = st.selectbox("🔎 Skill Filter", ["All"] + DATASET_SKILLS)

    if skill != "All":
        df = data[data["skills"].apply(lambda x: skill in x)]
    else:
        df = data.copy()

    # ---------------- MATCH SCORE ----------------
    def match_score(row):
        skill_score = len(row["skills"]) / 5
        stipend_score = min(row["stipend"]/30000,1)
        return round((0.7*skill_score + 0.3*stipend_score)*100,2)

    df["match_score"] = df.apply(match_score, axis=1)
    df = df.sort_values("match_score", ascending=False).head(10)

    # ---------------- JOB CARDS ----------------
    for _,row in df.iterrows():
        job_id = f"{row['title']}@{row['company']}"

        st.markdown(f"""
        ### {row['title']}
        **Company:** {row['company']}  
        **Skills:** {", ".join(row['skills'])}  
        **Match Score:** {row['match_score']}%
        """)

        if st.button("Apply", key=job_id):
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO applications (username,job_id,status)
                VALUES (?,?,?)
            """,(st.session_state.user,job_id,"Pending"))
            conn.commit()
            st.success("Applied successfully")

        st.markdown("---")

    # ---------------- TOP SKILLS CHART ----------------
    st.subheader("📊 Top Skills Demand")

    all_skills = sum(data["skills"],[])
    skill_counts = pd.Series(all_skills).value_counts().head(10)

    fig,ax = plt.subplots()
    skill_counts.plot(kind="bar", ax=ax)
    st.pyplot(fig)

# ---------------- ROUTER ----------------
if st.session_state.page == "login":
    login_page()
else:
    dashboard()
