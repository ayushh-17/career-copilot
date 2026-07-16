"""
AI Career Copilot - Backend Server
-----------------------------------
Ye Flask app humari website ka "dimaag" hai. Ye:
1. Frontend (HTML page) ko serve karta hai
2. Claude API se baat karta hai (resume/JD analyze karne ke liye)
3. Baad me database se applications save/fetch karega

Beginner note: Flask ek "web framework" hai jo Python me website banane
me help karta hai. Har @app.route() ek "URL address" define karta hai
jispe browser request bhej sakta hai.
"""

import os
from flask import Flask, render_template, request, jsonify, send_file
import google.generativeai as genai
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from pypdf import PdfReader
from docx import Document
import tempfile
import time
from threading import Lock
import sqlite3
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import json

# .env file se environment variables load karo (jaise API key)
load_dotenv()

app = Flask(__name__)

# Upload folder configure
UPLOAD_FOLDER = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Database setup
DB_PATH = os.path.join(os.path.dirname(__file__), 'career_copilot.db')

def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resume_name TEXT,
            job_title TEXT,
            company TEXT,
            match_score INTEGER,
            analysis_text TEXT,
            suggestions_text TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Rate limiting
REQUEST_LIMIT = 5  # Free tier: 5 requests per minute
TIME_WINDOW = 60  # seconds
request_times = []
request_lock = Lock()

# Gemini client configure kiya - ye humein Google AI se baat karne dega (FREE)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-flash-latest")

def check_rate_limit():
    """Rate limiting - 5 requests per minute for free tier"""
    global request_times
    current_time = time.time()
    
    with request_lock:
        # Remove old requests outside the time window
        request_times = [t for t in request_times if current_time - t < TIME_WINDOW]
        
        if len(request_times) >= REQUEST_LIMIT:
            wait_time = TIME_WINDOW - (current_time - request_times[0])
            return False, wait_time
        
        request_times.append(current_time)
        return True, 0

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_resume(file_path):
    """Resume se text nikal lo - PDF, DOCX, ya TXT"""
    try:
        if file_path.endswith('.pdf'):
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
        elif file_path.endswith('.docx') or file_path.endswith('.doc'):
            doc = Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
            return text
        elif file_path.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
    except Exception as e:
        return f"Error extracting text: {str(e)}"
    return ""

def extract_match_score(analysis_text):
    """Analysis se match score nikalo"""
    if "Match Score:" in analysis_text:
        try:
            score_part = analysis_text.split("Match Score:")[1].split("%")[0].strip()
            return int(''.join(filter(str.isdigit, score_part)))
        except:
            return 0
    return 0

