from PyPDF2 import PdfReader

DATASET_SKILLS = [
    "python","java","c","sql","mysql","postgresql",
    "react","node.js","express","fastapi",
    "data analysis","data science","machine learning",
    "nlp","ai","aws","excel",
    "communication","leadership"
]

def extract_skills_from_resume(pdf_file):
    reader = PdfReader(pdf_file)
    text = " ".join([p.extract_text() or "" for p in reader.pages]).lower()
    return [s for s in DATASET_SKILLS if s in text]
