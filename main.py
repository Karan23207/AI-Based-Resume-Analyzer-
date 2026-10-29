
import os
import uuid
import re
import sqlite3
from flask import Flask, redirect, url_for, session, render_template, request
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from openai import OpenAI
from werkzeug.utils import secure_filename

import pymupdf as fitz  # PyMuPDF for robust PDF extraction
from PIL import Image
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

load_dotenv()
DB_PATH = "database/resume.db"
app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # Limit file size to 5MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE


class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            ats_score INTEGER,
            skills_count INTEGER,
            resume_rank TEXT,
            analysis TEXT,
            job_description TEXT,
            upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()
        conn.close()

    def save_history(self, user_email, score, skills_count, resume_rank, analysis, job_description):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO history (user_email, ats_score, skills_count, resume_rank, analysis, job_description)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (user_email, score, skills_count, resume_rank, analysis, job_description))
        conn.commit()
        conn.close()

    def get_latest_history(self, email):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
        SELECT ats_score, skills_count, resume_rank FROM history
        WHERE user_email = ? ORDER BY id DESC LIMIT 1
        """, (email,))
        result = cursor.fetchone()
        conn.close()
        return result

    def get_all_history(self, email):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
        SELECT ats_score, skills_count, resume_rank, upload_time FROM history
        WHERE user_email = ? ORDER BY id DESC
        """, (email,))
        data = cursor.fetchall()
        conn.close()
        return data

class ResumeAnalyzer:
    SKILL_CATEGORIES = {
        "programming": ["python", "java", "c++", "c", "javascript"],
        "web": ["html", "css", "react", "node.js", "flask", "express"],
        "database": ["sql", "mysql", "mongodb", "postgresql"],
        "ai_ml": ["machine learning", "deep learning", "tensorflow", "pytorch", "nlp"],
        "tools": ["git", "github", "docker", "aws", "linux"]
    }

    def __init__(self, resume_text, job_description):
        self.resume_text = resume_text.lower()
        self.job_description = job_description.lower()

    def extract_skills(self, text):
        text = text.lower()
        found_skills = []
        for category in self.SKILL_CATEGORIES.values():
            for skill in category:
                pattern = r"(?<!\w)" + re.escape(skill) + r"(?!\w)"
                if re.search(pattern, text):
                    found_skills.append(skill)
        return list(set(found_skills))

    def calculate_ats_score(self):
        resume_skills = self.extract_skills(self.resume_text)
        required_skills = self.extract_skills(self.job_description)

        matched_skills = list(set(resume_skills) & set(required_skills))
        missing_skills = list(set(required_skills) - set(resume_skills))

        # Skill Score (Max 50)
        skill_score = (len(matched_skills) / len(required_skills)) * 50 if required_skills else 25

        # Contact Score (Max 10)
        contact_score = 0
        if re.search(r"\S+@\S+", self.resume_text):
            contact_score += 5
        if re.search(r"\b\d{10}\b", self.resume_text):
            contact_score += 5

        # Education Score (Max 15)
        edu_keywords = ["b.tech", "btech", "b.e", "bachelor", "degree", "computer science", "education"]
        education_score = 15 if any(kw in self.resume_text for kw in edu_keywords) else 0

        # Experience Score (Max 15)
        exp_keywords = ["experience", "project", "internship", "developer", "engineer"]
        experience_score = 15 if any(kw in self.resume_text for kw in exp_keywords) else 0

        # Completeness Score (Max 10)
        completeness_score = 10 if len(self.resume_text) >= 300 else 5

        total_score = skill_score + contact_score + education_score + experience_score + completeness_score

        return {
            "score": min(round(total_score), 100),
            "resume_skills": resume_skills,
            "required_skills": required_skills,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills
        }


db_manager = DatabaseManager(DB_PATH)
db_manager.init_db()

app.secret_key = os.getenv("FLASK_SECRET_KEY")

ai_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)



