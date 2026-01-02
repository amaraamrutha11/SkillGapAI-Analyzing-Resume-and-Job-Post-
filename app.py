from flask import Flask, render_template, request
import pdfplumber
from docx import Document
from io import BytesIO
import spacy
from spacy.matcher import PhraseMatcher
from sentence_transformers import SentenceTransformer, util

# ------------------ LOAD MODELS ------------------
nlp = spacy.load("en_core_web_sm")
bert_model = SentenceTransformer("all-MiniLM-L6-v2")

app = Flask(__name__)

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

# ------------------ ERROR HANDLER ------------------
@app.errorhandler(413)
def file_too_large(e):
    return render_template(
        'index.html',
        resume_text="",
        jd_text="",
        error_msg="File too large. Maximum size is 5 MB."
    ), 413

# ------------------ FILE HELPERS ------------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_pdf(data):
    text = ""
    with pdfplumber.open(BytesIO(data)) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def extract_docx(data):
    doc = Document(BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs)

def extract_txt(data):
    return data.decode('utf-8', errors='ignore')

# ------------------ SKILL LISTS ------------------
TECH_SKILLS = [
    "python", "sql",
    "data analysis", "data analytics",
    "data visualization", "data visualisation",
    "tableau", "power bi",
    "dashboard", "dashboards"
]

SOFT_SKILLS = [
    "communication",
    "problem solving", "problem-solving",
    "leadership", "team leader", "team leadership",
    "professionalism",
    "english communication"
]

ALL_SKILLS = TECH_SKILLS + SOFT_SKILLS

# ------------------ KEYWORD EXTRACTION ------------------
def extract_skills(text, skill_list):
    text = text.lower()
    found_skills = set()
    for skill in skill_list:
        if skill.lower() in text:
            found_skills.add(skill)
    return sorted(found_skills)

# ------------------ spaCy EXTRACTION ------------------
def spacy_skill_extractor(text, skills):
    doc = nlp(text.lower())
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    patterns = [nlp.make_doc(skill) for skill in skills]
    matcher.add("SKILLS", patterns)

    matches = matcher(doc)
    found_skills = set()
    for _, start, end in matches:
        found_skills.add(doc[start:end].text.lower())

    return sorted(found_skills)

# ------------------ BERT EXTRACTION ------------------
def bert_skill_extractor(text, skills, threshold=0.6):
    sentences = [sent.text for sent in nlp(text).sents]
    skill_embeddings = bert_model.encode(skills, convert_to_tensor=True)

    found = set()
    for sentence in sentences:
        sent_embedding = bert_model.encode(sentence, convert_to_tensor=True)
        similarities = util.cos_sim(sent_embedding, skill_embeddings)[0]

        for idx, score in enumerate(similarities):
            if score >= threshold:
                found.add(skills[idx])

    return sorted(found)

# ------------------ SKILL GAP ------------------
def calculate_skill_gap(resume_skills, jd_skills):
    resume_set = set(resume_skills)
    jd_set = set(jd_skills)

    matched_skills = sorted(resume_set & jd_set)
    missing_skills = sorted(jd_set - resume_set)

    match_percentage = 0
    if jd_set:
        match_percentage = round((len(matched_skills) / len(jd_set)) * 100, 2)

    return matched_skills, missing_skills, match_percentage

# ------------------ ROUTE ------------------
@app.route('/', methods=['GET', 'POST'])
def index():
    resume_text = ""
    jd_text = ""
    error_msg = ""

    resume_skills = []
    jd_skills = []

    matched_skills = []
    missing_skills = []
    match_percentage = 0

    if request.method == 'POST':
        resume = request.files.get('resume')
        jd = request.files.get('jd')

        if resume and resume.filename and allowed_file(resume.filename):
            data = resume.read()
            ext = resume.filename.rsplit('.', 1)[1].lower()
            if ext == 'pdf':
                resume_text = extract_pdf(data)
            elif ext == 'docx':
                resume_text = extract_docx(data)
            elif ext == 'txt':
                resume_text = extract_txt(data)

        if jd and jd.filename and allowed_file(jd.filename):
            data = jd.read()
            ext = jd.filename.rsplit('.', 1)[1].lower()
            if ext == 'pdf':
                jd_text = extract_pdf(data)
            elif ext == 'docx':
                jd_text = extract_docx(data)
            elif ext == 'txt':
                jd_text = extract_txt(data)

    # -------- RESUME SKILLS --------
    if resume_text:
        resume_skills = set()
        resume_skills |= set(extract_skills(resume_text, ALL_SKILLS))
        resume_skills |= set(spacy_skill_extractor(resume_text, ALL_SKILLS))
        resume_skills |= set(bert_skill_extractor(resume_text, ALL_SKILLS))

    # -------- JD SKILLS --------
    if jd_text:
        jd_skills = set()
        jd_skills |= set(extract_skills(jd_text, ALL_SKILLS))
        jd_skills |= set(spacy_skill_extractor(jd_text, ALL_SKILLS))
        jd_skills |= set(bert_skill_extractor(jd_text, ALL_SKILLS))

    # -------- GAP --------
    matched_skills, missing_skills, match_percentage = calculate_skill_gap(
        resume_skills, jd_skills
    )

    return render_template(
        'index.html',
        resume_text=resume_text,
        jd_text=jd_text,
        error_msg=error_msg,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        match_percentage=match_percentage
    )

# ------------------ RUN ------------------
if __name__ == '__main__':
    app.run(debug=True)
