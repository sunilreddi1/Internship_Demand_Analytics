def predict_demand(internship):
    """
    Predict demand score for an internship (simulated model)
    """

    score = 0

    title = internship.get("title", "").lower()
    location = internship.get("location", "").lower()

    # Simple heuristic-based demand logic
    if "data" in title or "ai" in title or "ml" in title:
        score += 40
    if "python" in title:
        score += 30
    if "remote" in location:
        score += 20

    return min(score, 100)
