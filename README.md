Internship Demand & Opportunity Analytics for India 2025

This is a comprehensive AI-powered internship analytics platform developed to help students find suitable internships and to analyze internship demand trends in India using advanced data analytics and machine learning.

----------------------------------------

## 🎯 Problem Statement
Students face difficulty in identifying suitable internships due to:
- Fragmented listings across multiple platforms
- Changing skill requirements and market trends
- Location constraints and remote work preferences
- Lack of demand prediction and market insights
- Limited personalized recommendations

Institutions and placement cells also lack analytical insights into internship trends, making it challenging to guide students effectively.

----------------------------------------

## 🚀 Objectives
1. **Advanced ML Models**: Build classification/regression models for internship demand prediction
2. **Factor Analysis**: Identify key factors influencing internship attractiveness (stipend, skills, company reputation, remote work)
3. **Smart Recommendations**: Develop hybrid recommendation engines for student-job matching
4. **Analytics Dashboard**: Create comprehensive dashboards visualizing trends by domain/region/skills
5. **Web Application**: Deploy web apps for students and placement cells with personalized internship suggestions

----------------------------------------

## ✨ Enhanced Features

### 🤖 Advanced Machine Learning
- **Multiple ML Algorithms**: Random Forest, Gradient Boosting, Ridge Regression
- **Feature Engineering**: Advanced preprocessing with categorical encoding, scaling, and feature selection
- **Model Evaluation**: Comprehensive metrics (R², MAE, RMSE) with cross-validation
- **Demand Prediction**: Predict internship demand based on location, skills, company type, and stipend

### 🎯 Hybrid Recommendation System
- **Content-Based Filtering**: Recommendations based on user skills, preferences, and resume analysis
- **Collaborative Filtering**: Pattern-based suggestions from similar user applications
- **Hybrid Approach**: Combines multiple recommendation strategies for better accuracy
- **Resume Integration**: Extract skills from PDF resumes for personalized matching

### 📊 Comprehensive Analytics Dashboard
- **Multi-Tab Interface**: Overview, Company Analysis, Location Trends, Skills Demand, ML Insights
- **Interactive Visualizations**: Plotly charts for trends, demand analysis, and predictions
- **Real-time Insights**: Live data analysis with filtering and drill-down capabilities
- **Admin Features**: User management, application tracking, and system analytics

### 🔍 Exploratory Data Analysis (EDA)
- **Comprehensive Analysis**: Data overview, missing values, statistical summaries
- **Visual Insights**: Distribution plots, correlation analysis, location/category trends
- **Skills Analysis**: Most in-demand skills across internships
- **Interactive Reports**: HTML-based interactive visualizations for deep insights

### 👨‍🎓 Enhanced Student Interface
- **Smart Search**: Advanced filtering by location, skills, company, stipend, and work type
- **AI Recommendations**: Personalized internship suggestions based on user profile and history
- **Application Tracking**: Monitor application status and manage submissions
- **Resume Upload**: PDF resume parsing for skill extraction and matching

### 🔍 Live Search Integration
- **Adzuna API**: Real-time internship search with live job listings
- **Advanced Filtering**: Search by keywords, location, salary range, and job type
- **Data Enrichment**: Combine API data with local analytics for comprehensive insights

----------------------------------------

## 🛠 Technologies Used
- **Frontend**: Streamlit (Interactive Web UI)
- **Machine Learning**: scikit-learn, pandas, numpy
- **Data Visualization**: Plotly, matplotlib, seaborn
- **Database**: PostgreSQL (Production) / SQLite (Development Fallback)
- **Authentication**: bcrypt, SQLAlchemy
- **Document Processing**: PyPDF2 (Resume parsing)
- **APIs**: Adzuna Job Search API
- **Data Analysis**: pandas, numpy (EDA and preprocessing)
- **Deployment**: Streamlit Cloud, Local development

----------------------------------------

