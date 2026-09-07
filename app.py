# CAPSTONE PROJECT — STREAMLIT APPLICATION
# Student Skill Gap Analysis and Career Recommendation System
# ============================================================

import streamlit as st
import pandas as pd
from pathlib import Path
import re




# ============================================================
# RESUME TEXT EXTRACTION HELPER
# ============================================================

def extract_resume_text(uploaded_file):
    """Extract text from an uploaded TXT, PDF, or DOCX resume."""

    if uploaded_file is None:
        return "", None

    file_name = uploaded_file.name.lower()

    try:
        uploaded_file.seek(0)

        if file_name.endswith(".txt"):
            raw_text = uploaded_file.read()
            if isinstance(raw_text, bytes):
                resume_text = raw_text.decode("utf-8", errors="ignore")
            else:
                resume_text = str(raw_text)

        elif file_name.endswith(".pdf"):
            try:
                from pypdf import PdfReader
            except ImportError:
                return "", (
                    "PDF extraction requires the 'pypdf' package. "
                    "Add pypdf to requirements.txt."
                )

            reader = PdfReader(uploaded_file)
            resume_text = "\n".join(
                page.extract_text() or ""
                for page in reader.pages
            )

        elif file_name.endswith(".docx"):
            try:
                from docx import Document
            except ImportError:
                return "", (
                    "DOCX extraction requires the 'python-docx' package. "
                    "Add python-docx to requirements.txt."
                )

            document = Document(uploaded_file)
            resume_text = "\n".join(
                paragraph.text
                for paragraph in document.paragraphs
                if paragraph.text.strip()
            )

        else:
            return "", "Unsupported resume file type."

        resume_text = resume_text.strip()

        if not resume_text:
            return "", (
                "The resume was uploaded, but no readable text could be "
                "extracted. Scanned/image-only PDFs may require OCR."
            )

        return resume_text, None

    except Exception as error:
        return "", f"Resume text extraction failed: {error}"




# ============================================================
# RESUME INFORMATION EXTRACTION HELPER
# ============================================================

def extract_resume_information(resume_text):
    """Extract a simple, transparent candidate profile from resume text."""

    text = resume_text or ""
    text_lower = text.lower()
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    # Education level
    education_level = "Not identified"
    education_patterns = [
        ("Doctoral Degree", ["phd", "ph.d", "doctor of philosophy", "doctorate"]),
        ("Master's Degree", ["master of", "master's", "masters", "m.sc", "msc", "m.s.", "mba", "mca"]),
        ("Bachelor's Degree", ["bachelor of", "bachelor's", "bachelors", "b.sc", "bsc", "b.s.", "btech", "b.tech", "bca"]),
        ("Certificate / Diploma", ["diploma", "certificate program", "postgraduate certificate", "graduate certificate"]),
        ("High School", ["high school", "secondary school"]),
    ]
    for level, keywords in education_patterns:
        if any(keyword in text_lower for keyword in keywords):
            education_level = level
            break

    # Field of study: pull a likely degree line when possible
    field_of_study = "Not identified"
    degree_markers = (
        "master", "bachelor", "b.sc", "bsc", "m.sc", "msc",
        "mba", "btech", "b.tech", "mca", "bca", "diploma"
    )
    for line in lines:
        if any(marker in line.lower() for marker in degree_markers):
            field_of_study = line[:180]
            break

    # Years of experience: use the largest explicit "X years" statement
    years_matches = re.findall(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)", text_lower)
    years_experience = "Not identified"
    if years_matches:
        try:
            years_experience = f"{max(float(x) for x in years_matches):g} years"
        except ValueError:
            pass

    # Skills and tools. These are deliberately explicit keyword matches so
    # the demo remains interpretable rather than pretending to be an LLM parser.
    skill_keywords = [
        "data analysis", "data analytics", "machine learning", "deep learning",
        "natural language processing", "nlp", "statistical analysis",
        "business analysis", "data visualization", "reporting",
        "communication", "problem solving", "critical thinking",
        "leadership", "teamwork", "customer service", "project management",
        "research", "forecasting", "optimization", "database management",
        "software development", "web development", "requirements analysis",
        "active listening", "monitoring", "reading comprehension",
        "speaking", "writing", "mathematics", "science"
    ]

    tool_keywords = [
        "python", "sql", "power bi", "tableau", "excel", "r studio",
        "r programming", "databricks", "spark", "pyspark", "scikit-learn",
        "tensorflow", "pytorch", "pandas", "numpy", "faiss", "spacy",
        "streamlit", "github", "git", "java", "javascript", "html",
        "css", "react", "spring", "mongodb", "mysql", "postgresql",
        "oracle", "aws", "azure", "google cloud", "jira", "salesforce"
    ]

    detected_skills = []
    for skill in skill_keywords:
        if skill in text_lower:
            label = "NLP" if skill == "nlp" else skill.title()
            if label not in detected_skills:
                detected_skills.append(label)

    detected_tools = []
    for tool in tool_keywords:
        if tool in text_lower:
            display = {
                "sql": "SQL", "power bi": "Power BI", "r studio": "RStudio",
                "r programming": "R", "pyspark": "PySpark", "faiss": "FAISS",
                "spacy": "spaCy", "github": "GitHub", "git": "Git",
                "java": "Java", "javascript": "JavaScript", "html": "HTML",
                "css": "CSS", "mongodb": "MongoDB", "mysql": "MySQL",
                "postgresql": "PostgreSQL", "aws": "AWS", "azure": "Azure"
            }.get(tool, tool.title())
            if display not in detected_tools:
                detected_tools.append(display)

    # Certification lines
    certification_lines = []
    for line in lines:
        low = line.lower()
        if any(k in low for k in ["certification", "certified", "certificate"]):
            if line not in certification_lines:
                certification_lines.append(line[:180])
        if len(certification_lines) >= 5:
            break

    # Experience/project highlights
    highlight_lines = []
    action_terms = [
        "developed", "built", "created", "designed", "implemented",
        "analyzed", "managed", "supervised", "led", "supported",
        "maintained", "coordinated", "trained", "project", "experience"
    ]
    for line in lines:
        if any(term in line.lower() for term in action_terms) and len(line) >= 25:
            if line not in highlight_lines:
                highlight_lines.append(line[:220])
        if len(highlight_lines) >= 6:
            break

    return {
        "Education Level": education_level,
        "Education / Field Evidence": field_of_study,
        "Years of Experience": years_experience,
        "Detected Skills": ", ".join(detected_skills) if detected_skills else "No configured skill keywords detected",
        "Detected Software / Tools": ", ".join(detected_tools) if detected_tools else "No configured tool keywords detected",
        "Certifications": " | ".join(certification_lines) if certification_lines else "Not identified",
        "Experience / Project Highlights": " | ".join(highlight_lines) if highlight_lines else "Not identified",
    }


