import base64
import os
import tempfile
import sys
import webbrowser
import re
import sqlite3
from threading import Timer
from datetime import datetime

# Try importing required packages with error handling
try:
    from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
    from werkzeug.utils import secure_filename
    import google.generativeai as genai
    from dotenv import load_dotenv
    import PyPDF2
    import io
except ImportError as e:
    print(f"Error importing required packages: {e}")
    print("Please make sure all required packages are installed by running:")
    print("pip install flask werkzeug PyPDF2 google-generativeai python-dotenv")
    sys.exit(1)

# Load environment variables from .env file
load_dotenv()

# Debug: Print environment variables
print("Environment variables:")
print(f"GOOGLE_API_KEY exists: {'GOOGLE_API_KEY' in os.environ}")

# Check if API key is available
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("API key not found. Please set either GEMINI_API_KEY or GOOGLE_API_KEY in your .env file.")

# Define host and port for the application
HOST = 'localhost'
PORT = 3000

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
ALLOWED_EXTENSIONS = {'pdf'}

# Create uploads folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Database setup
DATABASE = 'resume_analyzer.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create applications table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        domain TEXT NOT NULL,
        key_skills TEXT NOT NULL,
        missing_skills TEXT NOT NULL,
        score INTEGER NOT NULL,
        date TEXT NOT NULL,
        analysis TEXT NOT NULL,
        overview TEXT NOT NULL,
        resume_path TEXT NOT NULL
    )
    ''')
    
    # Create admin credentials table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS admin_credentials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    ''')
    
    # Check if admin credentials exist, if not add default
    cursor.execute('SELECT COUNT(*) FROM admin_credentials')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO admin_credentials (username, password) VALUES (?, ?)', 
                      ('admin', 'password123'))
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

# Mock admin credentials (in a real app, use a database and proper authentication)
def get_admin_credentials():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT username, password FROM admin_credentials LIMIT 1')
    admin = cursor.fetchone()
    conn.close()
    return admin['username'], admin['password']

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(pdf_file):
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            text += pdf_reader.pages[page_num].extract_text()
        return text
    except Exception as e:
        app.logger.error(f"Error extracting text from PDF: {str(e)}")
        return None

def extract_data_from_analysis(analysis_text):
    """Extract structured data from the analysis text"""
    data = {
        'domain': '',
        'key_skills': [],
        'missing_skills': [],
        'score': 0,
        'overview': ''
    }
    
    # Extract domain
    domain_match = re.search(r'Professional Domain:?\s*([^\n]+)', analysis_text)
    if domain_match:
        data['domain'] = domain_match.group(1).strip()
    
    # Extract key skills
    skills_section = re.search(r'Key Skills:?\s*([\s\S]*?)(?=\n\s*Missing Skills|\Z)', analysis_text)
    if skills_section:
        skills_text = skills_section.group(1)
        # Look for bullet points or numbered lists
        skills = re.findall(r'[-•*]\s*([^\n]+)', skills_text)
        if not skills:  # Try finding skills without bullet points
            skills = [s.strip() for s in skills_text.split('\n') if s.strip()]
        data['key_skills'] = [s.strip() for s in skills if s.strip()][:4]  # Limit to 4 skills
    
    # Extract missing skills
    missing_section = re.search(r'Missing Skills:?\s*([\s\S]*?)(?=\n\s*Resume Score|\Z)', analysis_text)
    if missing_section:
        missing_text = missing_section.group(1)
        missing = re.findall(r'[-•*]\s*([^\n]+)', missing_text)
        if not missing:  # Try finding skills without bullet points
            missing = [s.strip() for s in missing_text.split('\n') if s.strip()]
        data['missing_skills'] = [s.strip() for s in missing if s.strip()][:3]  # Limit to 3 skills
    
    # Extract score
    score_match = re.search(r'Resume Score:?\s*(\d+(?:\.\d+)?)', analysis_text)
    if score_match:
        try:
            data['score'] = int(float(score_match.group(1)))
        except ValueError:
            # If conversion fails, default to 5
            data['score'] = 5
    
    # Extract overview
    overview_section = re.search(r'Resume Overview:?\s*([\s\S]*?)(?=\n\s*Resume Content|\Z)', analysis_text)
    if overview_section:
        data['overview'] = overview_section.group(1).strip()
    
    return data

