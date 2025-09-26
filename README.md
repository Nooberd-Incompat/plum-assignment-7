# AI-Powered Medical Report Simplifier

## Project Overview
This project is a backend service built with FastAPI that simplifies medical reports for patients. It accepts typed text or scanned images of reports, extracts key test results, tracks them over time, and provides a personalized, easy-to-understand summary using AI.

## Features
- **OCR Support:** Extracts text from uploaded medical report images.
- **AI-Powered Extraction:** Uses Google's Gemini Pro to identify tests, values, and statuses from raw text, correcting common OCR errors.
- **Stateful History:** Stores report history for each user in an SQLite database.
- **Trend Analysis:** Compares the latest report with the previous one to identify trends (increasing, decreasing, stable).
- **Personalized Summaries:** Generates empathetic, non-technical explanations of results.
- **Simple Frontend:** Includes a basic web interface for easy interaction and demonstration.

## Architecture
The application is built using a modular Python backend:
- **FastAPI:** Serves the API endpoints and the HTML frontend.
- **SQLite:** Provides simple, file-based persistence for user report history.
- **Services Layer:**
  - `llm_service.py`: Handles all interactions with the Google Gemini API.
  - `analysis_service.py`: Contains the logic for trend analysis.
  - `db_manager.py`: Manages all database operations.
- **Frontend:** A single HTML file with vanilla JavaScript for API communication.

## Setup Instructions
1. Clone the repository:
   `git clone <your-repo-url>`
2. Navigate to the project directory:
   `cd medical-report-simplifier`
3. Create and activate a virtual environment:
   `python -m venv venv`
   `source venv/bin/activate`  # On Windows: `venv\Scripts\activate`
4. Install dependencies:
   `pip install -r requirements.txt`  *(You should create this file by running `pip freeze > requirements.txt`)*
5. Create a `.env` file and add your Google API key:
   `GOOGLE_API_KEY="YOUR_API_KEY_HERE"`
6. Run the application:
   `uvicorn main:app --reload`

## API Usage Example (cURL)

### Submit a Text Report
curl -X 'POST' \
  'http://127.0.0.1:8000/simplify-report/' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'user_id=patient-123' \
  -F 'report_text=CBC: Hemoglobin 11.9 g/dL (Low)'

### Submit an Image Report
curl -X 'POST' \
  'http://127.0.0.1:8000/simplify-report/' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'user_id=patient-456' \
  -F 'report_image=@/path/to/your/report.png'