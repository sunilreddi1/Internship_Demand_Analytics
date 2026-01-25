# Internship Demand Analytics - AI Coding Guidelines

## Architecture Overview
This is a Streamlit-based internship analytics platform with ML-driven demand prediction and hybrid recommendation systems. The app serves both students (job search + recommendations) and administrators (analytics dashboard).

**Core Components:**
- `app.py`: Main Streamlit UI with authentication, search, and user management
- `src/demand_model.py`: ML models for internship demand prediction using Random Forest/Gradient Boosting
- `src/recommender.py`: Hybrid recommendation engine combining content-based and collaborative filtering
- `src/preprocess.py`: Data preprocessing pipeline with memory optimization
- `src/live_search.py`: Adzuna API integration for real-time job search
- `src/resume_parser.py`: PDF skill extraction using PyPDF2

**Data Flow:**
1. Raw CSV data → `preprocess.py` → Feature engineering
2. Features → `demand_model.py` → Trained ML models
3. User profiles + job data → `recommender.py` → Personalized recommendations
4. Live search → `live_search.py` → API enrichment

## Database Layer
**Dual Database Support:**
- Production: PostgreSQL (configured via `DATABASE_URL` env var)
- Development: SQLite fallback (`users.db`)
- Tables: `users` (auth), `applications` (tracking)

**Database Connection Pattern:**
```python
def db():
    try:
        # Try PostgreSQL first
        if st.secrets["db"]["url"]:
            engine = create_engine(st.secrets["db"]["url"], connect_args={'sslmode': 'require'})
            return engine
    except:
        pass
    # Fallback to SQLite
    return create_engine("sqlite:///users.db")
```

## Critical Workflows

### Database Initialization
- Run `python init_db.py` to create tables
- Handles both PostgreSQL and SQLite schemas automatically
- Use `python test_db.py` to verify connections

### Local Development
```powershell
# Kill existing processes and start fresh
.\run_app.ps1  # Uses port 8503, localhost only
# Or for network sharing:
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

### ML Model Training
```python
from src.demand_model import train_advanced_model
model, scaler, features, metrics = train_advanced_model(df, target_column='demand_score', model_type='rf')
```

## Project-Specific Patterns

### Safe Imports with Fallbacks
```python
try:
    import psycopg2
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False
```

### Memory-Optimized Data Processing
```python
# Reduce memory usage in preprocessing
df['stipend'] = df['stipend'].astype('int32')
df['description'] = df['description'].str[:500]  # Truncate long text
```

### Authentication & Security
- Passwords hashed with `bcrypt`
- Strong password validation: 8+ chars, uppercase, lowercase, numbers, special chars
- User roles: 'student', 'admin'

### Feature Engineering Conventions
- Location features: `is_remote`, `is_metro` (Delhi/Mumbai/Bangalore/etc.)
- Company features: `company_score` (frequency-based), `company_reputation`
- Category features: `is_tech`, `is_finance`, `is_marketing`
- Text features: Extract tech/soft skills, experience level, premium company indicators

### Recommendation Scoring
- Content-based: 70% skill match + 30% stipend compatibility
- Hybrid approach: Combines multiple recommendation strategies
- Skill matching: Exact string intersection of user skills vs job requirements

## Integration Points

### External APIs
- **Adzuna API**: Live job search with app_id and app_key from secrets
- Configure in `.streamlit/secrets.toml`:
```toml
[api]
adzuna_app_id = "your_id"
adzuna_app_key = "your_key"
```

### Deployment Configurations
- **Railway**: Use `railway.json` + `DATABASE_URL` env var
- **Render**: Use `render.yaml`
- **Docker**: `docker build -t app . && docker run -p 8501:8501 app`
- **Streamlit Cloud**: Automatic from GitHub repo

## Development Conventions

### File Organization
- Core logic in `src/` with `__init__.py`
- Configuration in `.streamlit/` (secrets, config)
- Deployment scripts in root (`.ps1`, `.bat`, `.sh`)
- Data files: `adzuna_internships_raw.csv`

### Error Handling
- Database connections: Always try PostgreSQL first, fallback to SQLite
- API calls: Graceful degradation when services unavailable
- File operations: Check existence before processing

### Testing & Validation
- Run `python -c "import app; print('Syntax check passed')"` for basic validation
- Use `python test_db.py` for database connectivity
- ML models validated with cross-validation and multiple metrics (R², MAE, RMSE)

## Common Pitfalls to Avoid

### Database Issues
- Never hardcode database URLs - use environment variables or Streamlit secrets
- Always handle both PostgreSQL and SQLite column types (SERIAL vs INTEGER PRIMARY KEY)

### Memory Management
- Process large CSV files in chunks when possible
- Use appropriate dtypes (int32, float32) to reduce memory usage
- Truncate long text fields in preprocessing

### Streamlit Session State
- Use `st.session_state.user` for current user tracking
- Initialize session state variables defensively
- Handle page refreshes gracefully

### API Rate Limiting
- Implement caching for API responses
- Provide fallback demo data when APIs are unavailable
- Handle API errors without breaking the UI

## Key Reference Files
- `src/demand_model.py`: ML model training and prediction logic
- `src/recommender.py`: Recommendation algorithm implementations
- `app.py`: Main application structure and UI flow
- `init_db.py`: Database schema and initialization
- `run_app.ps1`: Local development startup script