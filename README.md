Internship Demand & Opportunity Analytics for India 2025

This is a final year project developed to help students find suitable internships
and to analyze internship demand trends in India using data analytics and machine learning.

----------------------------------------

Problem Statement:
Students face difficulty in identifying suitable internships due to fragmented listings,
changing skill requirements, location constraints, and lack of demand prediction.
Institutions and placement cells also lack analytical insights into internship trends.

----------------------------------------

Objectives:
1. Analyze internship data to understand trends and demand.
2. Predict internship demand using machine learning techniques.
3. Recommend internships to students based on their skills.
4. Provide real-time internship search using live job APIs.
5. Deploy the system as a web application.

----------------------------------------

Features:
- Live internship search using API
- Dataset-based internship analytics
- Internship demand prediction
- Student–internship recommendation system
- Web application using Streamlit

----------------------------------------

Technologies Used:
- Python
- Streamlit
- Pandas
- NumPy
- Scikit-learn
- Adzuna Job Search API

----------------------------------------

Dataset:
- Adzuna internship/job dataset (CSV file)
- Real-time internship data fetched using API

----------------------------------------

Steps to Run the Project:

1. Install required libraries:
   pip install -r requirements.txt

2. Run the application:
   streamlit run app.py

3. Open the browser and use the web interface.

----------------------------------------

Output:
- Internship recommendations for students
- Predicted internship demand
- Internship analytics dashboard
- Live internship search results

----------------------------------------

## Deployment Instructions

### Local Development:
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create `.streamlit/secrets.toml` with database configuration:
   ```toml
   [db]
   url = "postgresql://neondb_owner:npg_Oigm2nBb0Jqk@ep-orange-band-ah7k9fu3-pooler.c-3.us-east-1.aws.neon.tech:5432/neondb?sslmode=require"
   ```
4. Run: `streamlit run app.py`

### Troubleshooting Port Issues:

If you get "Port 8505 is not available" error:

**Option 1: Use the provided scripts**
- **Windows**: Double-click `run_app.bat`
- **PowerShell**: Run `.\run_app.ps1`

**Option 2: Manual cleanup**
```bash
# Kill existing processes
taskkill /F /IM python.exe /FI "WINDOWTITLE eq streamlit*"
taskkill /F /IM streamlit.exe

# Wait a few seconds, then run
streamlit run app.py
```

**Option 3: Use a different port**
```bash
streamlit run app.py --server.port 8506
```

The app is configured to always use port 8505. If you need to change this permanently, edit `.streamlit/config.toml`.

### Streamlit Cloud Deployment:
1. Connect your GitHub repository to Streamlit Cloud
2. Set secrets in Streamlit Cloud dashboard:
   ```
   [db]
   url = "postgresql://neondb_owner:npg_Oigm2nBb0Jqk@ep-orange-band-ah7k9fu3-pooler.c-3.us-east-1.aws.neon.tech:5432/neondb?sslmode=require"
   ```
3. Deploy from main branch with `app.py` as entry point

### Database Configuration:
- **Production**: PostgreSQL (Neon)
- **Development**: Automatic fallback to SQLite
- **Secrets**: Configure in `.streamlit/secrets.toml` (local) or Streamlit Cloud settings (production)

## Live Demo
Streamlit App:
https://internship-demand-analytics.streamlit.app


----------------------------------------

Author:
V. Sunil Reddy
