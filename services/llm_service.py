import os
import requests
from dotenv import load_dotenv
import json
import cv2
import numpy as np

# Load environment variables from .env file
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not found. Please set it in your .env file.")

MODEL_NAME = "gemini-2.5-flash"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={api_key}"

print(">>>>>> LLM SERVICE CONFIGURED FOR DIRECT HTTP API CALLS USING gemini-2.5-flash <<<<<<")


def call_gemini_api(prompt: str) -> dict:
    headers = {'Content-Type': 'application/json'}
    
    # --- FIX: Add generationConfig to allow for larger responses ---
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 8192  # Increased from default to handle long reports
        }
    }

    try:
        # Make the POST request to the API
        response = requests.post(URL, headers=headers, json=data)
        response.raise_for_status()
        
        response_json = response.json()
        
        json_text = response_json['candidates'][0]['content']['parts'][0]['text']
        json_text = json_text.strip().replace("```json", "").replace("```", "").strip()
        
        return json.loads(json_text)

    except requests.exceptions.RequestException as e:
        # This will now correctly send a 503 Service Unavailable error
        raise HTTPException(status_code=503, detail=f"AI service is unavailable: {e}")
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        # This will now correctly send a 500 Internal Server Error
        raise HTTPException(status_code=500, detail=f"Error parsing AI response: {e}")


def extract_test_data_from_text(text: str) -> dict:
    # ... (rest of the file is unchanged)
    prompt = f"""
    You are a medical data extraction assistant. Analyze the following medical report text, correct OCR typos, and extract tests into a clean JSON object.
    Input Text: "CBC: Hemglobin 10.2 g/dL (Low), WBC 11200 /uL (Hgh)"
    JSON Output: {{"tests_raw": [{{"name": "Hemoglobin", "value": 10.2, "unit": "g/dL", "status": "Low"}}, {{"name": "WBC", "value": 11200, "unit": "/uL", "status": "High"}}], "confidence": 0.95}}
    ---
    Input Text: "{text}"
    ---
    JSON Output:
    """
    return call_gemini_api(prompt)

def get_personalized_summary(tests: list, patient_details) -> dict:
    # ... (rest of the file is unchanged)
    tests_str = json.dumps(tests, indent=2)
    details_str = json.dumps(patient_details.dict() if patient_details else {"age": "N/A", "sex": "N/A"})

    prompt = f"""
    You are an empathetic medical AI assistant. Explain the test results to a patient simply. The 'trend' field shows changes. **Do not diagnose.**
    Patient Details: {details_str}
    Latest Test Results: {tests_str}
    ---
    Generate a JSON object with "summary" and "explanations" keys.
    ---
    JSON Output:
    """
    return call_gemini_api(prompt)