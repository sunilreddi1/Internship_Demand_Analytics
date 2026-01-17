from PyPDF2 import PdfReader

SKILLS = [
    "python", "java", "sql", "machine learning", "data science",
    "html", "css", "javascript", "react", "django", "flask",
    "aws", "excel", "power bi"
]

def extract_skills_from_resume(pdf_file):
    reader = PdfReader(pdf_file)
    text = " ".join([p.extract_text() or "" for p in reader.pages]).lower()
    return list({skill for skill in SKILLS if skill in text})
