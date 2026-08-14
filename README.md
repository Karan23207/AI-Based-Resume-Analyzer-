# 🤖 AI Resume Analyzer

![AI Resume Analyzer](static/cover-img.png)

An AI-powered web application that analyzes resumes and provides an ATS-style score, detected skills, resume ranking, and AI-generated career feedback. The application is built with **Python Flask**, **SQLite**, **PyPDF2**, **Google OAuth**, and an **OpenRouter-compatible AI API**.

## 🚀 Overview

The **AI Resume Analyzer** helps users understand how well their resume performs against common ATS (Applicant Tracking System) criteria.

A user can:

- Create an account / authenticate using Google
- Upload a PDF resume
- Extract resume text automatically
- Detect predefined technical skills
- Calculate an ATS-style score
- Receive an AI-generated resume analysis
- View a resume ranking based on the score
- View previous resume analysis records through History
- Analyze another resume from the dashboard

The landing page presents the project with a career-focused message, while the dashboard provides the main resume analysis workflow.

## ✨ Key Features

### 1. 🔐 Google Authentication

The application uses **Google OAuth 2.0** for user authentication. After successful authentication, the user's information is stored in the Flask session.

### 2. 📄 PDF Resume Upload

Users can upload their resume as a PDF. The application reads the PDF using **PyPDF2** and extracts text from all available pages.

### 3. 🧹 Resume Text Processing

The extracted text is normalized by:

- Removing newline characters
- Converting text to lowercase
- Limiting the analyzed text to the first 3000 characters

### 4. 🛠️ Skill Detection

The application currently checks the extracted resume text against a predefined list of skills, including:

- Python
- Java
- HTML
- CSS
- JavaScript
- SQL
- Flask
- React
- MySQL
- Machine Learning

Detected skills are displayed on the analysis result page.

### 5. 📊 ATS Score

A basic ATS-style score is calculated from detected skills and contact information.

Current scoring logic:

- Each detected skill → **+8 points**
- Email detected → **+10 points**
- 10-digit phone number detected → **+10 points**
- Maximum score → **100**

> **Note:** This is a project-specific scoring mechanism, not an official ATS score used by a particular company or recruitment platform.

### 6. 🧠 AI Resume Analysis

After the basic analysis, the extracted resume content is sent to an AI model through an OpenRouter-compatible API.

The AI is prompted to provide:

1. Resume Summary
2. Strengths
3. Weaknesses
4. Missing Skills
5. Improvement Suggestions
6. Best Job Roles
7. Interview Readiness

The current implementation uses the `deepseek/deepseek-chat` model through OpenRouter.

### 7. 🏆 Resume Ranking

The application converts the ATS score into a simple ranking category:

| ATS Score | Resume Rank |
|---:|---|
| 85–100 | Top 5% |
| 70–84 | Top 15% |
| 50–69 | Top 30% |
| Below 50 | Needs Improvement |

### 8. 📈 Dashboard

The dashboard displays the user's latest:

- ATS Score
- Skills Matched
- Resume Rank

It also provides direct navigation to resume analysis and history.

### 9. 🕘 Resume History

Every analysis is stored in SQLite. Users can view previous analysis records containing:

- ATS Score
- Number of detected skills
- Resume Rank
- Upload date/time

## 🏗️ Application Workflow

```text
User
  │
  ▼
Landing Page
  │
  ▼
Google Login
  │
  ▼
Dashboard
  │
  ▼
Upload PDF Resume
  │
  ▼
Extract Text using PyPDF2
  │
  ▼
Clean Resume Text
  │
  ├───────────────┐
  ▼               ▼
Skill Detection   Contact Detection
  │               │
  └───────┬───────┘
          ▼
      ATS Score
          │
          ▼
   AI Resume Analysis
          │
          ▼
   Save Result to SQLite
          │
          ▼
    Analysis Result
          │
          ▼
       History
```

## 🧰 Tech Stack

### Backend

- **Python**
- **Flask**
- **PyPDF2**
- **SQLite**
- **Authlib**
- **OpenAI Python SDK**

