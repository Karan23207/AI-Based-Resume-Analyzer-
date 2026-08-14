import os
import PyPDF2
from flask import Flask, redirect, url_for, session, render_template, request
from authlib.integrations.flask_client import OAuth
import re
from openai import OpenAI
import sqlite3
from dotenv import load_dotenv

load_dotenv()
DB_PATH = "database/resume.db"
app = Flask(__name__)

def init_db():

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS history (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_email TEXT,

        ats_score INTEGER,

        skills_count INTEGER,

        resume_rank TEXT,

        analysis TEXT,

        upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )

    """)

    conn.commit()

    conn.close()

init_db()

app.secret_key = os.getenv("FLASK_SECRET_KEY")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)
# GOOGLE OAUTH
oauth = OAuth(app)

google = oauth.register(
    name='google',

    client_id=os.getenv("GOOGLE_CLIENT_ID"),

    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),

    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',

    client_kwargs={
        'scope': 'openid email profile'
    }
)

@app.route("/")
def index():
    return render_template("landingpage.html")


# LOGIN ROUTE
@app.route('/login')
def login():

    redirect_uri = url_for('authorize', _external=True)

    return google.authorize_redirect(redirect_uri)



@app.route('/authorize')
def authorize():

    token = google.authorize_access_token()

    user_info = token['userinfo']

    session['user'] = user_info

    return redirect(url_for('dashboard'))


@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/")

    user = session['user']

    username = user['name']

    email = user['email']


    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("""

    SELECT ats_score,
           skills_count,
           resume_rank

    FROM history

    WHERE user_email = ?

    ORDER BY id DESC

    LIMIT 1

    """, (email,))

    result = cursor.fetchone()

    conn.close()


    if result:

        ats_score = result[0]

        skills_count = result[1]

        resume_rank = result[2]

    else:

        ats_score = 0

        skills_count = 0

        resume_rank = "N/A"


    return render_template(

        "dashboard.html",

        username=username,

        ats_score=ats_score,

        skills_count=skills_count,

        resume_rank=resume_rank
    )


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files['resume']

    UPLOAD_FOLDER = 'uploads'

    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    filepath = os.path.join("uploads", file.filename)
    # file saved
    file.save(filepath)

    # extracting text

    text = ""
    with open(filepath, 'rb') as Pdffile:
        reader = PyPDF2.PdfReader(Pdffile)

        total_pages = len(reader.pages)

        text = ""

        for page_num in range(total_pages):
            page = reader.pages[page_num]

            text += page.extract_text()

        print(text)

        # CLEAN TEXT
        text = text.replace("\n", " ").lower()
        text = text[:3000]

        # EMAIL EXTRACTION
        email = re.findall(r'\S+@\S+', text)

        # PHONE EXTRACTION
        phone = re.findall(r'\b\d{10}\b', text)

        # SKILL EXTRACTION
        skills = [
            "python",
            "java",
            "html",
            "css",
            "javascript",
            "sql",
            "flask",
            "react",
            "mysql",
            "machine learning"
        ]

        found_skills = []

        for skill in skills:
            if skill in text:
                found_skills.append(skill)

        # BASIC ATS SCORE
        score = 0

        score += len(found_skills) * 8

        if email:
            score += 10

        if phone:
            score += 10

        score = min(score, 100)

        # GEMINI PROMPT
        prompt = f"""
        You are an expert ATS Resume Analyzer.

        Analyze this resume professionally.

        Give:

        1. Resume Summary
        2. Strengths
        3. Weaknesses
        4. Missing Skills
        5. Improvement Suggestions
        6. Best Job Roles
        7. Interview Readiness

        Resume:
        {text}
        """

        # GEMINI RESPONSE
        analysis = ""

        try:

            response = client.chat.completions.create(
                model="deepseek/deepseek-chat",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            analysis = response.choices[0].message.content

        except Exception as e:

            analysis = """
            AI analysis temporarily unavailable due to API quota limit.

            Basic ATS analysis generated successfully.
            """

        user_email = session['user']['email']

        skills_count = len(found_skills)

        if score >= 85:

            resume_rank = "Top 5%"

        elif score >= 70:

            resume_rank = "Top 15%"

        elif score >= 50:

            resume_rank = "Top 30%"

        else:

            resume_rank = "Needs Improvement"

        conn = sqlite3.connect(DB_PATH)

        cursor = conn.cursor()

        cursor.execute("""

        INSERT INTO history
        (user_email,
         ats_score,
         skills_count,
         resume_rank,
         analysis)

        VALUES (?, ?, ?, ?, ?)

        """, (

            user_email,
            score,
            skills_count,
            resume_rank,
            analysis

        ))

        conn.commit()

        conn.close()

    return render_template(
        "Analysispage.html",
        score=score,
        skills=found_skills,
        analysis=analysis
    )

# history view logic
@app.route("/history")
def history():

    if "user" not in session:
        return redirect("/")

    email = session['user']['email']

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("""

    SELECT ats_score,
           skills_count,
           resume_rank,
           upload_time

    FROM history

    WHERE user_email = ?

    ORDER BY id DESC

    """, (email,))

    data = cursor.fetchall()

    conn.close()

    return render_template(
        "history.html",
        data=data
    )

# LOGOUT
@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)
