# Self-Evolving Neuro-Symbolic AI for Fair & Future-Proof Hiring

**The Problem**

Modern AI-driven hiring systems often fall short - lacking adaptability, reinforcing biases, and operating as black-box models with little transparency. These limitations hinder career switchers, underrepresented candidates, and businesses striving for fair, data-driven recruitment.

**Common challenges include:**

* Outdated models that fail to keep pace with evolving job markets.
* Embedded biases that exclude non-traditional candidates.
* Opaque decision-making, leaving recruiters with little insight into AI-driven selections.

**The Challenge**

Develop an adaptive, bias-aware AI hiring system that:

* **Learns in real-time** - Continuously updates based on job trends, skill graphs, and industry reports.
* **Eliminates bias** - Embeds ethical constraints and fairness checks.
* **Provides explainable decisions** - Justifies recommendations with interpretable rules and skill-gap analysis.
* **Empowers recruiters** - Enables HR to refine AI decisions, adjust skill weightage, and track AI reasoning.

**What We Expect**

A functional, innovative, and scalable AI hiring solution that ensures fairness, real-time adaptability, and seamless human-AI collaboration - transforming recruitment for the future.
=======
# PDF Summarizer

A Flask web application that allows users to upload PDF files and get a summary of the content using Google's Gemini AI.

## Features

- Upload PDF files (up to 16MB)
- Extract text from PDF files
- Generate comprehensive summaries using Google's Gemini AI
- Clean and responsive user interface

## Setup

1. Clone this repository
2. Create a `.env` file in the root directory with your Google API key:
   ```
   GOOGLE_API_KEY=your_google_api_key_here
   ```
3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
4. Run the application:
   ```
   python app.py
   ```
5. Open your browser and navigate to `http://127.0.0.1:5000/`

## Requirements

- Python 3.7+
- Flask
- PyPDF2
- Google Generative AI Python SDK
- python-dotenv

## Usage

1. Access the web interface at `http://127.0.0.1:5000/`
2. Upload a PDF file using the form
3. Click "Generate Summary" to process the file
4. View the generated summary on the results page
5. Click "Upload Another PDF" to summarize another document

## Notes

- The maximum file size is limited to 16MB
- Only PDF files are accepted
- The quality of the summary depends on the clarity and structure of the PDF content
- The application uses Gemini 2.0 Flash model for generating summaries 
