from flask import Flask, render_template, request, redirect, url_for, send_file, session
from werkzeug.utils import secure_filename
import os
import re
import PyPDF2
import spacy
import sqlite3

app = Flask(__name__)
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "skillgap-ai-local-development-key"
)

# ---------------- CONFIGURATION ----------------

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB

nlp = spacy.load("en_core_web_sm")
# ---------------- LEARNING DATABASE ----------------

def init_learning_database():

    conn = sqlite3.connect("learning_progress.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS learning_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            skill TEXT,
            task TEXT,
            study_day TEXT,
            duration REAL,
            completed INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            skill TEXT,
            score INTEGER,
            total_questions INTEGER
        )
    """)

    conn.commit()
    conn.close()

# ---------------- CAREER SKILLS ----------------

CAREERS = {
    "AI / ML Engineer": [
        "Python", "Machine Learning", "Artificial Intelligence",
        "SQL", "Statistics", "Data Science", "Git"
    ],

    "Data Analyst": [
        "Python", "SQL", "Excel", "Statistics",
        "Data Visualization", "Power BI", "Tableau"
    ],

    "Python Developer": [
        "Python", "Flask", "SQL", "Git", "GitHub", "APIs"
    ],

    "Full Stack Developer": [
        "HTML", "CSS", "JavaScript", "Python",
        "Flask", "SQL", "Git", "GitHub"
    ],

    "Data Engineer": [
        "Python", "SQL", "Hadoop", "Spark",
        "ETL", "Database", "Git"
    ]
}


# ---------------- SKILL DETECTION ----------------

ALL_SKILLS = [
    "Python", "Java", "C++", "SQL", "HTML", "CSS",
    "JavaScript", "Machine Learning", "Artificial Intelligence",
    "Data Science", "Statistics", "Excel", "Power BI",
    "Tableau", "Data Visualization", "Git", "GitHub",
    "Flask", "APIs", "Hadoop", "Spark", "ETL", "Database"
]


def normalize_text(text):
    """Prepare text for reliable skill matching."""
    text = text.lower()
    text = text.replace("c++", "cplusplus")
    text = text.replace("c#", "csharp")
    text = re.sub(r"[^a-z0-9+#.]", " ", text)
    return " ".join(text.split())


def extract_skills(text):
    """Find technical skills in resume text."""
    normalized_resume = normalize_text(text)

    found = []

    for skill in ALL_SKILLS:
        normalized_skill = normalize_text(skill)

        pattern = r"(?<![a-z0-9])" + re.escape(normalized_skill) + r"(?![a-z0-9])"

        if re.search(pattern, normalized_resume):
            found.append(skill)

    return found


def extract_nlp_keywords(text):
    """Extract meaningful nouns and proper nouns using spaCy."""
    doc = nlp(text[:100000])

    keywords = []

    for token in doc:
        if token.pos_ in ["NOUN", "PROPN"]:
            word = token.text.strip()

            if len(word) > 2 and word.isalpha():
                keywords.append(word.lower())

    return sorted(set(keywords))
# ---------------- RESUME CONTENT IMPROVEMENT ----------------

def get_resume_content_suggestions(text):

    suggestions = []

    weak_phrases = {
        "hardworking": "Use a specific achievement to demonstrate your work ethic.",
        "team player": "Describe how you collaborated with a team to complete a project.",
        "quick learner": "Mention a tool or technology you learned and how you applied it.",
        "good communication skills": "Provide an example of how you communicated or presented information.",
        "responsible for": "Start with a strong action verb such as Developed, Managed, or Implemented.",
        "worked on": "Explain exactly what you built, improved, or accomplished."
    }

    resume_lower = text.lower()

    for phrase, suggestion in weak_phrases.items():

        if phrase in resume_lower:
            suggestions.append({
                "phrase": phrase,
                "suggestion": suggestion
            })

    if not suggestions:
        suggestions.append({
            "phrase": "No common weak phrases detected",
            "suggestion": "Continue using specific action verbs and measurable achievements."
        })

    return suggestions


# ---------------- LEARNING ROADMAP ----------------

ROADMAP = {
    "Python": "Learn Python basics, functions, OOP and important libraries.",
    "Machine Learning": "Study supervised learning, regression, classification and model evaluation.",
    "Artificial Intelligence": "Understand AI fundamentals, intelligent agents and problem solving.",
    "SQL": "Practice SELECT, WHERE, JOIN, GROUP BY and database queries.",
    "Statistics": "Learn probability, distributions and hypothesis testing.",
    "Data Science": "Practice data cleaning, analysis and exploratory data analysis.",
    "Git": "Learn commits, branches, repositories and version control.",
    "Excel": "Learn formulas, pivot tables, charts and data analysis.",
    "Power BI": "Build dashboards and learn data modeling.",
    "Tableau": "Create interactive charts and dashboards.",
    "Flask": "Learn routes, templates, forms and REST APIs.",
    "GitHub": "Learn repositories, commits and project collaboration.",
    "APIs": "Understand REST APIs, HTTP requests and JSON.",
    "Hadoop": "Learn HDFS and MapReduce.",
    "Spark": "Understand distributed data processing.",
    "ETL": "Learn Extract, Transform and Load pipelines.",
    "Database": "Learn database design and SQL."
}


# ---------------- COURSE RECOMMENDATIONS ----------------

COURSES = {
    "Python": {
        "name": "Python Programming for Beginners",
        "url": "https://www.youtube.com/results?search_query=python+programming+for+beginners"
    },
    "Machine Learning": {
        "name": "Machine Learning Fundamentals",
        "url": "https://www.youtube.com/results?search_query=machine+learning+for+beginners"
    },
    "Artificial Intelligence": {
        "name": "Artificial Intelligence Basics",
        "url": "https://www.youtube.com/results?search_query=artificial+intelligence+for+beginners"
    },
    "SQL": {
        "name": "SQL and Database Fundamentals",
        "url": "https://www.youtube.com/results?search_query=sql+for+beginners"
    },
    "Statistics": {
        "name": "Statistics for Data Science",
        "url": "https://www.youtube.com/results?search_query=statistics+for+data+science"
    },
    "Data Science": {
        "name": "Data Science Fundamentals",
        "url": "https://www.youtube.com/results?search_query=data+science+for+beginners"
    },
    "Git": {
        "name": "Git and GitHub Fundamentals",
        "url": "https://www.youtube.com/results?search_query=git+github+for+beginners"
    },
    "Excel": {
        "name": "Excel for Data Analysis",
        "url": "https://www.youtube.com/results?search_query=excel+data+analysis+for+beginners"
    },
    "Power BI": {
        "name": "Power BI Dashboard Development",
        "url": "https://www.youtube.com/results?search_query=power+bi+for+beginners"
    },
    "Tableau": {
        "name": "Tableau Data Visualization",
        "url": "https://www.youtube.com/results?search_query=tableau+for+beginners"
    },
    "Flask": {
        "name": "Flask Web Development",
        "url": "https://www.youtube.com/results?search_query=flask+python+for+beginners"
    },
    "GitHub": {
        "name": "GitHub for Developers",
        "url": "https://www.youtube.com/results?search_query=github+for+beginners"
    },
    "APIs": {
        "name": "REST API Development",
        "url": "https://www.youtube.com/results?search_query=rest+api+for+beginners"
    },
    "Hadoop": {
        "name": "Hadoop and Big Data",
        "url": "https://www.youtube.com/results?search_query=hadoop+for+beginners"
    },
    "Spark": {
        "name": "Apache Spark Fundamentals",
        "url": "https://www.youtube.com/results?search_query=apache+spark+for+beginners"
    },
    "ETL": {
        "name": "ETL and Data Engineering",
        "url": "https://www.youtube.com/results?search_query=etl+data+engineering+for+beginners"
    },
    "Database": {
        "name": "Database Design and SQL",
        "url": "https://www.youtube.com/results?search_query=database+design+for+beginners"
    }
}
# ---------------- SKILL QUIZ QUESTIONS ----------------

QUIZ_QUESTIONS = {
    "Python": [
        {
            "question": "Which keyword is used to define a function in Python?",
            "options": ["function", "def", "define", "fun"],
            "answer": "def"
        },
        {
            "question": "Which data type stores True or False?",
            "options": ["int", "str", "bool", "list"],
            "answer": "bool"
        },
        {
            "question": "Which symbol is used for comments in Python?",
            "options": ["//", "#", "/*", "--"],
            "answer": "#"
        }
    ],

    "SQL": [
        {
            "question": "Which SQL command retrieves data from a table?",
            "options": ["GET", "OPEN", "SELECT", "FETCH ALL"],
            "answer": "SELECT"
        },
        {
            "question": "Which clause filters rows in SQL?",
            "options": ["ORDER BY", "WHERE", "GROUP BY", "JOIN"],
            "answer": "WHERE"
        },
        {
            "question": "Which function counts the number of rows?",
            "options": ["SUM()", "COUNT()", "TOTAL()", "NUMBER()"],
            "answer": "COUNT()"
        }
    ],

    "Machine Learning": [
        {
            "question": "Which type of learning uses labeled data?",
            "options": [
                "Unsupervised Learning",
                "Reinforcement Learning",
                "Supervised Learning",
                "Deep Learning"
            ],
            "answer": "Supervised Learning"
        },
        {
            "question": "Which algorithm is commonly used for classification?",
            "options": [
                "Linear Regression",
                "Logistic Regression",
                "K-Means",
                "PCA"
            ],
            "answer": "Logistic Regression"
        },
        {
            "question": "What is overfitting?",
            "options": [
                "Model performs well on training data but poorly on new data",
                "Model has no training data",
                "Model is always accurate",
                "Model uses fewer features"
            ],
            "answer": "Model performs well on training data but poorly on new data"
        }
    ]
}


# ---------------- CAREER RECOMMENDATIONS ----------------

CAREER_REASONS = {
    "AI / ML Engineer":
        "Your technical skills can help you build intelligent systems and machine learning solutions.",

    "Data Analyst":
        "Your data-related skills can help you analyze information and generate useful insights.",

    "Python Developer":
        "Your programming skills can help you develop Python applications and APIs.",

    "Full Stack Developer":
        "Your programming and web skills can help you build complete web applications.",

    "Data Engineer":
        "Your programming and database skills can help you build data pipelines."
}


def get_career_recommendations(found_skills):
    recommendations = []

    found_lower = {skill.lower() for skill in found_skills}

    for career, required_skills in CAREERS.items():

        matched = sum(
            1 for skill in required_skills
            if skill.lower() in found_lower
        )

        score = int((matched / len(required_skills)) * 100)

        recommendations.append({
            "career": career,
            "score": score,
            "reason": CAREER_REASONS[career]
        })

    recommendations.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return recommendations[:3]


# ---------------- SKILL RECOMMENDATIONS ----------------

def get_skill_recommendations(missing_skills, career):

    recommendations = []

    for skill in missing_skills:
        recommendations.append({
            "skill": skill,
            "reason": (
                f"{skill} is important for a {career} role. "
                "Learning this skill can improve your career readiness."
            )
        })

    return recommendations
# ---------------- PROJECT RECOMMENDATIONS ----------------

PROJECT_DATABASE = {
    "Python": {
        "name": "Student Management System",
        "description": "Build an application to manage student records using Python."
    },
    "Machine Learning": {
        "name": "House Price Prediction",
        "description": "Build an ML model to predict house prices using property data."
    },
    "Artificial Intelligence": {
        "name": "AI-Based Career Recommendation System",
        "description": "Develop a system that recommends careers based on user skills."
    },
    "SQL": {
        "name": "Student Database Management",
        "description": "Create a database to store and manage student information."
    },
    "Statistics": {
        "name": "Student Performance Analysis",
        "description": "Analyze student marks and identify performance patterns."
    },
    "Data Science": {
        "name": "Exploratory Data Analysis Project",
        "description": "Analyze a dataset and discover useful patterns and insights."
    },
    "Flask": {
        "name": "Personal Portfolio Website",
        "description": "Build a dynamic portfolio website using Python Flask."
    },
    "Git": {
        "name": "Version-Controlled Project",
        "description": "Manage a software project using Git branches and commits."
    },
    "Excel": {
        "name": "Sales Analysis Dashboard",
        "description": "Analyze sales data using Excel formulas and charts."
    },
    "Power BI": {
        "name": "Business Intelligence Dashboard",
        "description": "Create an interactive dashboard using Power BI."
    },
    "Tableau": {
        "name": "Data Visualization Dashboard",
        "description": "Build interactive visualizations using Tableau."
    },
    "GitHub": {
        "name": "Developer Project Portfolio",
        "description": "Publish and organize your coding projects on GitHub."
    },
    "APIs": {
        "name": "Weather Information Application",
        "description": "Build an application that retrieves weather information through an API."
    },
    "Hadoop": {
        "name": "Big Data Processing Project",
        "description": "Explore large datasets using Hadoop."
    },
    "Spark": {
        "name": "Large-Scale Data Analysis",
        "description": "Process and analyze large datasets using Apache Spark."
    },
    "ETL": {
        "name": "Data Pipeline Development",
        "description": "Build a pipeline to extract, transform and load data."
    },
    "Database": {
        "name": "Library Management System",
        "description": "Develop a database application to manage library records."
    }
}


def get_project_recommendations(missing_skills):

    recommendations = []

    for skill in missing_skills:
        if skill in PROJECT_DATABASE:
            project = PROJECT_DATABASE[skill]

            recommendations.append({
                "skill": skill,
                "name": project["name"],
                "description": project["description"]
            })

    return recommendations[:5]

# ---------------- STUDY PREFERENCES ----------------

@app.route("/study-preferences")
def study_preferences():

    return render_template("study_preferences.html")
@app.route("/generate-learning-schedule", methods=["POST"])
def generate_learning_schedule():
    selected_days = request.form.getlist("days")

    try:
        study_hours = float(request.form.get("study_hours", 1))
    except (ValueError, TypeError):
        return "Please enter valid study hours.", 400

    if not selected_days:
        return "Please select at least one study day.", 400

    if study_hours < 0.5 or study_hours > 8:
        return "Please select study hours between 0.5 and 8.", 400

    missing_skills = session.get("report_data", {}).get("missing_skills", [])

    if not missing_skills:
        return "Please analyze a resume first.", 400

    conn = sqlite3.connect("learning_progress.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM learning_tasks WHERE user_id = ?",
        ("default_user",)
    )

    for index, skill in enumerate(missing_skills):
        day = selected_days[index % len(selected_days)]

        cursor.execute("""
            INSERT INTO learning_tasks
            (user_id, skill, task, study_day, duration)
            VALUES (?, ?, ?, ?, ?)
        """, (
            "default_user",
            skill,
            f"Learn and practice {skill}",
            day,
            study_hours
        ))

    conn.commit()

    cursor.execute("""
        SELECT id, skill, task, study_day, duration, completed
        FROM learning_tasks
        WHERE user_id = ?
        ORDER BY CASE study_day
            WHEN 'Monday' THEN 1
            WHEN 'Tuesday' THEN 2
            WHEN 'Wednesday' THEN 3
            WHEN 'Thursday' THEN 4
            WHEN 'Friday' THEN 5
            WHEN 'Saturday' THEN 6
            WHEN 'Sunday' THEN 7
        END
    """, ("default_user",))

    schedule = cursor.fetchall()
    conn.close()

    return render_template(
        "learning_schedule.html",
        schedule=schedule
    )
# ---------------- HOME PAGE ----------------

@app.route("/")
def home():
    return render_template("index.html")


# ---------------- UPLOAD PAGE ----------------

@app.route("/upload")
def upload():
    return render_template(
        "upload.html",
        careers=CAREERS.keys()
    )


# ---------------- RESUME ANALYSIS ----------------

@app.route("/analyze", methods=["POST"])
def analyze():

    file = request.files.get("resume")
    career = request.form.get("career")
    job_description = request.form.get(
        "job_description", ""
    ).strip()

    if not file or file.filename == "":
        return "Please upload your resume PDF."

    if not file.filename.lower().endswith(".pdf"):
        return "Only PDF files are supported."

    if career not in CAREERS:
        return "Please select a valid career."

    filename = secure_filename(file.filename)

    if not filename:
        return "Invalid file name."

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename
    )

    file.save(filepath)

    # -------- Extract PDF Text --------

    try:
        text = ""

        with open(filepath, "rb") as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)

            if reader.is_encrypted:
                return "Please upload an unlocked PDF."

            for page in reader.pages:
                text += page.extract_text() or ""

    except Exception:
        return "Unable to read this PDF. Please try another file."

    if not text.strip():
        return (
            "No readable text found. "
            "Please upload a text-based PDF resume."
        )

    # -------- NLP Keyword Extraction --------

    nlp_keywords = extract_nlp_keywords(text)
    # -------- Resume Content Improvement --------

    resume_content_suggestions = get_resume_content_suggestions(text)

    # -------- Skill Detection --------

    found_skills = extract_skills(text)

    required_skills = CAREERS[career]

    missing_skills = [
        skill for skill in required_skills
        if skill.lower() not in {
            item.lower() for item in found_skills
        }
    ]

    matched = len(required_skills) - len(missing_skills)

    match_percentage = int(
        (matched / len(required_skills)) * 100
    )

    # -------- Job Description Matching --------

    job_match_percentage = 0

    if job_description:

        resume_normalized = normalize_text(text)
        job_normalized = normalize_text(job_description)

        job_skills = extract_skills(job_description)

        if job_skills:
            matched_job_skills = [
                skill for skill in job_skills
                if skill.lower() in {
                    item.lower() for item in found_skills
                }
            ]

            job_match_percentage = int(
                len(matched_job_skills) / len(job_skills) * 100
            )
        else:
            resume_words = set(resume_normalized.split())
            job_words = set(job_normalized.split())

            common_words = resume_words.intersection(job_words)

            job_match_percentage = int(
                len(common_words) / max(len(job_words), 1) * 100
            )

        job_match_percentage = min(job_match_percentage, 100)

    # -------- Career Recommendations --------

    career_recommendations = get_career_recommendations(
        found_skills
    )

    skill_recommendations = get_skill_recommendations(
        missing_skills, career
    )
    # -------- Project Recommendations --------

    project_recommendations = get_project_recommendations(
    missing_skills
    )

    # -------- Skill Priority --------

    skill_priority = []

    high_priority = [
        "Python", "Machine Learning",
        "Artificial Intelligence", "SQL"
    ]

    medium_priority = [
        "Statistics", "Data Science",
        "Data Visualization", "Git"
    ]

    for skill in missing_skills:

        if skill in high_priority:
            priority = "High"
        elif skill in medium_priority:
            priority = "Medium"
        else:
            priority = "Low"

        skill_priority.append({
            "skill": skill,
            "priority": priority
        })

    # -------- Learning Roadmap --------

    learning_roadmap = []

    for skill in missing_skills:
        if skill in ROADMAP:
            learning_roadmap.append({
                "skill": skill,
                "roadmap": ROADMAP[skill]
            })

    # -------- Course Recommendations --------

    learning_skills = (
        missing_skills if missing_skills else required_skills
    )

    course_recommendations = []

    for skill in learning_skills:
        if skill in COURSES:
            course_recommendations.append({
                "skill": skill,
                "course": COURSES[skill]
            })

    # -------- Improvement Suggestions --------

    improvement_suggestions = []

    if len(found_skills) < 5:
        improvement_suggestions.append(
            "Add more relevant technical skills to your resume."
        )

    if missing_skills:
        improvement_suggestions.append(
            "Focus on learning the missing skills for your selected career."
        )

    if "GitHub" not in found_skills:
        improvement_suggestions.append(
            "Create a GitHub profile and showcase your projects."
        )

    if "Git" not in found_skills:
        improvement_suggestions.append(
            "Learn Git to manage your project code."
        )

    if len(found_skills) >= 5:
        improvement_suggestions.append(
            "Keep your technical skills updated with current industry requirements."
        )

    # -------- Career Readiness --------

    if match_percentage >= 80:
        readiness_level = "Job Ready"
        readiness_message = (
            "Your skills strongly match the selected career."
        )

    elif match_percentage >= 60:
        readiness_level = "Almost Ready"
        readiness_message = (
            "You have a good foundation. Focus on the remaining skill gaps."
        )

    elif match_percentage >= 40:
        readiness_level = "Developing"
        readiness_message = (
            "Continue learning the missing skills and building projects."
        )

    else:
        readiness_level = "Needs Improvement"
        readiness_message = (
            "Focus on building the required technical skills and projects."
        )

    # -------- Resume Strength --------

    skill_score = min(len(found_skills) * 5, 40)
    gap_score = max(0, 30 - len(missing_skills) * 5)

    resume_strength = int(min(
        100,
        match_percentage * 0.5 + skill_score + gap_score
    ))

    # -------- ATS Score --------

    ats_score = 0

    if len(found_skills) >= 5:
        ats_score += 30
    elif len(found_skills) >= 3:
        ats_score += 20
    else:
        ats_score += 10

    if len(nlp_keywords) >= 10:
        ats_score += 25
    elif len(nlp_keywords) >= 5:
        ats_score += 15
    else:
        ats_score += 5

    if not missing_skills:
        ats_score += 30
    elif len(missing_skills) <= 2:
        ats_score += 25
    else:
        ats_score += 15

    if job_description:
        ats_score += int(job_match_percentage * 0.15)

    ats_score = min(ats_score, 100)
    # -------- Store Results for PDF Report --------
    session["report_data"] = {
        "career": career,
        "selected_career": career,
        "readiness_level": readiness_level,
        "readiness_message": readiness_message,
        "resume_strength": resume_strength,
        "career_match": match_percentage,
        "ats_score": ats_score,
        "job_match": job_match_percentage,
        "job_description": job_description,
        "found_skills": found_skills,
        "missing_skills": missing_skills,
        "skill_priority": skill_priority,
        "career_recommendations": career_recommendations,
        "learning_roadmap": learning_roadmap,
        "course_recommendations": course_recommendations,
        "improvement_suggestions": improvement_suggestions
    }

    # -------- Dashboard Result --------

    return render_template(
        "result.html",

        # Career details
        career=career,
        selected_career=career,

        # Skill details
        skills=found_skills,
        found_skills=found_skills,
        required_skills=required_skills,
        missing_skills=missing_skills,

        # Scores
        match_percentage=match_percentage,
        career_match=match_percentage,
        resume_strength=resume_strength,
        ats_score=ats_score,
        job_match_percentage=job_match_percentage,
        job_match=job_match_percentage,

        # Recommendations
        improvement_suggestions=improvement_suggestions,
        resume_content_suggestions=resume_content_suggestions,
        skill_priority=skill_priority,
        project_recommendations=project_recommendations,
        career_recommendations=career_recommendations,
        skill_recommendations=skill_recommendations,

        # Learning
        learning_roadmap=learning_roadmap,
        roadmap=[item["skill"] for item in learning_roadmap],
        course_recommendations=course_recommendations,

        # Readiness
        readiness_level=readiness_level,
        readiness_message=readiness_message,

        # NLP and job description
        nlp_keywords=nlp_keywords,
        job_description=job_description,
        resume_text=text,

    # Career chart data
    career_names=[
        item["career"] for item in career_recommendations
    ],
    career_scores=[
        item["score"] for item in career_recommendations
    ]
)
# ---------------- VIEW LEARNING SCHEDULE ----------------

@app.route("/learning-schedule")
def view_learning_schedule():

    conn = sqlite3.connect("learning_progress.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, skill, task, study_day, duration, completed
        FROM learning_tasks
        WHERE user_id = ?
        ORDER BY CASE study_day
            WHEN 'Monday' THEN 1
            WHEN 'Tuesday' THEN 2
            WHEN 'Wednesday' THEN 3
            WHEN 'Thursday' THEN 4
            WHEN 'Friday' THEN 5
            WHEN 'Saturday' THEN 6
            WHEN 'Sunday' THEN 7
        END
    """, ("default_user",))

    schedule = cursor.fetchall()
    conn.close()

    return render_template(
        "learning_schedule.html",
        schedule=schedule
    )
