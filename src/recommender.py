# src/recommender.py

def compute_match_score(job_skills, user_skills, stipend):
    """
    Prototype-level matching score
    - job_skills: list of skills required by internship
    - user_skills: list of skills extracted from resume
    - stipend: internship stipend
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