def generate_summary(pdf_text):
    try:
        # Configure the generative AI model
        genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
        
        # Use the gemini-pro model
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Create a prompt for resume analysis with one-word skills
        prompt = f"""
        Analyze the following resume and provide:
        
        Professional Domain:
        
        Identify the primary professional domain/field of the candidate (one word or short phrase only).
        
        Key Skills:
        
        List EXACTLY 4 key skills the candidate possesses based on the resume. 
        * Format as a bulleted list with asterisks (*)
        * Use ONLY single words or very short technical terms (e.g., "Python", "Project Management", "SEO")
        * DO NOT include descriptions or explanations
        
        Missing Skills:
        
        List EXACTLY 3 important skills that are typically expected in this domain but missing from the resume.
        * Format as a bulleted list with asterisks (*)
        * Use ONLY single words or very short technical terms (e.g., "Docker", "React", "Data Analysis")
        * DO NOT include descriptions or explanations
        
        Resume Score:
        
        Rate the resume on a scale of 1-10 based on its completeness, relevance to the identified domain, and overall quality.
        
        Resume Overview:
        
        Write a concise 2-3 sentence summary of the candidate's profile, highlighting their experience level, key strengths, and potential fit for roles in their domain. Keep it professional and constructive.
        
        Format your response EXACTLY as shown in this example:
        
        Professional Domain:
        
        Data Science
        
        Key Skills:
        
        * Python
        * MySQL
        * Machine Learning
        * Tableau
        
        Missing Skills:
        
        * Cloud
        * Deep Learning
        * Big Data
        
        Resume Score:
        
        7
        
        Resume Overview:
        
        This resume belongs to a mid-level Data Science professional with strong technical skills in Python and Machine Learning. The candidate demonstrates proficiency in data visualization using Tableau and database management with MySQL. While the resume shows solid foundational skills, it could be enhanced by adding experience with Cloud technologies and Big Data tools to become more competitive in the Data Science field.
        
        Resume Content:
        {pdf_text}
        """
        
        # Generate the analysis
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
            }
        )
        
        return response.text
    except Exception as e:
        app.logger.error(f"Error generating resume analysis: {str(e)}")
        # Raise the exception to be handled by the caller
        raise

def get_all_applications():
    conn = get_db_connection()
    applications = conn.execute('SELECT * FROM applications ORDER BY score DESC, id DESC').fetchall()
    
    # Convert to list of dictionaries
    result = []
    for app in applications:
        app_dict = dict(app)
        app_dict['key_skills'] = app_dict['key_skills'].split(',')
        app_dict['missing_skills'] = app_dict['missing_skills'].split(',')
        result.append(app_dict)
    
    conn.close()
    return result

def get_application_by_id(application_id):
    conn = get_db_connection()
    app = conn.execute('SELECT * FROM applications WHERE id = ?', (application_id,)).fetchone()
    
    if app:
        app_dict = dict(app)
        app_dict['key_skills'] = app_dict['key_skills'].split(',')
        app_dict['missing_skills'] = app_dict['missing_skills'].split(',')
        conn.close()
        return app_dict
    
    conn.close()
    return None

def save_application(name, email, domain, key_skills, missing_skills, score, analysis, overview, resume_path):
    conn = get_db_connection()
    
    # Convert lists to comma-separated strings
    key_skills_str = ','.join(key_skills)
    missing_skills_str = ','.join(missing_skills)
    
    conn.execute(
        'INSERT INTO applications (name, email, domain, key_skills, missing_skills, score, date, analysis, overview, resume_path) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (name, email, domain, key_skills_str, missing_skills_str, score, datetime.now().strftime('%b %d, %Y'), analysis, overview, resume_path)
    )
    
    conn.commit()
    app_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.close()
    
    return app_id

def delete_application(application_id):
    conn = get_db_connection()
    
    # Get the resume path before deleting
    app = conn.execute('SELECT resume_path FROM applications WHERE id = ?', (application_id,)).fetchone()
    
    if app:
        resume_path = app['resume_path']
        
        # Delete from database
        conn.execute('DELETE FROM applications WHERE id = ?', (application_id,))
        conn.commit()
        
        # Delete the resume file if it exists
        if os.path.exists(resume_path):
            try:
                os.remove(resume_path)
            except Exception as e:
                app.logger.error(f"Error deleting resume file: {str(e)}")
    
    conn.close()

