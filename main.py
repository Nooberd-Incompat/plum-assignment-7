from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from typing import Optional
import io
from PIL import Image
import pytesseract
from contextlib import asynccontextmanager

# Import services and the new db_manager
from services.llm_service import extract_test_data_from_text, get_personalized_summary
from services.analysis_service import analyze_trends
from database.db_manager import setup_database, save_report, get_latest_report

# --- Lifespan Event to Set Up Database on Startup ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code to run on startup
    print("Setting up database...")
    setup_database()
    yield
    # Code to run on shutdown (if any)
    print("Shutting down...")

app = FastAPI(
    title="AI-Powered Medical Report Simplifier",
    description="A stateful API that personalizes and simplifies medical reports.",
    version="3.0.0", # Version bump for the new feature!
    lifespan=lifespan
)

# (OCR function remains the same)
def perform_ocr(image_bytes: bytes) -> str:
    try:
        image = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(image.convert('L'))
        return text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Welcome to the Medical Report Simplifier API!"}

@app.post("/simplify-report/")
async def simplify_report(
    user_id: str = Form(...), # User ID is now a required form field
    report_image: Optional[UploadFile] = File(None),
    report_text: Optional[str] = Form(None),
    # We no longer need the context object from the user
):
    # (Input validation and OCR logic remains the same)
    if not report_image and not report_text:
        raise HTTPException(status_code=400, detail="Please provide a report image or text.")
    # ...

    extracted_text = ""
    if report_text:
        extracted_text = report_text
    elif report_image:
        image_bytes = await report_image.read()
        extracted_text = perform_ocr(image_bytes)

    # --- NEW WORKFLOW ---

    # 1. Get previous report from DB
    previous_report = get_latest_report(user_id)
    previous_tests = previous_report.get("tests") if previous_report else None

    # 2. Process current report
    extraction_result = extract_test_data_from_text(extracted_text)
    current_tests = extraction_result.get("tests_raw", [])

    # 3. Analyze trends if previous data exists
    if previous_tests:
        current_tests = analyze_trends(current_tests, previous_tests)

    # 4. Generate the personalized summary (we'll just use a placeholder for patient details for now)
    summary_data = get_personalized_summary(current_tests, patient_details=None)

    # 5. Assemble the final report object
    final_report = {
        "user_id": user_id,
        "tests": current_tests,
        "summary_data": summary_data
    }

    # 6. Save the new report to the DB for next time
    save_report(user_id, final_report)

    return final_report