# ============================================================
# LIVE RESUME CAREER RECOMMENDATION HELPER — IMPROVED
# ============================================================

def generate_resume_career_recommendations(
    resume_text,
    top5_recommendations,
    top_n=5
):
    """
    Generate transparent live recommendations for a newly uploaded resume.

    Score composition:
        40% occupation skill/tool evidence
        30% education / field alignment
        20% experience / occupation evidence
        10% Canadian labour demand

    IMPORTANT:
    This is a deployment/demo inference path for a new resume.
    It is separate from the validated 63-candidate Week 8 evaluation.
    """

    text = (resume_text or "").lower()

    # --------------------------------------------------------
    # 1. Occupation-specific evidence profiles
    # --------------------------------------------------------
    occupation_profiles = {
        "software developer": {
            "skills": [
                "software development", "programming", "java", "javascript",
                "python", "sql", "api", "backend", "frontend", "full stack",
                "spring", "react", "git", "github", "html", "css"
            ],
            "education": [
                "computer science", "information technology",
                "software engineering", "computer engineering",
                "computing", "data analytics"
            ],
            "experience": [
                "developer", "software engineer", "programmer",
                "developed", "implemented", "built", "designed",
                "debugging", "testing", "application", "web application"
            ],
        },
        "software engineer": {
            "skills": [
                "software engineering", "software development", "programming",
                "java", "javascript", "python", "system design", "api",
                "backend", "frontend", "testing", "git", "github"
            ],
            "education": [
                "computer science", "software engineering",
                "computer engineering", "information technology"
            ],
            "experience": [
                "software engineer", "developer", "programmer",
                "designed", "developed", "implemented",
                "testing", "system design"
            ],
        },
        "data scientist": {
            "skills": [
                "data science", "machine learning", "python", "sql",
                "statistics", "statistical analysis", "pandas", "numpy",
                "scikit-learn", "tensorflow", "pytorch", "nlp",
                "forecasting", "data analytics", "data analysis"
            ],
            "education": [
                "data science", "data analytics", "computer science",
                "statistics", "mathematics", "artificial intelligence"
            ],
            "experience": [
                "data scientist", "data analyst", "analyzed", "model",
                "machine learning", "predictive", "forecasting",
                "data project", "analytics project"
            ],
        },
        "information systems specialist": {
            "skills": [
                "information systems", "systems analysis", "it support",
                "technical support", "requirements analysis", "database",
                "sql", "network", "systems", "jira", "business systems"
            ],
            "education": [
                "information systems", "information technology",
                "computer science", "computer engineering"
            ],
            "experience": [
                "systems analyst", "it analyst", "technical support",
                "supported", "requirements", "systems", "database"
            ],
        },
        "business systems specialist": {
            "skills": [
                "business analysis", "business systems",
                "requirements analysis", "process improvement",
                "systems analysis", "sql", "jira", "stakeholder",
                "documentation", "project management"
            ],
            "education": [
                "business analytics", "information systems",
                "information technology", "computer science",
                "business administration"
            ],
            "experience": [
                "business analyst", "systems analyst", "requirements",
                "stakeholder", "process improvement", "documentation"
            ],
        },
        "web developer": {
            "skills": [
                "web development", "html", "css", "javascript", "react",
                "frontend", "backend", "full stack", "api", "website"
            ],
            "education": [
                "computer science", "information technology",
                "software engineering", "web development"
            ],
            "experience": [
                "web developer", "frontend developer", "backend developer",
                "full stack developer", "website", "web application",
                "developed", "built"
            ],
        },
        "database analyst": {
            "skills": [
                "database", "sql", "mysql", "postgresql", "oracle",
                "data modeling", "database management", "etl", "query"
            ],
            "education": [
                "computer science", "information technology",
                "information systems", "data analytics"
            ],
            "experience": [
                "database analyst", "database administrator",
                "database", "sql", "etl", "data model"
            ],
        },
        "computer network": {
            "skills": [
                "network", "networking", "technical support", "it support",
                "router", "switch", "tcp", "ip", "server", "systems"
            ],
            "education": [
                "computer science", "information technology",
                "computer engineering", "network"
            ],
            "experience": [
                "network technician", "network administrator",
                "technical support", "server", "network"
            ],
        },
        "financial and investment analyst": {
            "skills": [
                "financial analysis", "finance", "investment", "forecasting",
                "excel", "financial modeling", "budget", "valuation",
                "reporting"
            ],
            "education": [
                "finance", "accounting", "economics",
                "business administration", "commerce"
            ],
            "experience": [
                "financial analyst", "investment analyst", "budget",
                "valuation", "financial reporting", "forecast"
            ],
        },
        "business development": {
            "skills": [
                "business development", "market research", "sales",
                "marketing", "customer", "client", "research",
                "communication", "strategy"
            ],
            "education": [
                "business", "marketing", "commerce",
                "business administration", "management"
            ],
            "experience": [
                "business development", "sales", "marketing",
                "client", "customer", "market research"
            ],
        },
        "administrative assistant": {
            "skills": [
                "administrative", "administration", "office", "scheduling",
                "calendar", "customer service", "data entry",
                "documentation", "microsoft office", "excel",
                "word", "outlook", "records"
            ],
            "education": [
                "office administration", "administration",
                "business administration", "business"
            ],
            "experience": [
                "administrative assistant", "office assistant",
                "receptionist", "clerical", "scheduling",
                "data entry", "records", "office"
            ],
        },
        "office manager": {
            "skills": [
                "office management", "administration", "scheduling",
                "operations", "customer service", "records",
                "coordination", "inventory", "supervised", "managed"
            ],
            "education": [
                "business administration", "management",
                "office administration", "business"
            ],
            "experience": [
                "office manager", "supervisor", "managed",
                "supervised", "coordinated", "operations"
            ],
        },
        "food service supervisor": {
            "skills": [
                "food service", "restaurant", "food safety",
                "customer service", "inventory", "scheduling",
                "cash", "pos", "kitchen", "hospitality"
            ],
            "education": [
                "hospitality", "food service", "culinary",
                "hotel management", "restaurant management"
            ],
            "experience": [
                "food service supervisor", "restaurant supervisor",
                "restaurant", "supervised", "trained",
                "food safety", "kitchen", "hospitality"
            ],
        },
        "licensed practical nurse": {
            "skills": [
                "nursing", "patient care", "healthcare", "clinical",
                "medication", "vital signs", "medical", "care plan"
            ],
            "education": [
                "nursing", "practical nursing", "health sciences",
                "healthcare"
            ],
            "experience": [
                "licensed practical nurse", "practical nurse",
                "nurse", "patient care", "clinical"
            ],
        },
        "bookkeeper": {
            "skills": [
                "bookkeeping", "accounting", "accounts payable",
                "accounts receivable", "payroll", "quickbooks",
                "invoice", "reconciliation", "excel"
            ],
            "education": [
                "accounting", "finance", "commerce",
                "business administration"
            ],
            "experience": [
                "bookkeeper", "accounting assistant",
                "accounts payable", "accounts receivable",
                "payroll", "reconciliation"
            ],
        },
        "inside sales representative": {
            "skills": [
                "inside sales", "sales", "crm", "salesforce",
                "lead generation", "cold calling", "customer service",
                "client", "negotiation"
            ],
            "education": [
                "business", "marketing", "sales",
                "business administration"
            ],
            "experience": [
                "inside sales representative", "sales representative",
                "sales associate", "lead generation", "cold calling",
                "sales target", "quota"
            ],
        },
        "retail sales associate": {
            "skills": [
                "retail sales", "sales", "customer service", "pos",
                "cash", "merchandising", "inventory", "customer"
            ],
            "education": [
                "retail", "business", "marketing",
                "business administration"
            ],
            "experience": [
                "retail sales associate", "sales associate",
                "retail", "cashier", "customer service",
                "merchandising"
            ],
        },
        "continuing care assistant": {
            "skills": [
                "patient care", "personal care", "healthcare",
                "caregiving", "elderly", "mobility", "hygiene",
                "support worker"
            ],
            "education": [
                "continuing care", "healthcare", "health sciences",
                "personal support"
            ],
            "experience": [
                "continuing care assistant", "care assistant",
                "personal support worker", "caregiver",
                "patient care", "elderly care"
            ],
        },
        "information technology (it) analyst": {
            "skills": [
                "information technology", "it support", "systems",
                "technical support", "requirements analysis",
                "sql", "database", "network", "jira"
            ],
            "education": [
                "information technology", "computer science",
                "information systems", "computer engineering"
            ],
            "experience": [
                "it analyst", "information technology analyst",
                "systems analyst", "technical support",
                "requirements", "systems"
            ],
        },
    }

    # --------------------------------------------------------
    # 2. Helper to calculate fair profile coverage
    # --------------------------------------------------------
    def component_score(keywords):
        if not keywords:
            return 0.0, []

        matches = []
        for keyword in keywords:
            if keyword in text and keyword not in matches:
                matches.append(keyword)

        # Avoid the old "2 out of 3 = 67%" problem.
        # A category needs several independent pieces of evidence
        # before receiving a very high score.
        score = min(len(matches) / 5.0, 1.0)
        return score, matches

    occupations = sorted(
        top5_recommendations["recommended_occupation"]
        .dropna()
        .astype(str)
        .unique()
    )

    rows = []

    for occupation in occupations:
        occupation_lower = occupation.lower()

        matched_profile = None

        # Exact/contained profile matching, longest name first.
        for profile_name in sorted(
            occupation_profiles.keys(),
            key=len,
            reverse=True
        ):
            if (
                profile_name == occupation_lower
                or profile_name in occupation_lower
                or occupation_lower in profile_name
            ):
                matched_profile = occupation_profiles[profile_name]
                break

        if matched_profile is None:
            matched_profile = {
                "skills": [
                    token
                    for token in re.findall(
                        r"[a-zA-Z]+",
                        occupation_lower
                    )
                    if len(token) > 3
                ],
                "education": [],
                "experience": []
            }

        skill_score, skill_matches = component_score(
            matched_profile["skills"]
        )

        education_score, education_matches = component_score(
            matched_profile["education"]
        )

        experience_score, experience_matches = component_score(
            matched_profile["experience"]
        )

        # ----------------------------------------------------
        # 3. Strong domain mismatch safeguard
        # ----------------------------------------------------
        technical_education_terms = [
            "computer science", "information technology",
            "software engineering", "computer engineering",
            "information systems", "data science", "data analytics"
        ]

        healthcare_education_terms = [
            "nursing", "health sciences", "healthcare",
            "practical nursing"
        ]

        business_education_terms = [
            "business administration", "business", "marketing",
            "finance", "accounting", "commerce"
        ]

        has_technical_background = any(
            term in text for term in technical_education_terms
        )

        has_healthcare_background = any(
            term in text for term in healthcare_education_terms
        )

        has_business_background = any(
            term in text for term in business_education_terms
        )

        technical_occ = any(
            term in occupation_lower
            for term in [
                "software", "information technology",
                "information systems", "data scientist",
                "database", "web developer", "computer network",
                "business systems"
            ]
        )

        healthcare_occ = any(
            term in occupation_lower
            for term in [
                "nurse", "care assistant", "health"
            ]
        )

        sales_occ = any(
            term in occupation_lower
            for term in [
                "sales", "retail"
            ]
        )

        # Domain alignment starts neutral.
        domain_alignment = 1.0

        if has_technical_background and technical_occ:
            domain_alignment = 1.15

        elif has_technical_background and healthcare_occ:
            domain_alignment = 0.35

        elif has_technical_background and sales_occ:
            # Sales can still be recommended, but only if the resume
            # contains meaningful direct sales evidence.
            if experience_score < 0.4:
                domain_alignment = 0.45

        elif has_healthcare_background and healthcare_occ:
            domain_alignment = 1.15

        elif has_business_background and sales_occ:
            domain_alignment = 1.10

        # ----------------------------------------------------
        # 4. Project demand signal
        # ----------------------------------------------------
        occupation_rows = top5_recommendations[
            top5_recommendations["recommended_occupation"]
            .astype(str)
            .str.lower()
            == occupation_lower
        ]

        if (
            not occupation_rows.empty
            and "demand_percentage" in occupation_rows.columns
        ):
            demand = float(
                occupation_rows["demand_percentage"].mean()
            )
        else:
            demand = 0.0

        # ----------------------------------------------------
        # 5. Final live score
        # ----------------------------------------------------
        weighted_resume_score = (
            0.40 * skill_score
            + 0.30 * education_score
            + 0.20 * experience_score
        )

        weighted_resume_score = min(
            weighted_resume_score * domain_alignment,
            0.90
        )

        display_score = (
            weighted_resume_score * 100
            + 0.10 * demand
        )

        # Cap final live score at 100.
        display_score = min(display_score, 100.0)

        matched_evidence = (
            skill_matches
            + education_matches
            + experience_matches
        )

        matched_evidence = list(
            dict.fromkeys(matched_evidence)
        )

        rows.append(
            {
                "Occupation": occupation,
                "Live Resume Match %": round(display_score, 2),
                "Skill / Tool Match %": round(skill_score * 100, 2),
                "Education Alignment %": round(education_score * 100, 2),
                "Experience Evidence %": round(experience_score * 100, 2),
                "Project Demand %": round(demand, 2),
                "Matched Resume Evidence": (
                    ", ".join(matched_evidence)
                    if matched_evidence
                    else "No configured evidence terms matched"
                ),
            }
        )

    result = (
        pd.DataFrame(rows)
        .sort_values(
            [
                "Live Resume Match %",
                "Education Alignment %",
                "Skill / Tool Match %",
                "Experience Evidence %"
            ],
            ascending=False
        )
        .head(top_n)
        .reset_index(drop=True)
    )

    result.insert(
        0,
        "Rank",
        range(1, len(result) + 1)
    )

    return result


