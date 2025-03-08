import flask
import werkzeug
import PyPDF2
import google.generativeai as genai
from dotenv import load_dotenv
import importlib.metadata

print("All imports successful!")
try:
    print(f"Flask version: {importlib.metadata.version('flask')}")
except Exception as e:
    print(f"Flask version check error: {e}")

try:
    print(f"Werkzeug version: {importlib.metadata.version('werkzeug')}")
except Exception as e:
    print(f"Werkzeug version check error: {e}")

try:
    print(f"PyPDF2 version: {PyPDF2.__version__}")
except Exception as e:
    print(f"PyPDF2 version check error: {e}")

try:
    print(f"Google Generative AI version: {importlib.metadata.version('google-generativeai')}")
except Exception as e:
    print(f"Google Generative AI version check error: {e}") 