def save_analysis_to_db(resume_name, job_title, company, match_score, analysis_text, suggestions_text):
    """Analysis ko database mein save karo"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            INSERT INTO analyses (resume_name, job_title, company, match_score, analysis_text, suggestions_text)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (resume_name, job_title, company, match_score, analysis_text, suggestions_text))
        conn.commit()
        analysis_id = c.lastrowid
        conn.close()
        return analysis_id
    except Exception as e:
        print(f"DB Error: {str(e)}")
        return None


@app.route("/")
def home():
    """
    Jab koi browser me http://localhost:5000 kholega,
    ye function chalega aur humara HTML page dikhayega.
    """
    return render_template("index.html")


@app.route("/test-ai", methods=["GET"])
def test_ai():
    """
    Ye ek TEST route hai - sirf ye check karne ke liye ki
    humara Claude API connection sahi se kaam kar raha hai ya nahi.

    Browser me jaake http://localhost:5000/test-ai kholo,
    agar Gemini ka reply dikhe to matlab sab set hai!
    """
    try:
        response = model.generate_content(
            "Say 'Career Copilot is connected!' in a friendly way."
        )
        ai_reply = response.text
        return jsonify({"status": "success", "message": ai_reply})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/analyze", methods=["POST"])
def analyze():
    """
    Resume upload karke analysis - matching score + suggestions
    """
    try:
        # Check rate limit
        allowed, wait_time = check_rate_limit()
        if not allowed:
            return jsonify({
                "status": "error",
                "message": f"⏳ API Quota hit! Please wait {int(wait_time)} seconds before trying again. (Gemini Free Tier: 5 requests/minute)",
                "wait_seconds": int(wait_time)
            }), 429
        
        # Resume file check
        if 'resume' not in request.files:
            return jsonify({"status": "error", "message": "Resume file required"}), 400
        
        resume_file = request.files['resume']
        job_description = request.form.get('job_description', '')
        
        if not job_description.strip():
            return jsonify({"status": "error", "message": "Job description required"}), 400
        
        if resume_file.filename == '':
            return jsonify({"status": "error", "message": "No file selected"}), 400
        
        if not allowed_file(resume_file.filename):
            return jsonify({"status": "error", "message": "Only PDF, DOCX, DOC, TXT allowed"}), 400
        
        # File save karo
        filename = secure_filename(resume_file.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        resume_file.save(temp_path)
        
        # Resume se text nikalo
        resume_text = extract_text_from_resume(temp_path)
        
        if not resume_text or len(resume_text) < 50:
            return jsonify({"status": "error", "message": "Could not extract text from resume. Try another file."}), 400
        
        # Matching prompt banao
        prompt = f"""
        You are an expert recruiter and resume analyst. Analyze this resume against the job description.
        
        RESUME:
        {resume_text[:2000]}
        
        JOB DESCRIPTION:
        {job_description[:1000]}
        
        Provide:
        1. Match Score (0-100%)
        2. Top 5 Matching Skills
        3. Missing Skills
        4. Strengths
        5. Improvement Areas
        6. Overall Recommendation
        
        Format response in clear sections with emojis for readability.
        """
        
        response = model.generate_content(prompt)
        analysis = response.text
        match_score = extract_match_score(analysis)
        
        # Actionable suggestions generate karo
        suggestions_prompt = f"""
        Based on this resume analysis, provide ACTIONABLE NEXT STEPS for the candidate.
        
        Analysis:
        {analysis[:1000]}
        
        Provide:
        1. Top 3 Immediate Actions (this week)
        2. 30-Day Goals (skills to develop)
        3. 90-Day Goals (projects to build)
        4. Resource Links (courses, platforms)
        
        Keep it motivating and specific!
        """
        
        suggestions_response = model.generate_content(suggestions_prompt)
        suggestions = suggestions_response.text
        
        # Get job title from form or extract from JD
        job_title = request.form.get('job_title', 'Unknown Position')
        company = request.form.get('company', 'Unknown Company')
        
        # Database mein save karo
        analysis_id = save_analysis_to_db(
            filename, job_title, company, match_score, analysis, suggestions
        )
        
        # Temp file delete karo
        try:
            os.remove(temp_path)
        except:
            pass
        
        return jsonify({
            "status": "success",
            "analysis": analysis,
            "suggestions": suggestions,
            "match_score": match_score,
            "analysis_id": analysis_id
        })
    
    except Exception as e:
        error_msg = str(e)
        
        # Check if it's a quota error
        if "quota" in error_msg.lower() or "429" in error_msg:
            return jsonify({
                "status": "error",
                "message": "⏳ Gemini API Quota Hit! Free tier allows 5 requests/minute. Please wait a moment and try again.",
                "details": error_msg
            }), 429
        
        return jsonify({"status": "error", "message": error_msg}), 500


@app.route("/portfolio", methods=["GET"])
def portfolio():
    """Get all saved analyses for portfolio"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM analyses ORDER BY created_at DESC')
        analyses = [dict(row) for row in c.fetchall()]
        conn.close()
        return jsonify({"status": "success", "analyses": analyses})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/export-pdf/<int:analysis_id>", methods=["GET"])
def export_pdf(analysis_id):
    """Export analysis as PDF"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM analyses WHERE id = ?', (analysis_id,))
        row = c.fetchone()
        conn.close()
        
        if not row:
            return jsonify({"status": "error", "message": "Analysis not found"}), 404
        
        # PDF generate karo
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch)
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor='#4f46e5',
            spaceAfter=12,
            alignment=1
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor='#4f46e5',
            spaceAfter=10,
            spaceBefore=10
        )
        
        # Title
        story.append(Paragraph("📊 Resume Analysis Report", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Details
        details_text = f"""
        <b>Resume:</b> {row['resume_name']}<br/>
        <b>Position:</b> {row['job_title']}<br/>
        <b>Company:</b> {row['company']}<br/>
        <b>Match Score:</b> {row['match_score']}%<br/>
        <b>Date:</b> {row['created_at']}
        """
        story.append(Paragraph(details_text, styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Analysis
        story.append(Paragraph("Analysis", heading_style))
        analysis_text = row['analysis_text'].replace('\n', '<br/>')
        story.append(Paragraph(analysis_text, styles['Normal']))
        
        story.append(PageBreak())
        
        # Suggestions
        story.append(Paragraph("Next Steps & Recommendations", heading_style))
        suggestions_text = row['suggestions_text'].replace('\n', '<br/>')
        story.append(Paragraph(suggestions_text, styles['Normal']))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"analysis_{analysis_id}.pdf"
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/analysis/<int:analysis_id>", methods=["GET"])
def get_analysis(analysis_id):
    """Get specific analysis with suggestions"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM analyses WHERE id = ?', (analysis_id,))
        row = c.fetchone()
        conn.close()
        
        if not row:
            return jsonify({"status": "error", "message": "Analysis not found"}), 404
        
        return jsonify({
            "status": "success",
            "analysis": dict(row)
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    # Production: PORT from environment (Railway sets this)
    # Development: default to 5000
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV") == "development"
    app.run(debug=debug, host="0.0.0.0", port=port)
