import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
import streamlit as st

def compute_match_score(job_skills, user_skills, stipend):
    """
    Enhanced matching score with multiple factors
    """
    # Skill matching score
    if not job_skills:
        skill_score = 0.4
    else:
        matched = set(job_skills).intersection(set(user_skills))
        skill_score = len(matched) / len(job_skills)

    # Stipend influence (normalized)
    stipend_score = min(stipend / 30000, 1)

    # Final weighted score
    final_score = (0.7 * skill_score + 0.3 * stipend_score) * 100
    return round(final_score, 2)

def create_user_profile(user_skills, user_preferences):
    """
    Create a comprehensive user profile for better matching

    Args:
        user_skills: List of user skills
        user_preferences: Dict with user preferences (location, domain, stipend_range, etc.)

    Returns:
        user_profile: Dict with normalized user features
    """
    profile = {
        'skills': user_skills,
        'preferred_location': user_preferences.get('location', ''),
        'preferred_domain': user_preferences.get('domain', ''),
        'min_stipend': user_preferences.get('min_stipend', 0),
        'max_stipend': user_preferences.get('max_stipend', 50000),
        'remote_preference': user_preferences.get('remote', False),
        'experience_level': user_preferences.get('experience', 'entry')
    }
    return profile

def calculate_content_based_score(user_profile, job_data):
    """
    Content-based filtering score based on user profile and job features

    Args:
        user_profile: Dict with user preferences and skills
        job_data: Dict with job features

    Returns:
        tuple: (content_score, skill_score) - both floats between 0-100
    """
    score = 0
    max_score = 100
    skill_score = 0

    # Skills matching (40% weight of content score, but skill_score is pure skill match)
    job_skills = set(job_data.get('skills_required', '').split(', '))
    user_skills = set(user_profile['skills'])
    if job_skills:
        skill_match_ratio = len(user_skills.intersection(job_skills)) / len(job_skills)
        skill_score = skill_match_ratio * 100  # Pure skill score 0-100
        score += skill_match_ratio * 40  # 40% weight in content score

    # Location matching (20% weight)
    user_location = user_profile['preferred_location'].lower()
    job_location = job_data.get('location', '').lower()
    if user_location in job_location or job_data.get('is_remote', False):
        score += 20
    elif user_location and job_location:
        # Partial location match
        score += 10

    # Domain/Category matching (15% weight)
    user_domain = user_profile['preferred_domain'].lower()
    job_category = job_data.get('category', '').lower()
    if user_domain in job_category or user_domain == 'any':
        score += 15

    # Stipend compatibility (15% weight)
    job_stipend = job_data.get('stipend', 0)
    min_stipend = user_profile['min_stipend']
    max_stipend = user_profile['max_stipend']
    if min_stipend <= job_stipend <= max_stipend:
        score += 15
    elif job_stipend >= min_stipend * 0.8:  # 80% of minimum is acceptable
        score += 10

    # Remote work preference (10% weight)
    if user_profile['remote_preference'] and job_data.get('is_remote', False):
        score += 10
    elif not user_profile['remote_preference'] and not job_data.get('is_remote', False):
        score += 10

    return min(score, max_score), round(skill_score, 2)

def calculate_collaborative_score(user_id, job_id, applications_df):
    """
    Collaborative filtering based on similar users' preferences

    Args:
        user_id: Current user ID
        job_id: Job ID to score
        applications_df: DataFrame with user-job interactions

    Returns:
        score: Collaborative filtering score
    """
    if applications_df is None or applications_df.empty:
        return 50  # Neutral score if no data

    # Find users who applied to similar jobs
    similar_job_applications = applications_df[applications_df['job_id'] == job_id]

    if similar_job_applications.empty:
        return 50

    # Calculate popularity score based on applications
    total_applications = len(similar_job_applications)
    score = min(total_applications * 2, 100)  # Scale popularity to 0-100

    return score

def hybrid_recommendation_engine(user_profile, jobs_df, applications_df=None, top_n=10):
    """
    Hybrid recommendation system combining content-based and collaborative filtering

    Args:
        user_profile: Dict with user preferences and skills
        jobs_df: DataFrame with job listings
        applications_df: DataFrame with user-job interactions (optional)
        top_n: Number of recommendations to return

    Returns:
        recommendations: DataFrame with ranked job recommendations
    """
    recommendations = []

    for _, job in jobs_df.iterrows():
        # Content-based score and skill score
        content_score, skill_score = calculate_content_based_score(user_profile, job.to_dict())

        # Collaborative score (if applications data available)
        collab_score = 50  # Default neutral score
        if applications_df is not None:
            collab_score = calculate_collaborative_score(
                user_profile.get('user_id', 'anonymous'),
                job.get('id', job.get('title', '')),
                applications_df
            )

        # Hybrid score (weighted combination)
        hybrid_score = (0.7 * content_score) + (0.3 * collab_score)

        # Add demand/popularity factor
        demand_factor = job.get('demand_score', 50) / 100  # Normalize to 0-1
        final_score = hybrid_score * (0.8 + 0.2 * demand_factor)  # Boost popular jobs slightly

        job_recommendation = job.copy()
        job_recommendation['recommendation_score'] = round(final_score, 2)
        job_recommendation['content_score'] = round(content_score, 2)
        job_recommendation['skill_score'] = skill_score  # Pure skill matching score
        job_recommendation['collaborative_score'] = round(collab_score, 2)

        recommendations.append(job_recommendation)

    # Sort by recommendation score and return top N
    recommendations_df = pd.DataFrame(recommendations)
    recommendations_df = recommendations_df.sort_values('recommendation_score', ascending=False)

    return recommendations_df.head(top_n)

def get_personalized_recommendations(user_skills, user_preferences, jobs_df, applications_df=None):
    """
    Main function to get personalized internship recommendations

    Args:
        user_skills: List of user skills
        user_preferences: Dict with user preferences
        jobs_df: DataFrame with available jobs
        applications_df: DataFrame with application history (optional)

    Returns:
        recommendations: DataFrame with top recommendations
    """
    # Create user profile
    user_profile = create_user_profile(user_skills, user_preferences)

    # Get hybrid recommendations
    recommendations = hybrid_recommendation_engine(
        user_profile, jobs_df, applications_df, top_n=20
    )

    return recommendations

# Legacy function for backward compatibility
def compute_match_score(job_skills, user_skills, stipend):
    """
    Legacy matching score function
    """
    # Skill matching score
    if not job_skills:
        skill_score = 0.4
    else:
        matched = set(job_skills).intersection(set(user_skills))
        skill_score = len(matched) / len(job_skills)

    # Stipend influence
    stipend_score = min(stipend / 30000, 1)

    # Final weighted score
    final_score = (0.7 * skill_score + 0.3 * stipend_score) * 100
    return round(final_score, 2)