# ============================================================
# 1. PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Career Recommendation System",
    page_icon="🎯",
    layout="wide"
)


# ============================================================
# 2. PROJECT PATHS — DEPLOYMENT READY
# ============================================================

APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR

WEEK8_OUTPUT_DIR = APP_DIR
HUMAN_EVAL_DIR = APP_DIR
STREAMLIT_DIR = APP_DIR

CANDIDATE_MASTER_FILE = (
    WEEK8_OUTPUT_DIR
    / "week8_candidate_deployment_master.csv"
)

TOP5_FILE = (
    WEEK8_OUTPUT_DIR
    / "week8_streamlit_top5_recommendations.csv"
)

KPI_FILE = (
    WEEK8_OUTPUT_DIR
    / "week8_project_kpi_summary.csv"
)

OCCUPATION_SUMMARY_FILE = (
    WEEK8_OUTPUT_DIR
    / "week8_occupation_deployment_summary.csv"
)

INSIGHTS_FILE = (
    WEEK8_OUTPUT_DIR
    / "week8_final_project_insights.csv"
)

HUMAN_EVAL_SUMMARY_FILE = (
    HUMAN_EVAL_DIR
    / "final_human_evaluation_summary.csv"
)

FRONT_IMAGE_FILE = (
    STREAMLIT_DIR
    / "career_banner.png"
)