# ---------------- SKILL QUIZ QUESTIONS ----------------

QUIZ_QUESTIONS = {
    "Python": [
        {
            "question": "Which keyword is used to define a function in Python?",
            "options": ["function", "def", "define", "fun"],
            "answer": "def"
        },
        {
            "question": "Which data type stores True or False?",
            "options": ["int", "str", "bool", "list"],
            "answer": "bool"
        },
        {
            "question": "Which symbol is used for comments in Python?",
            "options": ["//", "#", "/*", "--"],
            "answer": "#"
        }
    ],

    "SQL": [
        {
            "question": "Which SQL command retrieves data from a table?",
            "options": ["GET", "OPEN", "SELECT", "FETCH ALL"],
            "answer": "SELECT"
        },
        {
            "question": "Which clause filters rows in SQL?",
            "options": ["ORDER BY", "WHERE", "GROUP BY", "JOIN"],
            "answer": "WHERE"
        },
        {
            "question": "Which function counts the number of rows?",
            "options": ["SUM()", "COUNT()", "TOTAL()", "NUMBER()"],
            "answer": "COUNT()"
        }
    ],

    "Machine Learning": [
        {
            "question": "Which type of learning uses labeled data?",
            "options": [
                "Unsupervised Learning",
                "Reinforcement Learning",
                "Supervised Learning",
                "Deep Learning"
            ],
            "answer": "Supervised Learning"
        },
        {
            "question": "Which algorithm is commonly used for classification?",
            "options": [
                "Linear Regression",
                "Logistic Regression",
                "K-Means",
                "PCA"
            ],
            "answer": "Logistic Regression"
        },
        {
            "question": "What is overfitting?",
            "options": [
                "Model performs well on training data but poorly on new data",
                "Model has no training data",
                "Model is always accurate",
                "Model uses fewer features"
            ],
            "answer": "Model performs well on training data but poorly on new data"
        }
    ]
}
# ---------------- COMPLETE LEARNING TASK ----------------

