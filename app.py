from flask import Flask, render_template, request
import pdfplumber
from docx import Document
from io import BytesIO

app = Flask(__name__)

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

@app.errorhandler(413)
def file_too_large(e):
    return render_template(
        'index.html',
        resume_text="",
        jd_text="",
        error_msg="File too large. Maximum size is 5 MB."
    ), 413

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

@app.route('/', methods=['GET', 'POST'])
def index():
    resume_text = ""
    jd_text = ""
    error_msg = ""

    if request.method == 'POST':
        resume = request.files.get('resume')
        jd = request.files.get('jd')

        if resume and resume.filename:
            if allowed_file(resume.filename):
                data = resume.read()
                ext = resume.filename.rsplit('.', 1)[1].lower()
                if ext == 'pdf':
                    resume_text = extract_pdf(data)
                elif ext == 'docx':
                    resume_text = extract_docx(data)
                elif ext == 'txt':
                    resume_text = extract_txt(data)
            else:
                error_msg = "Invalid resume format"

        if jd and jd.filename:
            if allowed_file(jd.filename):
                data = jd.read()
                ext = jd.filename.rsplit('.', 1)[1].lower()
                if ext == 'pdf':
                    jd_text = extract_pdf(data)
                elif ext == 'docx':
                    jd_text = extract_docx(data)
                elif ext == 'txt':
                    jd_text = extract_txt(data)
            else:
                error_msg = "Invalid job description format"

    return render_template(
        'index.html',
        resume_text=resume_text,
        jd_text=jd_text,
        error_msg=error_msg
    )

if __name__ == '__main__':
    app.run(debug=True)