# ============================================================
# 3. LOAD WEEK 8 DEPLOYMENT DATA
# ============================================================

@st.cache_data
def load_data():

    candidate_master = pd.read_csv(
        CANDIDATE_MASTER_FILE
    )

    top5_recommendations = pd.read_csv(
        TOP5_FILE
    )

    project_kpis = pd.read_csv(
        KPI_FILE
    )

    occupation_summary = pd.read_csv(
        OCCUPATION_SUMMARY_FILE
    )

    project_insights = pd.read_csv(
        INSIGHTS_FILE
    )

    human_evaluation_summary = pd.read_csv(
        HUMAN_EVAL_SUMMARY_FILE
    )

    return (
        candidate_master,
        top5_recommendations,
        project_kpis,
        occupation_summary,
        project_insights,
        human_evaluation_summary
    )


try:

    (
        candidate_master,
        top5_recommendations,
        project_kpis,
        occupation_summary,
        project_insights,
        human_evaluation_summary
    ) = load_data()

except Exception as error:

    st.error(
        "The deployment or human-evaluation datasets could not be loaded."
    )

    st.exception(error)
    st.stop()


# ============================================================
# HUMAN EVALUATION METRIC HELPER
# ============================================================

def get_human_eval_metric(component, metric, default=None):
    """Return one metric from the final human-evaluation summary."""
    match = human_evaluation_summary[
        (human_evaluation_summary["evaluation_component"] == component)
        & (human_evaluation_summary["metric"] == metric)
    ]

    if match.empty:
        return default

    return float(match.iloc[0]["value"])


# ============================================================
# 4. SIDEBAR NAVIGATION
# ============================================================