### AI

- **OpenRouter API**
- **DeepSeek Chat model**

### Frontend

- **HTML5**
- **CSS3**
- **Bootstrap 5**
- **JavaScript**

### Authentication

- **Google OAuth 2.0**

## 📁 Project Structure

A typical project structure for this application is:

```text
AI-Resume-Analyzer/
│
├── main.py
│
├── database/
│   └── resume.db
│
├── templates/
│   ├── landingpage.html
│   ├── register.html
│   ├── dashboard.html
│   ├── Analysispage.html
│   └── history.html
│
├── static/
│   ├── style.css
│   ├── dashboard.css
│   ├── result.css
│   └── cover-img.png
│
├── uploads/
│   └── uploaded resumes
│
└── README.md
```

## 🗄️ Database

The project uses **SQLite** to store resume analysis history.

The `history` table contains:

| Column | Description |
|---|---|
| `id` | Unique analysis ID |
| `user_email` | Email of the authenticated user |
| `ats_score` | Calculated ATS score |
| `skills_count` | Number of detected skills |
| `resume_rank` | Resume ranking category |
| `analysis` | AI-generated analysis |
| `upload_time` | Analysis upload timestamp |

The database is initialized automatically when the Flask application starts.

## ⚙️ Installation & Setup

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd AI-Resume-Analyzer
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install flask PyPDF2 authlib openai
```

### 4. Configure API credentials

Do **not** hard-code API keys or OAuth secrets in `main.py`.

Create environment variables for:

```text
OPENROUTER_API_KEY=your_openrouter_api_key
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

The Google OAuth callback must also be configured correctly in your Google Cloud project.

### 5. Run the application

```bash
python main.py
```

The Flask development server will start locally.

Open the application in your browser using the local address shown by Flask.

## 🔑 Important Security Note

API keys, OAuth client secrets, and Flask secret keys should never be committed to GitHub.

If credentials have previously been exposed in source code, **rotate/revoke them and replace them with environment variables** before publishing the repository.

For production, also replace Flask's development secret key with a strong secret stored securely outside the source code.

## 🖥️ Main Pages

### Landing Page

Introduces the application and provides the login entry point.

### Dashboard

Shows the user's latest resume metrics and provides the resume upload interface.

### Analysis Page

Displays:

- ATS score
- Detected skills
- AI-generated resume analysis
- Navigation to the dashboard
- Option to analyze another resume

### History Page

Displays previous resume analysis results for the authenticated user.

## 🎯 Example Use Case

A student uploads a resume containing Python, SQL, Flask, HTML, and JavaScript.

The application:

1. Extracts the resume text.
2. Detects the listed skills.
3. Checks for email and phone information.
4. Calculates the ATS-style score.
5. Sends the resume content to the AI model.
6. Generates strengths, weaknesses, missing skills, job-role suggestions, and interview-readiness feedback.
7. Stores the result in SQLite.
8. Displays the complete analysis to the user.

## 🔮 Future Improvements

The current project can be extended with:

- Job Description vs Resume matching
- Semantic similarity using embeddings
- More advanced NLP-based skill extraction
- Industry-specific ATS scoring
- Resume section detection
- Keyword recommendations
- Resume formatting checks
- Multiple resume versions
- Downloadable analysis reports
- Admin dashboard
- Better authentication and password security
- Cloud database integration
- Deployment using Docker
- Production-grade error handling
- Secure file validation and upload limits

## 📌 Current Limitations

- Skill detection currently uses a predefined skill list.
- ATS scoring is rule-based.
- Only PDF resume processing is implemented in the current upload flow.
- Resume text is limited to 3000 characters before analysis.
- AI analysis depends on external API availability/quota.
- The current ranking is a score-based project ranking, not a real percentile calculated from a population of resumes.

## 📄 License

This project is intended for educational and portfolio purposes.

## 👨‍💻 Author

**Karan Rawal**

B.Tech – Computer Science / CSE (AI & ML)

---

⭐ If you find this project useful, consider giving the repository a star!
