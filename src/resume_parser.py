from PyPDF2 import PdfReader

SKILLS = [
    "python", "java", "sql", "machine learning",
    "data science", "html", "css", "javascript",
    "react", "django", "flask"
]

def extract_skills_from_resume(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""

    for page in reader.pages:
        text += page.extract_text().lower()

    found_skills = [s for s in SKILLS if s in text]
    return list(set(found_skills))
