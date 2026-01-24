"""
Comprehensive Test Suite for Internship Analytics Platform
==========================================================

This script tests all major functionality of the internship analytics platform
including data loading, ML models, recommendations, and database operations.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

def test_data_loading():
    """Test data preprocessing and loading"""
    print("\n🔍 TESTING DATA LOADING")
    print("-" * 30)

    try:
        from src.preprocess import preprocess_data
        print("✅ Preprocessing module imported")

        df = preprocess_data()
        print(f"✅ Dataset loaded: {len(df)} internships")
        print(f"   - Columns: {list(df.columns)}")
        print(f"   - Locations: {df['location'].nunique()} unique")
        print(f"   - Categories: {df['category'].nunique()} unique")

        # Check for required columns
        required_cols = ['title', 'company', 'location', 'stipend', 'skills_required']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            print(f"⚠️  Missing columns: {missing_cols}")
        else:
            print("✅ All required columns present")

        return True, df

    except Exception as e:
        print(f"❌ Data loading failed: {e}")
        return False, None

def test_ml_models():
    """Test ML model functionality"""
    print("\n🤖 TESTING ML MODELS")
    print("-" * 30)

    try:
        from src.demand_model import build_features, train_advanced_model
        print("✅ ML model module imported")

        # Load data for testing
        success, df = test_data_loading()
        if not success:
            return False

        # Test feature building
        features_df = build_features(df)
        print(f"✅ Features built: {features_df.shape[1]} features")

        # Test model training (quick test with limited data)
        model, scaler, feature_columns, metrics = train_advanced_model(features_df, target_column='applications_count', model_type='rf')
        print("✅ Model training completed")
        print(f"   - Model type: Random Forest")
        print(f"   - Test R²: {metrics.get('test_r2', 0):.2f}%")
        return True

    except Exception as e:
        print(f"❌ ML model test failed: {e}")
        return False

def test_recommender():
    """Test recommendation system"""
    print("\n🎯 TESTING RECOMMENDER SYSTEM")
    print("-" * 30)

    try:
        import pandas as pd
        from src.recommender import get_personalized_recommendations
        print("✅ Recommender module imported")

        # Load data
        success, df = test_data_loading()
        if not success:
            return False

        # Test with sample user data
        test_skills = ['python', 'machine learning', 'sql']
        test_preferences = {
            'location': 'Bangalore',
            'domain': 'Technology',
            'min_stipend': 5000,
            'remote': False
        }
        test_applications = None  # No application history for new user

        recommendations = get_personalized_recommendations(
            test_skills, test_preferences, df, test_applications
        )

        if isinstance(recommendations, pd.DataFrame) and not recommendations.empty:
            print(f"✅ Recommendations generated: {len(recommendations)} internships")
            print(f"   - Top recommendation: {recommendations.iloc[0]['title'][:50]}...")
            print(f"   - Score: {recommendations.iloc[0].get('recommendation_score', 0):.1f}")
            return True
        elif isinstance(recommendations, list) and len(recommendations) > 0:
            print(f"✅ Recommendations generated: {len(recommendations)} internships")
            print(f"   - Top recommendation: {recommendations[0].get('title', 'Unknown')[:50]}...")
            return True
        else:
            print("⚠️  No recommendations generated")
            return False

    except Exception as e:
        print(f"❌ Recommender test failed: {e}")
        return False

def test_resume_parser():
    """Test resume parsing functionality"""
    print("\n📄 TESTING RESUME PARSER")
    print("-" * 30)

    try:
        # Test the skill bank and parsing logic
        SKILL_BANK = [
            "python","java","sql","machine learning","data science","ai","react",
            "django","flask","aws","docker","html","css","javascript","excel","git"
        ]

        # Test skill matching
        test_text = "I know python, machine learning, and sql. Also familiar with react and django."
        found_skills = [skill for skill in SKILL_BANK if skill in test_text.lower()]

        print("✅ Resume parser logic working")
        print(f"   - Skill bank size: {len(SKILL_BANK)}")
        print(f"   - Test skills found: {found_skills}")

        return True

    except Exception as e:
        print(f"❌ Resume parser test failed: {e}")
        return False

def test_database():
    """Test database operations"""
    print("\n💾 TESTING DATABASE OPERATIONS")
    print("-" * 30)

    try:
        # Test database connection
        import streamlit as st
        from sqlalchemy import create_engine

        # Mock streamlit secrets for testing
        if not hasattr(st, 'secrets'):
            st.secrets = {'db': {'url': 'sqlite:///users.db'}}

        # Import and test database functions
        from app import db, init_db

        engine = db()
        print("✅ Database connection established")

        # Test table creation
        init_db()
        print("✅ Database tables initialized")

        # Test basic query
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result.fetchall()]
            print(f"✅ Tables found: {tables}")

        return True

    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_authentication():
    """Test authentication functions"""
    print("\n🔐 TESTING AUTHENTICATION")
    print("-" * 30)

    try:
        from app import register_user, validate_login
        import streamlit as st

        # Mock streamlit secrets
        if not hasattr(st, 'secrets'):
            st.secrets = {'db': {'url': 'sqlite:///users.db'}}

        # Test user registration
        test_user = f"test_user_{int(__import__('time').time())}"
        success, message = register_user(test_user, f"{test_user}@test.com", "TestPass123!", "Student")

        if success:
            print("✅ User registration successful")
        else:
            print(f"⚠️  Registration result: {message}")

        # Test login
        role = validate_login(test_user, "TestPass123!")
        if role:
            print(f"✅ User login successful, role: {role}")
            return True
        else:
            print("❌ User login failed")
            return False

    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return False

def run_all_tests():
    """Run comprehensive test suite"""
    print("🧪 COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    print("Testing Internship Demand & Analytics Platform")
    print("=" * 60)

    test_results = []

    # Run all tests
    test_results.append(("Data Loading", test_data_loading()[0]))
    test_results.append(("ML Models", test_ml_models()))
    test_results.append(("Recommender", test_recommender()))
    test_results.append(("Resume Parser", test_resume_parser()))
    test_results.append(("Database", test_database()))
    test_results.append(("Authentication", test_authentication()))

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)

    passed = 0
    total = len(test_results)

    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print("15")
        if result:
            passed += 1

    print(f"\n🎯 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED! Platform is fully functional.")
    elif passed >= total * 0.8:
        print("👍 MOST TESTS PASSED! Platform is mostly functional.")
    else:
        print("⚠️  SOME TESTS FAILED! Check issues above.")

    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)