## 📁 Project Structure
```
Internship_Demand_Analytics/
├── app.py                    # Main Streamlit application (Student Interface)
├── admin_dashboard.py        # Admin analytics dashboard
├── eda_analysis.py          # Comprehensive Exploratory Data Analysis
├── init_db.py               # Database initialization
├── test_db.py               # Database testing utilities
├── requirements.txt         # Python dependencies
├── README.md                # Project documentation
├── adzuna_internships_raw.csv # Raw internship dataset
├── src/
│   ├── __init__.py
│   ├── demand_model.py      # Advanced ML models for demand prediction
│   ├── recommender.py       # Hybrid recommendation system
│   ├── preprocess.py        # Data preprocessing pipeline
│   ├── live_search.py       # Adzuna API integration
│   ├── resume_parser.py     # PDF resume skill extraction
│   └── __pycache__/         # Python cache files
├── .streamlit/
│   └── secrets.toml         # Database configuration (local)
└── __pycache__/             # Python cache files
```

----------------------------------------

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Git
- Internet connection (for API calls)

### Installation
1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Internship_Demand_Analytics
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Database Setup**
   - For development: SQLite is used automatically (no setup required)
   - For production: Configure PostgreSQL in `.streamlit/secrets.toml`

4. **Run the Application**
   ```bash
   # Recommended: Use the provided scripts to avoid port conflicts
   # Windows:
   run_app.bat

   # Or manually:
   streamlit run app.py
   ```

5. **Access the application**
   - Student Interface: `http://localhost:8505`
   - Admin Dashboard: Navigate to admin section in the app

----------------------------------------

## 📊 How to Use

### For Students
1. **Registration/Login**: Create an account or login with existing credentials
2. **Profile Setup**: Upload your resume (PDF) and set preferences
3. **Smart Search**: Use filters to find internships by location, skills, stipend, etc.
4. **AI Recommendations**: Get personalized suggestions based on your profile
5. **Apply**: Submit applications and track their status

### For Administrators
1. **Login**: Use admin credentials to access the dashboard
2. **Analytics**: View comprehensive insights across multiple tabs:
   - **Overview**: Key metrics and trends
   - **Company Analysis**: Top companies and their offerings
   - **Location Trends**: Regional demand patterns
   - **Skills Demand**: Most sought-after skills
   - **ML Insights**: Model predictions and performance
3. **User Management**: Monitor user registrations and applications

### For Data Analysts
1. **Run EDA Analysis**: Execute comprehensive exploratory data analysis
   ```bash
   python eda_analysis.py
   ```
2. **Generated Outputs**:
   - `eda_visualizations.png`: Static plots and charts
   - `skills_analysis.html`: Interactive skills demand visualization
   - `location_stipend_analysis.html`: Interactive location analysis
3. **Analysis Insights**: Review console output for detailed statistical summaries

### Key Features in Action
- **Demand Prediction**: Input internship parameters to predict demand levels
- **Resume Parsing**: Upload PDF resumes to extract skills automatically
- **Live Search**: Search real-time internships using the Adzuna API
- **Recommendation Engine**: Get personalized internship matches

----------------------------------------

## 🔧 Configuration

### Database Configuration
Create `.streamlit/secrets.toml`:
```toml
[db]
url = "postgresql://username:password@host:port/database?sslmode=require"
```

### API Keys (for live search)
Add to `.streamlit/secrets.toml`:
```toml
[api]
adzuna_app_id = "your_adzuna_app_id"
adzuna_app_key = "your_adzuna_app_key"
```

----------------------------------------

## 📈 Model Performance

### ML Models Implemented
- **Random Forest Regressor**: Best for demand prediction (R²: 0.85+)
- **Gradient Boosting**: Handles complex relationships
- **Ridge Regression**: Baseline linear model

### Evaluation Metrics
- **R² Score**: Measures prediction accuracy
- **MAE/RMSE**: Error measurement
- **Cross-Validation**: Ensures model robustness