def allowed_file(filename):
    """Check if uploaded file extension matches the safe whitelist."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_text_from_file(filepath, extension):
    """Dynamically handle structured/unstructured PDFs via PyMuPDF or images via Tesseract OCR."""
    extracted_text = ""

    if extension == 'pdf':
        try:
            # PyMuPDF handles complex, multi-column, and unstructured PDF layouts effectively
            with fitz.open(filepath) as doc:
                for page in doc:
                    extracted_text += page.get_text()
        except Exception as e:
            print(f"PDF extraction error: {e}")

    elif extension in {'png', 'jpg', 'jpeg'}:
        try:
            # Uses Pillow to load the image and Tesseract to perform OCR extraction
            image = Image.open(filepath)
            extracted_text = pytesseract.image_to_string(image)
        except Exception as e:
            print(f"OCR extraction error: {e}")

    return extracted_text


# ---------------- FLASK ROUTES ----------------

@app.route("/")
def index():
    return render_template("landingpage.html")


@app.route('/login')
def login():
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route('/authorize')
def authorize():
    token = google.authorize_access_token()
    session['user'] = token['userinfo']
    return redirect(url_for('dashboard'))


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    user = session['user']
    result = db_manager.get_latest_history(user['email'])

    if result:
        ats_score, skills_count, resume_rank = result
    else:
        ats_score, skills_count, resume_rank = 0, 0, "N/A"

    return render_template("dashboard.html", username=user['name'], ats_score=ats_score, skills_count=skills_count,
                           resume_rank=resume_rank)


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("resume")
    job_description = request.form.get("job_description", "").strip()

    if not file or file.filename == "":
        return "Please upload a resume file.", 400
    if not job_description:
        return "Please enter a job description.", 400

    # 1. Security Check: Validate file extension
    if not allowed_file(file.filename):
        return "Invalid file type. Only PDF, PNG, JPG, and JPEG files are permitted.", 400

    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    # 2. Security Check: Prevent path traversal and filename collisions using UUID
    ext = file.filename.rsplit('.', 1)[1].lower()
    secure_name = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4()}_{secure_name}"
    filepath = os.path.join(UPLOAD_FOLDER, unique_filename)

    file.save(filepath)

    # 3. Extract text robustly (supports unstructured PDFs and Images via OCR)
    raw_text = extract_text_from_file(filepath, ext)

    # 4. Clean up the uploaded file from the server immediately after extraction
    try:
        os.remove(filepath)
    except OSError:
        pass

    if not raw_text.strip():
        return "Could not extract any readable text from the document. Please check your file.", 400

    text = raw_text.replace("\n", " ").lower()[:3000]

    analyzer = ResumeAnalyzer(text, job_description)
    ats_result = analyzer.calculate_ats_score()

    score = ats_result["score"]
    found_skills = ats_result["matched_skills"]
    missing_skills = ats_result["missing_skills"]

    prompt = f"""
    You are an expert ATS Resume Analyzer. Analyze the resume based on the job description.
    Job Description: {job_description}
    Resume: {text}
    ATS Score: {score}/100
    Matched Skills: {found_skills}
    Missing Skills: {missing_skills}
    Provide: Summary, Match, Strengths, Weaknesses, Missing Skills, Suggestions, Roles, Interview Prep.
    """

    try:
        response = ai_client.chat.completions.create(
            model="deepseek/deepseek-chat",
            messages=[{"role": "user", "content": prompt}]
        )
        analysis = response.choices[0].message.content
    except Exception:
        analysis = "AI analysis temporarily unavailable due to API limits. Basic ATS analysis generated."

    # Save via DatabaseManager class
    db_manager.save_history(
        user_email=session['user']['email'],
        score=score,
        skills_count=len(found_skills),
        resume_rank="JD Match",
        analysis=analysis,
        job_description=job_description
    )

    return render_template("Analysispage.html", score=score, skills=found_skills, missing_skills=missing_skills,
                           analysis=analysis)


@app.route("/history")
def history():
    if "user" not in session:
        return redirect("/")

    data = db_manager.get_all_history(session['user']['email'])
    return render_template("history.html", data=data)


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)