st.sidebar.title("🎯 Career Analytics")

page = st.sidebar.radio(
    "Navigation",
    [
        "Home / Overview",
        "Candidate Input",
        "Recommendations",
        "Skill Gap Analysis",
        "RAG Explanation",
        "Dashboard / Insights"
    ]
)


# ============================================================
# 5. CANDIDATE SELECTION
# ============================================================

candidate_list = sorted(
    candidate_master["candidate_id"].unique()
)

# Hide the existing-candidate selector on the Candidate Input page.
# A default internal candidate is still defined so the rest of the
# application can safely reference selected_candidate.
if page != "Candidate Input":

    st.sidebar.divider()

    st.sidebar.subheader("Candidate Selection")

    selected_candidate = st.sidebar.selectbox(
        "Select Candidate",
        candidate_list
    )

else:

    selected_candidate = candidate_list[0]


# ------------------------------------------------------------
# Selected candidate profile
# ------------------------------------------------------------

selected_profile = (
    candidate_master[
        candidate_master["candidate_id"]
        == selected_candidate
    ]
    .iloc[0]
)


# ------------------------------------------------------------
# Selected candidate Top-5 recommendations
# ------------------------------------------------------------

selected_top5 = (
    top5_recommendations[
        top5_recommendations["candidate_id"]
        == selected_candidate
    ]
    .sort_values("recommendation_rank")
    .copy()
)


# ============================================================
# PAGE 1 — HOME / OVERVIEW
# ============================================================

if page == "Home / Overview":

    st.title(
        "🎯 Student Skill Gap Analysis & "
        "Career Recommendation System"
    )

    st.write(
        "An NLP and hybrid recommendation system for "
        "career matching, skill-gap analysis, "
        "Canadian labour-market insights, and "
        "grounded career explanations."
    )

    if FRONT_IMAGE_FILE.exists():

        st.image(
            str(FRONT_IMAGE_FILE),
            use_container_width=True
        )

    else:

        st.info(
            "Add career_banner.png to the Streamlit folder "
            "to display the career analytics banner."
        )

    st.divider()

    st.subheader("System Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Candidates",
            candidate_master[
                "candidate_id"
            ].nunique()
        )

    with col2:

        st.metric(
            "Occupations Evaluated",
            15
        )

    with col3:

        st.metric(
            "Top-5 Recommendations",
            len(top5_recommendations)
        )

    with col4:

        deployment_ready = (
            candidate_master[
                "deployment_status"
            ]
            .eq("Ready")
            .sum()
        )

        st.metric(
            "Deployment Ready",
            deployment_ready
        )

    st.success(
        "Week 8 deployment datasets loaded successfully."
    )

    st.info(
        f"Currently selected candidate: "
        f"{selected_candidate}"
    )


# ============================================================
# PAGE 2 — CANDIDATE INPUT
# ============================================================