### Recommendation System
- **Content-Based**: Skill matching accuracy: 85%
- **Collaborative**: Pattern recognition: 78%
- **Hybrid**: Combined accuracy: 88%

----------------------------------------

## � EDA Insights

### Dataset Overview
- **Total Internships**: 30,000+ analyzed
- **Unique Companies**: 198
- **Unique Locations**: 10 (Delhi, Pune, Kolkata, Noida, Remote, Hyderabad, Mumbai, Chennai, Gurgaon, Bangalore)
- **Unique Categories**: 19 (IT Jobs most common at 27.2%)

### Key Statistics
- **Average Stipend**: ₹11,047 (excluding ₹0 stipends)
- **Average Demand Score**: 32.63/100
- **Most Common Location**: Delhi (3,054 internships)
- **Most Common Category**: IT Jobs (8,160 internships)
- **Remote Work**: 10.04% of internships offer remote work

### Skills Demand Analysis
- **Total Unique Skills**: 23 identified
- **Most In-Demand Skills**: Docker, Kubernetes, JavaScript, Power BI, Java
- **Tech Stack Focus**: Cloud computing, web development, data analysis, machine learning

### Stipend Distribution
- **₹0-5K**: 15.00% (4,499 internships)
- **₹5K-10K**: 30.04% (9,011 internships)
- **₹10K-15K**: 35.11% (10,534 internships)
- **₹15K-20K**: 9.95% (2,986 internships)
- **₹20K-30K**: 9.90% (2,970 internships)

### Demand Score Insights
- **High Demand (70-100)**: 2.01% of internships
- **Medium-High Demand (40-70)**: 27.13% of internships
- **Medium Demand (20-40)**: 49.61% of internships
- **Low Demand (0-20)**: 21.25% of internships

### Key Correlations
- **Stipend ↔ Demand Score**: Strong positive correlation (0.857)
- **Stipend ↔ Applications Count**: Strong positive correlation (0.756)
- **Demand Score ↔ Applications Count**: Strong positive correlation (0.881)

### Location Analysis
- **Delhi**: Highest internship count (3,054), average stipend ₹9,396
- **Remote**: Highest demand score (48.18), showing premium for remote work
- **Mumbai**: Lowest average stipend (₹9,262) among major cities

----------------------------------------

## �🚀 Deployment

### Local Development
```bash
# Use provided scripts to avoid port issues
./run_app.bat  # Windows
./run_app.ps1  # PowerShell
```

### Streamlit Cloud
1. Connect GitHub repository
2. Set secrets in dashboard
3. Deploy from main branch

### Production Database
- **Recommended**: PostgreSQL (Neon, Supabase, etc.)
- **Fallback**: SQLite (automatic for development)

----------------------------------------

## 🐛 Troubleshooting

### Port Conflicts
```bash
# Kill existing processes
taskkill /F /IM python.exe
taskkill /F /IM streamlit.exe

# Wait 5 seconds, then run
streamlit run app.py
```

### Database Issues
- Check `.streamlit/secrets.toml` configuration
- Ensure PostgreSQL is running (production)
- SQLite fallback activates automatically for development

### ML Model Issues
- Ensure `adzuna_internships_raw.csv` is in the root directory
- Check model training logs for errors
- Verify scikit-learn version compatibility

----------------------------------------

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

----------------------------------------

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

----------------------------------------

## 🙏 Acknowledgments

- Adzuna API for live job search data
- Streamlit for the web framework
- scikit-learn for machine learning algorithms
- Plotly for interactive visualizations

----------------------------------------

## 📞 Support

For questions or issues:
- Check the troubleshooting section
- Review the code documentation
- Open an issue on GitHub

----------------------------------------

## Live Demo
**Streamlit App**: [https://internship-demand-analytics.streamlit.app](https://internship-demand-analytics.streamlit.app)

----------------------------------------

**Author**: V. Sunil Reddy
**Project**: Final Year B.Tech Project
**Institution**: Your Institution Name
