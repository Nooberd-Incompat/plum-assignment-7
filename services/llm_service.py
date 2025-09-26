import os
import google.generativeai as genai
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()

# Configure the Gemini API
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not found. Please set it in your .env file.")
genai.configure(api_key=api_key)

# Initialize the generative model
model = genai.GenerativeModel('gemini-1.5-flash')

def extract_test_data_from_text(text: str) -> dict:
    """
    Uses an LLM to extract structured test data from raw text.
    """
    # This is our prompt. It tells the LLM exactly what to do.
    prompt = f"""
    You are a highly intelligent medical data extraction assistant.
    Your task is to analyze the following medical report text and extract key information for each test mentioned.
    
    Instructions:
    1. Identify each medical test.
    2. For each test, extract its value, unit, and status (e.g., Low, High, Normal).
    3. Correct any obvious OCR typos (e.g., "Hemglobin" -> "Hemoglobin", "Hgh" -> "High").
    4. Provide a confidence score between 0.0 and 1.0 for the overall extraction.
    5. Return the data in a clean JSON object format. Do not include any text or explanations outside of the JSON object.

    Example Input Text:
    "CBC: Hemglobin 10.2 g/dL (Low), WBC 11200 /uL (Hgh)"

    Expected JSON Output:
    {{
      "tests_raw": [
        {{"name": "Hemoglobin", "value": 10.2, "unit": "g/dL", "status": "Low"}},
        {{"name": "WBC", "value": 11200, "unit": "/uL", "status": "High"}}
      ],
      "confidence": 0.95
    }}

    ---
    Medical Report Text to Analyze:
    "{text}"
    ---
    JSON Output:
    """

    try:
        response = model.generate_content(prompt)
        # Clean up the response to ensure it's valid JSON
        json_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(json_text)
    except Exception as e:
        print(f"Error during LLM call or JSON parsing: {e}")
        # In case of an error, return a structured error message
        return {"error": "Failed to extract data from text.", "details": str(e)}
    
    # (Keep the existing imports and the extract_test_data_from_text function)

def get_personalized_summary(tests: list, patient_details: dict) -> dict:
    """
    Uses an LLM to generate a personalized, trend-aware summary.
    """
    # Convert the data into a string format for the prompt
    tests_str = json.dumps(tests, indent=2)
    details_str = json.dumps(patient_details.dict() if patient_details else {}, indent=2)

    prompt = f"""
    You are an empathetic medical AI assistant. Your goal is to explain medical test results to a patient in a simple, clear, and reassuring way.

    Instructions:
    1.  Review the patient's details and their latest test results provided below.
    2.  The 'trend' field indicates if a value is 'increasing', 'decreasing', or 'stable' compared to the last report. This is very important.
    3.  Generate a concise, easy-to-understand summary.
    4.  For any abnormal results, provide a simple one-sentence explanation of what the test relates to.
    5.  Highlight significant changes, especially if a test has worsened or improved.
    6.  **Crucially, DO NOT provide a diagnosis or medical advice. Use phrases like "This can sometimes indicate..." or "It's often related to..."**

    Patient Details:
    {details_str}

    Latest Test Results:
    {tests_str}

    ---
    Generate a JSON object with two keys: "summary" (a brief overall summary) and "explanations" (a list of strings for key takeaways).

    Example Output:
    {{
        "summary": "Overall, your results show a decrease in hemoglobin and an increase in white blood cells since your last report.",
        "explanations": [
            "Your hemoglobin, related to oxygen in your blood, has gone down and is currently low.",
            "Your white blood cell count, which can indicate infection, has increased and is now high.",
            "Other results remain stable."
        ]
    }}
    ---
    JSON Output:
    """

    try:
        response = model.generate_content(prompt)
        json_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(json_text)
    except Exception as e:
        print(f"Error during LLM summary call or JSON parsing: {e}")
        return {"error": "Failed to generate personalized summary.", "details": str(e)}