elif page == "Candidate Input":

    st.title("📝 Candidate Profile Input")

    st.write(
        "Enter a candidate profile to demonstrate the information "
        "used by the career recommendation workflow."
    )

    st.info(
        "For privacy, do not enter names, email addresses, phone "
        "numbers, street addresses, student numbers, dates of birth, "
        "or other unnecessary personal identifiers."
    )

    st.divider()

    with st.form("candidate_profile_form"):

        st.subheader("Candidate Information")

        col1, col2 = st.columns(2)

        with col1:

            education_level = st.selectbox(
                "Highest Education Level",
                [
                    "High School",
                    "Certificate / Diploma",
                    "Bachelor's Degree",
                    "Master's Degree",
                    "Doctoral Degree",
                    "Other"
                ]
            )

            field_of_study = st.text_input(
                "Field of Study",
                placeholder="Example: Data Analytics"
            )

            years_experience = st.number_input(
                "Years of Work Experience",
                min_value=0.0,
                max_value=50.0,
                value=0.0,
                step=0.5
            )

        with col2:

            career_interest = st.text_input(
                "Career Interest",
                placeholder="Example: Data, technology, business analytics"
            )

            certifications = st.text_area(
                "Certifications",
                placeholder=(
                    "Example: Microsoft Power BI, "
                    "Google Data Analytics"
                )
            )

            tools = st.text_area(
                "Software / Tools",
                placeholder=(
                    "Example: Python, SQL, Power BI, "
                    "Excel, Tableau"
                )
            )

        skills = st.text_area(
            "Skills",
            placeholder=(
                "Enter skills separated by commas. "
                "Example: Python, SQL, data analysis, "
                "communication, problem solving"
            ),
            height=120
        )

        projects = st.text_area(
            "Projects / Relevant Experience",
            placeholder=(
                "Briefly describe relevant academic, "
                "professional, or portfolio projects."
            ),
            height=120
        )

        st.subheader("Resume Upload (Optional)")

        uploaded_resume = st.file_uploader(
            "Upload Resume",
            type=["pdf", "docx", "txt"],
            help=(
                "Upload an anonymized PDF, DOCX, or TXT resume. "
                "Avoid unnecessary personal identifiers."
            )
        )

        if uploaded_resume is not None:
            st.caption(
                f"Selected file: {uploaded_resume.name}"
            )

        submitted = st.form_submit_button(
            "Process Candidate Profile",
            type="primary"
        )

    if submitted:

        resume_text, resume_error = extract_resume_text(
            uploaded_resume
        )

        skill_list = [
            skill.strip()
            for skill in skills.split(",")
            if skill.strip()
        ]

        tool_list = [
            tool.strip()
            for tool in tools.split(",")
            if tool.strip()
        ]

        certification_list = [
            item.strip()
            for item in certifications.split(",")
            if item.strip()
        ]

        st.divider()
        st.subheader("Extracted Candidate Information")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Skills Entered",
                len(skill_list)
            )

        with col2:
            st.metric(
                "Tools Entered",
                len(tool_list)
            )

        with col3:
            st.metric(
                "Years of Experience",
                f"{years_experience:g}"
            )

        profile_summary = pd.DataFrame(
            {
                "Profile Component": [
                    "Education Level",
                    "Field of Study",
                    "Career Interest",
                    "Skills",
                    "Software / Tools",
                    "Certifications",
                    "Projects / Relevant Experience"
                ],
                "Extracted Information": [
                    education_level,
                    field_of_study if field_of_study else "Not provided",
                    career_interest if career_interest else "Not provided",
                    ", ".join(skill_list) if skill_list else "Not provided",
                    ", ".join(tool_list) if tool_list else "Not provided",
                    ", ".join(certification_list)
                    if certification_list
                    else "Not provided",
                    projects if projects else "Not provided"
                ]
            }
        )

        st.dataframe(
            profile_summary,
            use_container_width=True,
            hide_index=True
        )

        st.subheader("Resume Processing")

        if uploaded_resume is None:

            st.info(
                "No resume uploaded. Manual candidate information "
                "was processed."
            )

        elif resume_error:

            st.warning(resume_error)

        else:

            st.success(
                f"Resume text extracted successfully from "
                f"{uploaded_resume.name}."
            )

            st.metric(
                "Resume Text Characters",
                f"{len(resume_text):,}"
            )

            resume_info = extract_resume_information(resume_text)

            st.subheader("Information Extracted From Resume")

            resume_profile_df = pd.DataFrame(
                {
                    "Resume Component": list(resume_info.keys()),
                    "Extracted Information": list(resume_info.values())
                }
            )

            st.dataframe(
                resume_profile_df,
                use_container_width=True,
                hide_index=True
            )

            detected_skill_text = resume_info["Detected Skills"]
            detected_tool_text = resume_info["Detected Software / Tools"]

            rcol1, rcol2 = st.columns(2)

            with rcol1:
                st.write("**Detected Skills**")
                st.info(detected_skill_text)

            with rcol2:
                st.write("**Detected Software / Tools**")
                st.info(detected_tool_text)

            with st.expander(
                "View Extracted Resume Text",
                expanded=False
            ):

                st.text_area(
                    "Extracted Resume Text",
                    value=resume_text,
                    height=350,
                    disabled=True
                )

            st.caption(
                "Resume-derived fields use transparent keyword and pattern matching "
                "for the deployment demonstration and should be reviewed by the user."
            )


            st.divider()
            st.subheader("🎯 Career Recommendations From Uploaded Resume")

            live_resume_recommendations = (
                generate_resume_career_recommendations(
                    resume_text=resume_text,
                    top5_recommendations=top5_recommendations,
                    top_n=5
                )
            )

            if live_resume_recommendations.empty:
                st.info(
                    "No career recommendations could be generated "
                    "from the uploaded resume."
                )
            else:
                top_live = live_resume_recommendations.iloc[0]

                st.markdown(
                    f"### Top Match: {top_live['Occupation']}"
                )

                rc1, rc2, rc3, rc4 = st.columns(4)

                with rc1:
                    st.metric(
                        "Live Resume Match",
                        f"{top_live['Live Resume Match %']:.2f}%"
                    )

                with rc2:
                    st.metric(
                        "Skill / Tool Match",
                        f"{top_live['Skill / Tool Match %']:.2f}%"
                    )

                with rc3:
                    st.metric(
                        "Education Alignment",
                        f"{top_live['Education Alignment %']:.2f}%"
                    )

                with rc4:
                    st.metric(
                        "Project Demand",
                        f"{top_live['Project Demand %']:.2f}%"
                    )

                st.markdown("#### Top 5 Career Recommendations")

                st.dataframe(
                    live_resume_recommendations[
                        [
                            "Rank",
                            "Occupation",
                            "Live Resume Match %",
                            "Skill / Tool Match %",
                            "Education Alignment %",
                            "Experience Evidence %",
                            "Project Demand %",
                            "Matched Resume Evidence",
                        ]
                    ],
                    use_container_width=True,
                    hide_index=True
                )

                st.info(
                    "These live recommendations use a transparent deployment "
                    "score based on 40% skill/tool evidence, 30% education/field "
                    "alignment, 20% occupation-specific experience evidence, "
                    "and 10% the project's Canadian demand signal. They are "
                    "separate from the validated Week 8 recommendations for "
                    "the 63 anonymized evaluation candidates."
                )

        st.success(
            "Candidate profile processed successfully."
        )

        st.warning(
            "This deployment page demonstrates candidate-profile "
            "collection and feature extraction. The validated career "
            "recommendations shown on the other pages are generated "
            "from the project's existing anonymized evaluation "
            "candidate profiles."
        )


# ============================================================
# PAGE 3 — RECOMMENDATIONS
# ============================================================

