def live_internship_search(skill, location="India", domain="Any"):
    """
    Safe demo + API-ready internship search
    """

    data = [
        {
            "title": f"{skill} Intern",
            "company": "Tech Solutions Pvt Ltd",
            "location": location,
            "domain": "Software",
            "remote": False,
            "url": "https://internshala.com/"
        },
        {
            "title": f"Junior {skill} Internship",
            "company": "Innovate India",
            "location": "Remote",
            "domain": "AI/ML",
            "remote": True,
            "url": "https://www.linkedin.com/jobs/"
        },
        {
            "title": f"{skill} Internship",
            "company": "Startup Hub",
            "location": location,
            "domain": "Data Science",
            "remote": False,
            "url": "https://wellfound.com/"
        }
    ]

    if domain != "Any":
        data = [d for d in data if d["domain"] == domain]

    return data
