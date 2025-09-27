import os
import requests
from dotenv import load_dotenv
import json
import cv2
import numpy as np
import json
# Load environment variables from .env file
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not found. Please set it in your .env file.")

MODEL_NAME = "gemini-2.5-flash"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={api_key}"

print(">>>>>> LLM SERVICE CONFIGURED FOR DIRECT HTTP API CALLS USING gemini-2.5-flash <<<<<<")

# --- Refactored prompt creation into its own function ---
def create_summary_prompt(tests: list, patient_details) -> str:
    """Creates the prompt for the personalized summary."""
    tests_str = json.dumps(tests, indent=2)
    details_str = json.dumps(patient_details.dict() if patient_details else {"age": "N/A", "sex": "N/A"})

    return f"""
    You are an empathetic medical AI assistant. Explain the test results to a patient simply. Reduce medical jargon. The 'trend' field shows changes. **Do not diagnose.**
    Patient Details: {details_str}
    Latest Test Results: {tests_str}
    ---
    Generate a JSON object with "summary", "status" and "explanations" keys.
    ---
    JSON Output:
    """

def call_gemini_api(prompt: str) -> dict:
    # ... (This function remains exactly the same as before)
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 8192}
    }
    try:
        response = requests.post(URL, headers=headers, json=data)
        response.raise_for_status()
        response_json = response.json()
        json_text = response_json['candidates'][0]['content']['parts'][0]['text']
        json_text = json_text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(json_text)
    except Exception as e:
        # Handle exceptions...
        return {"error": "API call failed", "details": str(e)}

# --- FIX: A much more robust prompt for extraction ---
# ... (keep all other code in the file the same)

def create_extraction_prompt(text: str) -> str:
    """Creates a final, more robust prompt designed to handle messy OCR text."""
    
    example_output = {
        "tests_raw": [
            {"name": "Hemoglobin", "value": 10.2, "unit": "g/dL", "status": "Low"},
            {"name": "WBC", "value": 11200, "unit": "/uL", "status": "High"}
        ],
        "confidence": 0.95
    }
    example_json_string = json.dumps(example_output)

    prompt = f"""
    You are a specialist AI for cleaning and extracting data from messy, imperfect Optical Character Recognition (OCR) text from medical reports.

    **CRITICAL INSTRUCTIONS:**
    1.  The following "Input Text" is noisy and contains many errors, garbage characters, and incorrect spacing from a low-quality scan.
    2.  Your primary goal is to intelligently parse this messy text to identify any medical tests, their values, and their units.
    3.  Ignore all non-medical text, headers, footers, and random characters.
    4.  Infer the correct test names and values even if they are misspelled or jumbled (e.g., "Hemglobin" is "Hemoglobin", "RBC aunt" is "RBC Count").
    5.  Extract the data into the specified JSON format. If you cannot confidently extract any tests, return an empty list for "tests_raw".

    **Example Format:**
    {example_json_string}

    ---
    Input Text:
    "{text}"
    ---
    JSON Output:
    """
    return prompt

def extract_test_data_from_text(text: str) -> dict:
    """Prepares the prompt for data extraction and calls the API."""
    prompt = create_extraction_prompt(text)
    return call_gemini_api(prompt)

def get_personalized_summary(tests: list, patient_details) -> dict:
    """Prepares the prompt for summarization and calls the API."""
    prompt = create_summary_prompt(tests, patient_details)
    return call_gemini_api(prompt)