elif page == "Recommendations":

    st.title("📊 Career Recommendations")

    st.write(
        f"Recommendation results for "
        f"**{selected_candidate}**"
    )

    st.divider()

    st.subheader("Top Career Recommendation")

    st.markdown(
        f"## {selected_profile['top_recommended_occupation']}"
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Overall Match",
            f"{selected_profile['top_recommendation_percentage']:.2f}%"
        )

    with col2:

        st.metric(
            "Skill Match",
            f"{selected_profile['top_skill_percentage']:.2f}%"
        )

    with col3:

        st.metric(
            "Semantic Match",
            f"{selected_profile['top_semantic_percentage']:.2f}%"
        )

    with col4:

        st.metric(
            "Labour Demand",
            f"{selected_profile['top_demand_percentage']:.2f}%"
        )

    col5, col6 = st.columns(2)

    with col5:

        st.metric(
            "Education Alignment",
            f"{selected_profile['top_education_percentage']:.2f}%"
        )

    with col6:

        st.metric(
            "Priority Missing Skills",
            int(
                selected_profile[
                    "missing_skill_count"
                ]
            )
        )

    st.divider()

    st.subheader(
        "Top 5 Career Recommendations"
    )

    top5_display = selected_top5[
        [
            "recommendation_rank",
            "recommended_occupation",
            "recommendation_percentage",
            "skill_percentage",
            "semantic_percentage",
            "demand_percentage",
            "education_percentage"
        ]
    ].copy()

    top5_display = top5_display.rename(
        columns={
            "recommendation_rank": "Rank",
            "recommended_occupation": "Occupation",
            "recommendation_percentage": "Overall Match %",
            "skill_percentage": "Skill Match %",
            "semantic_percentage": "Semantic Match %",
            "demand_percentage": "Labour Demand %",
            "education_percentage": "Education Alignment %"
        }
    )

    st.dataframe(
        top5_display,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# PAGE 4 — SKILL GAP ANALYSIS
# ============================================================

elif page == "Skill Gap Analysis":

    st.title("🧩 Skill Gap Analysis")

    st.write(
        f"Prescriptive skill-gap analysis for "
        f"**{selected_candidate}**"
    )

    st.divider()

    st.subheader(
        "Recommended Occupation"
    )

    st.markdown(
        f"## {selected_profile['top_recommended_occupation']}"
    )

    skill_gap_status = (
        selected_profile[
            "skill_gap_status"
        ]
    )

    if (
        skill_gap_status
        == "Skill development recommended"
    ):

        st.warning(
            f"{int(selected_profile['missing_skill_count'])} "
            "priority skill gap(s) identified."
        )

        st.subheader(
            "Priority Skills to Develop"
        )

        st.write(
            selected_profile[
                "prioritized_skill_gaps"
            ]
        )

        st.subheader(
            "Highest-Priority Skill"
        )

        highest_priority = (
            selected_profile[
                "highest_skill_priority_percentage"
            ]
        )

        st.info(
            f"{selected_profile['highest_priority_skill']} "
            f"({highest_priority:.2f}% priority)"
        )

        st.subheader(
            "Recommended Development Action"
        )

        st.write(
            selected_profile[
                "skill_development_action"
            ]
        )

    else:

        st.success(
            "No priority skill gaps identified "
            "for this recommended occupation."
        )

        st.subheader(
            "Development Recommendation"
        )

        st.write(
            selected_profile[
                "skill_development_action"
            ]
        )


# ============================================================
# PAGE 5 — RAG EXPLANATION
# ============================================================

elif page == "RAG Explanation":

    st.title(
        "🤖 Grounded RAG Explanation"
    )

    st.write(
        f"Grounded career explanation for "
        f"**{selected_candidate}**"
    )

    st.divider()

    st.subheader(
        "Recommended Occupation"
    )

    st.markdown(
        f"## {selected_profile['top_recommended_occupation']}"
    )

    st.subheader(
        "Recommendation Summary"
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Overall Match",
            f"{selected_profile['top_recommendation_percentage']:.2f}%"
        )

    with col2:

        st.metric(
            "Skill Match",
            f"{selected_profile['top_skill_percentage']:.2f}%"
        )

    with col3:

        st.metric(
            "Semantic Match",
            f"{selected_profile['top_semantic_percentage']:.2f}%"
        )

    with col4:

        st.metric(
            "Labour Demand",
            f"{selected_profile['top_demand_percentage']:.2f}%"
        )

    st.divider()

    st.subheader(
        "Grounded Career Explanation"
    )

    with st.container(
        border=True
    ):

        # Keep the displayed RAG score aligned with the final Week 8
        # recommendation score. This changes display text only.
        rag_explanation_display = str(
            selected_profile["final_rag_explanation"]
        )

        rag_explanation_display = re.sub(
            r"hybrid recommendation score of\s+\d+(?:\.\d+)?%?",
            (
                "final overall match of "
                f"{selected_profile['top_recommendation_percentage']:.2f}%"
            ),
            rag_explanation_display,
            flags=re.IGNORECASE
        )

        st.write(rag_explanation_display)

    st.subheader(
        "Skill-Gap Evidence"
    )

    if int(
        selected_profile[
            "missing_skill_count"
        ]
    ) > 0:

        st.warning(
            f"{int(selected_profile['missing_skill_count'])} "
            "priority skill gap(s) were identified."
        )

        st.write(
            "**Priority skills:** "
            + str(
                selected_profile[
                    "prioritized_skill_gaps"
                ]
            )
        )

        st.write(
            "**Development action:** "
            + str(
                selected_profile[
                    "skill_development_action"
                ]
            )
        )

    else:

        st.success(
            "No priority skill gaps were identified "
            "for this Top-1 occupation."
        )

        st.write(
            selected_profile[
                "skill_development_action"
            ]
        )

    st.subheader(
        "Labour-Market & Education Evidence"
    )

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Canadian Labour Demand",
            f"{selected_profile['top_demand_percentage']:.2f}%"
        )

    with col2:

        st.metric(
            "Education Alignment",
            f"{selected_profile['top_education_percentage']:.2f}%"
        )

    st.divider()

    st.subheader(
        "Explanation Validation"
    )

    if (
        selected_profile[
            "final_rag_status"
        ]
        == "Ready"
    ):

        st.success(
            "The RAG explanation is aligned with "
            "the final Top-1 recommendation."
        )

    else:

        st.warning(
            "The RAG explanation requires review."
        )

    st.caption(
        "Explanation source: "
        + str(
            selected_profile[
                "rag_explanation_source"
            ]
        )
    )

    with st.expander(
        "ℹ️ Decision-Support Limitation"
    ):

        st.write(
            "This recommendation is intended as a "
            "decision-support output rather than a guaranteed "
            "career outcome. Recommendation and demand scores "
            "should be considered together with candidate "
            "preferences, experience, current labour-market "
            "conditions, and human career guidance."
        )


# ============================================================
# PAGE 6 — DASHBOARD / INSIGHTS
# ============================================================