@app.route('/', methods=['GET', 'POST'])
def index():
    # Import the job_scrap function
    from job_scrap import get_job_listings
    
    # Get job listings for the landing page
    try:
        job_listings = get_job_listings(num_jobs=3)
    except Exception as e:
        app.logger.error(f"Error fetching job listings: {e}")
        job_listings = []
    
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'pdf_file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['pdf_file']
        name = request.form.get('name', '')
        email = request.form.get('email', '')
        
        # If user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            try:
                # Save the file
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                filename = f"{timestamp}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                
                # Read the file content
                with open(file_path, 'rb') as f:
                    pdf_text = extract_text_from_pdf(f)
                
                if not pdf_text or pdf_text.strip() == "":
                    flash('Could not extract text from the resume. The file might be encrypted, damaged, or contain only images.')
                    return redirect(request.url)
                
                try:
                    # Try to generate resume analysis
                    analysis_result = generate_summary(pdf_text)
                    
                    # If analysis was successful, extract data and save to database
                    if analysis_result:
                        extracted_data = extract_data_from_analysis(analysis_result)
                        
                        # Save application to database
                        app_id = save_application(
                            name, 
                            email, 
                            extracted_data['domain'].upper(),
                            extracted_data['key_skills'],
                            extracted_data['missing_skills'],
                            extracted_data['score'],
                            analysis_result,
                            extracted_data['overview'],
                            file_path
                        )
                        
                        # Store application ID in session for result page
                        session['current_application_id'] = app_id
                except Exception as e:
                    # Log the error but don't show it to the user
                    app.logger.error(f"Error during analysis: {str(e)}")
                    
                    # Create mock data for database
                    mock_data = {
                        'domain': 'GENERAL',
                        'key_skills': ['Resume', 'Submitted', 'For', 'Review'],
                        'missing_skills': ['Pending', 'Analysis', 'Review'],
                        'score': 5,
                        'overview': 'Resume submitted for manual review.'
                    }
                    
                    # Save application with mock data
                    app_id = save_application(
                        name, 
                        email, 
                        mock_data['domain'],
                        mock_data['key_skills'],
                        mock_data['missing_skills'],
                        mock_data['score'],
                        "API Error - Manual review required",
                        mock_data['overview'],
                        file_path
                    )
                    
                    # Store application ID in session
                    session['current_application_id'] = app_id
                
                # Always show thank you page after submission
                return render_template('thank_you.html')
                
            except Exception as e:
                # Log the error but don't show it to the user
                app.logger.error(f"Error processing file: {str(e)}")
                flash('Your application has been received. Thank you!')
                return render_template('thank_you.html')
        else:
            flash('File type not allowed. Please upload a PDF file.')
            return redirect(request.url)
    
    return render_template('index.html', job_listings=job_listings)

@app.route('/admin', methods=['GET'])
def admin():
    # Check if user is logged in
    if session.get('admin_logged_in'):
        applications = get_all_applications()
        return render_template('admin_dashboard.html', applications=applications)
    else:
        return render_template('admin_login.html')

@app.route('/admin/application/<int:application_id>')
def application_detail(application_id):
    # Check if user is logged in
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin'))
    
    # Find the application by ID
    application = get_application_by_id(application_id)
    
    if application:
        return render_template('application_detail.html', application=application)
    else:
        flash('Application not found')
        return redirect(url_for('admin'))

@app.route('/admin/application/<int:application_id>/resume')
def view_resume(application_id):
    # Check if user is logged in
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin'))
    
    # Find the application by ID
    application = get_application_by_id(application_id)
    
    if application and os.path.exists(application['resume_path']):
        return send_file(application['resume_path'], as_attachment=False)
    else:
        flash('Resume not found')
        return redirect(url_for('application_detail', application_id=application_id))

@app.route('/admin/application/<int:application_id>/delete', methods=['POST'])
def delete_application_route(application_id):
    # Check if user is logged in
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin'))
    
    # Delete the application
    delete_application(application_id)
    flash('Application deleted successfully')
    
    return redirect(url_for('admin'))

@app.route('/admin/login', methods=['POST'])
def admin_login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    try:
        admin_username, admin_password = get_admin_credentials()
        
        if username == admin_username and password == admin_password:
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        else:
            flash('Invalid username or password')
            return redirect(url_for('admin'))
    except Exception as e:
        print(f"Login error: {str(e)}")
        flash('Error during login. Please try again.')
        return redirect(url_for('admin'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin'))

@app.errorhandler(413)
def request_entity_too_large(error):
    flash('File too large. Maximum size is 16MB.')
    return redirect(url_for('index')), 413

@app.errorhandler(500)
def internal_server_error(error):
    flash('An internal server error occurred. Please try again later.')
    return redirect(url_for('index')), 500

def open_browser():
    # Open browser with the specific host and port
    url = f"http://{HOST}:{PORT}/"
    print(f"Opening browser at: {url}")
    webbrowser.open_new(url)

if __name__ == '__main__':
    # Open browser after a short delay
    Timer(1.5, open_browser).start()
    # Run the Flask app with the specified host and port
    app.run(host=HOST, port=PORT, debug=True)