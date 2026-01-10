from flask import Flask, render_template, request, redirect
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
    return data.decode("utf-8", errors="ignore")

# ------------------ SKILL LISTS ------------------
TECH_SKILLS = [
    "python", "sql", "data analysis", "data analytics",
    "data visualization", "data visualisation",
    "tableau", "power bi",
    "machine learning", "statistics"
]

SOFT_SKILLS = [
    "communication", "problem solving",
    "leadership", "team leader",
    "teamwork", "professionalism"
]

ALL_SKILLS = TECH_SKILLS + SOFT_SKILLS

# ------------------ MILESTONE-2: SKILL EXTRACTION ------------------
def spacy_extract(text, skills):
    doc = nlp(text.lower())
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    matcher.add("SKILLS", [nlp.make_doc(skill) for skill in skills])

    found = set()
    for _, start, end in matcher(doc):
        found.add(doc[start:end].text.lower())

    return sorted(found)

# ------------------ MILESTONE-3: BERT SIMILARITY ------------------
def bert_skill_gap(resume_skills, jd_skills):
    if not resume_skills or not jd_skills:
        return [], [], [], []

    resume_emb = bert_model.encode(resume_skills, convert_to_tensor=True)
    jd_emb = bert_model.encode(jd_skills, convert_to_tensor=True)

    similarity_matrix = util.cos_sim(jd_emb, resume_emb)

    matched = []
    partial = []
    missing = []
    heatmap = []

    for i, jd_skill in enumerate(jd_skills):
        scores = similarity_matrix[i].tolist()
        max_score = max(scores)

        heatmap.append([round(s, 2) for s in scores])

        if max_score >= 0.80:
            matched.append(jd_skill)
        elif max_score >= 0.50:
            partial.append(jd_skill)
        else:
            missing.append(jd_skill)

    return matched, partial, missing, heatmap

# ------------------ ROUTES ------------------
@app.route('/', methods=['GET', 'POST'])
def index():
    resume_text = ""
    jd_text = ""

    resume_skills = []
    jd_skills = []

    matched_skills = []
    partial_skills = []
    missing_skills = []
    heatmap = []

    if request.method == 'POST':
        resume = request.files.get('resume')
        jd = request.files.get('jd')

        if resume and allowed_file(resume.filename):
            data = resume.read()
            ext = resume.filename.rsplit('.', 1)[1].lower()
            resume_text = extract_pdf(data) if ext == 'pdf' else extract_docx(data) if ext == 'docx' else extract_txt(data)

        if jd and allowed_file(jd.filename):
            data = jd.read()
            ext = jd.filename.rsplit('.', 1)[1].lower()
            jd_text = extract_pdf(data) if ext == 'pdf' else extract_docx(data) if ext == 'docx' else extract_txt(data)

    if resume_text:
        resume_skills = spacy_extract(resume_text, ALL_SKILLS)

    if jd_text:
        jd_skills = spacy_extract(jd_text, ALL_SKILLS)

    matched_skills, partial_skills, missing_skills, heatmap = bert_skill_gap(
        resume_skills, jd_skills
    )

    return render_template(
        "index.html",
        resume_text=resume_text,
        jd_text=jd_text,
        resume_skills=resume_skills,
        jd_skills=jd_skills,
        matched_skills=matched_skills,
        partial_skills=partial_skills,
        missing_skills=missing_skills,
        heatmap=heatmap
    )

# ------------------ MILESTONE-4 REDIRECT ------------------
@app.route("/dashboard")
def dashboard():
    return redirect("http://localhost:8501")

# ------------------ RUN ------------------
if __name__ == "__main__":
    app.run(debug=True)
