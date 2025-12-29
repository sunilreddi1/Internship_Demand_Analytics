def recommend_internships(internships, skill):
    """
    Recommend and rank internships based on skill relevance
    """

    skill = skill.lower()
    results = []

    for job in internships:
        title = job.get("title", "").lower()

        # simple relevance score
        score = title.count(skill)
        match_percent = min(100, score * 40)

        job["match_score"] = score
        job["match_percent"] = match_percent

        results.append(job)

    # sort by relevance
    results.sort(key=lambda x: x["match_score"], reverse=True)

    return results