@app.route("/complete-learning-task", methods=["POST"])
def complete_learning_task():

    task_id = request.form.get("task_id")

    if not task_id or not task_id.isdigit():
        return "Invalid task ID.", 400

    conn = sqlite3.connect("learning_progress.db")
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE learning_tasks
        SET completed = 1
        WHERE id = ? AND user_id = ?
    """, (int(task_id), "default_user"))

    conn.commit()
    conn.close()

    return redirect(url_for("view_learning_schedule"))
# ---------------- PDF REPORT GENERATION ----------------

@app.route("/download-report")
def download_report():
    from playwright.sync_api import sync_playwright
    from flask import make_response

    report_data = session.get("report_data")

    if not report_data:
        return "Please analyze a resume before downloading the report.", 400

    html_content = render_template("report.html", **report_data)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        page.set_content(html_content, wait_until="networkidle")

        pdf_file = page.pdf(
            format="A4",
            print_background=True,
            prefer_css_page_size=True
        )

        browser.close()

    response = make_response(pdf_file)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = (
        'attachment; filename="SkillGap_AI_Resume_Report.pdf"'
    )

    return response
# ---------------- ERROR HANDLERS ----------------

@app.errorhandler(413)
def file_too_large(error):
    return "File is too large. Please upload a PDF under 10 MB.", 413

# ---------------- QUIZ SELECTION ----------------

@app.route("/quiz")
def quiz_home():

    missing_skills = session.get("report_data", {}).get(
        "missing_skills", []
    )

    available_quizzes = [
        skill for skill in missing_skills
        if skill in QUIZ_QUESTIONS
    ]

    return render_template(
        "quiz_home.html",
        available_quizzes=available_quizzes
    )


# ---------------- START QUIZ ----------------

@app.route("/start-quiz/<skill>")
def start_quiz(skill):

    questions = QUIZ_QUESTIONS.get(skill)

    if not questions:
        return "Quiz not available for this skill.", 404

    return render_template(
        "quiz.html",
        skill=skill,
        questions=questions
    )
# ---------------- SUBMIT QUIZ ----------------

@app.route("/submit-quiz", methods=["POST"])
def submit_quiz():

    skill = request.form.get("skill", "")
    questions = QUIZ_QUESTIONS.get(skill)

    if not questions:
        return "Quiz not available.", 404

    score = 0

    for index, question in enumerate(questions):
        selected_answer = request.form.get(f"answer_{index}")

        if selected_answer == question["answer"]:
            score += 1

    total_questions = len(questions)

    percentage = round((score / total_questions) * 100) if total_questions else 0

    conn = sqlite3.connect("learning_progress.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO quiz_results
        (user_id, skill, score, total_questions)
        VALUES (?, ?, ?, ?)
    """, ("default_user", skill, score, total_questions))

    conn.commit()
    conn.close()

    return render_template(
        "quiz_result.html",
        skill=skill,
        score=score,
        total_questions=total_questions,
        percentage=percentage
    )

# ---------------- RUN APPLICATION ----------------

if __name__ == "__main__":
    init_learning_database()
    app.run(debug=True)