elif page == "Dashboard / Insights":

    st.title(
        "📈 Dashboard / Insights"
    )

    st.write(
        "Project-level KPIs, occupation-level performance, "
        "and final analytical insights."
    )

    st.divider()

    st.subheader(
        "Project KPI Summary"
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Total Candidates",
            candidate_master[
                "candidate_id"
            ].nunique()
        )

    with col2:

        st.metric(
            "Occupations Evaluated",
            15
        )

    with col3:

        st.metric(
            "Candidate-Occupation Pairs",
            945
        )

    with col4:

        st.metric(
            "Deployment Ready",
            candidate_master[
                "deployment_status"
            ]
            .eq("Ready")
            .sum()
        )

    col5, col6, col7, col8 = st.columns(4)

    with col5:

        st.metric(
            "Avg. Top-1 Match",
            f"{candidate_master['top_recommendation_percentage'].mean():.2f}%"
        )

    with col6:

        st.metric(
            "Avg. Skill Match",
            f"{candidate_master['top_skill_percentage'].mean():.2f}%"
        )

    with col7:

        st.metric(
            "Candidates With Skill Gaps",
            candidate_master[
                "missing_skill_count"
            ]
            .gt(0)
            .sum()
        )

    with col8:

        st.metric(
            "RAG Explanations Ready",
            candidate_master[
                "final_rag_status"
            ]
            .eq("Ready")
            .sum()
        )

    st.divider()

    st.subheader(
        "Occupation-Level Summary"
    )

    st.markdown(
        "### Top-1 Recommendation Distribution"
    )

    max_count = (
        occupation_summary[
            "top1_candidate_count"
        ]
        .max()
    )

    for _, row in occupation_summary.iterrows():

        occupation = (
            row[
                "top_recommended_occupation"
            ]
        )

        count = int(
            row[
                "top1_candidate_count"
            ]
        )

        progress_value = (
            count / max_count
            if max_count > 0
            else 0
        )

        st.write(
            f"**{occupation}** — "
            f"{count} candidate(s)"
        )

        st.progress(
            progress_value
        )

    st.markdown(
        "### Detailed Occupation Results"
    )

    st.dataframe(
        occupation_summary,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # --------------------------------------------------------
    # Final Human Evaluation
    # --------------------------------------------------------
    st.subheader(
        "✅ Model Evaluation"
    )

    st.write(
        "Final validation results based on completed human-review samples "
        "for skill extraction, recommendation ranking, skill-gap analysis, "
        "and RAG explanation quality."
    )

    skill_f1_eval = get_human_eval_metric(
        "Skill Extraction",
        "F1 Score",
        0.0
    )

    ranking_precision_eval = get_human_eval_metric(
        "Recommendation Ranking",
        "Precision@5",
        0.0
    )

    ranking_ndcg_eval = get_human_eval_metric(
        "Recommendation Ranking",
        "NDCG@5",
        0.0
    )

    gap_accuracy_eval = get_human_eval_metric(
        "Skill Gap",
        "Accuracy",
        0.0
    )

    gap_expert_rating_eval = get_human_eval_metric(
        "Skill Gap",
        "Average Expert Rating",
        0.0
    )

    rag_mean_eval = get_human_eval_metric(
        "RAG",
        "Overall Mean Rating",
        0.0
    )

    ecol1, ecol2, ecol3 = st.columns(3)

    with ecol1:
        st.metric(
            "Skill Extraction F1",
            f"{skill_f1_eval * 100:.2f}%"
        )

    with ecol2:
        st.metric(
            "Ranking Precision@5",
            f"{ranking_precision_eval * 100:.2f}%"
        )

    with ecol3:
        st.metric(
            "Ranking NDCG@5",
            f"{ranking_ndcg_eval * 100:.2f}%"
        )

    ecol4, ecol5, ecol6 = st.columns(3)

    with ecol4:
        st.metric(
            "Skill Gap Accuracy",
            f"{gap_accuracy_eval * 100:.2f}%"
        )

    with ecol5:
        st.metric(
            "Skill Gap Expert Rating",
            f"{gap_expert_rating_eval:.2f}/5"
        )

    with ecol6:
        st.metric(
            "RAG Mean Rating",
            f"{rag_mean_eval:.2f}/5"
        )

    with st.expander(
        "View Full Human Evaluation Summary",
        expanded=False
    ):

        evaluation_display = human_evaluation_summary.copy()

        evaluation_display["value"] = evaluation_display.apply(
            lambda row: (
                f"{row['value'] * 100:.2f}%"
                if (
                    row["metric"] in [
                        "Accuracy",
                        "Precision",
                        "Recall",
                        "F1 Score",
                        "Precision@5",
                        "Recall@5",
                        "NDCG@5",
                        "MRR",
                        "Positive Rating Percentage"
                    ]
                )
                else (
                    f"{row['value']:.2f}/5"
                    if row["metric"] in [
                        "Average Expert Rating",
                        "Overall Mean Rating"
                    ]
                    else f"{row['value']:.0f}"
                )
            ),
            axis=1
        )

        evaluation_display = evaluation_display.rename(
            columns={
                "evaluation_component": "Evaluation Component",
                "metric": "Metric",
                "value": "Result"
            }
        )

        st.dataframe(
            evaluation_display,
            use_container_width=True,
            hide_index=True
        )

    st.info(
        "Human evaluation sample sizes: 200 skill-extraction labels, "
        "300 recommendation-ranking judgments, 200 skill-gap judgments, "
        "and 20 RAG explanations. RAG ratings reflect the reviewed sample "
        "and should not be interpreted as universal performance."
    )

    st.divider()

    st.subheader(
        "Final Project Insights"
    )

    st.write(
        "Key analytical findings and their implications "
        "from the final recommendation system."
    )

    for _, insight in project_insights.iterrows():

        category = (
            insight[
                "category"
            ]
        )

        finding = (
            insight[
                "finding"
            ]
        )

        implication = (
            insight[
                "implication"
            ]
        )

        with st.expander(
            f"💡 {category}"
        ):

            st.markdown(
                "**Finding**"
            )

            st.write(
                finding
            )

            st.markdown(
                "**Implication**"
            )

            st.write(
                implication
            )
