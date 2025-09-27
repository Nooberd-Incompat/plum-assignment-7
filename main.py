from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
import io
from PIL import Image
import pytesseract
from contextlib import asynccontextmanager
import numpy  as np
import cv2
from services.llm_service import create_extraction_prompt, create_summary_prompt, extract_test_data_from_text, get_personalized_summary
from services.analysis_service import analyze_trends
from database.db_manager import get_all_reports, setup_database, save_report, get_latest_report

# --- NEW: Configure templates ---
templates = Jinja2Templates(directory="templates")

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Setting up database...")
    setup_database()
    yield
    print("Shutting down...")

app = FastAPI(
    title="AI-Powered Medical Report Simplifier",
    description="A stateful API that personalizes and simplifies medical reports.",
    version="3.0.0",
    lifespan=lifespan
)

@app.get('/')
async def root():
    return {"message": "Welcome to the AI-Powered Medical Report Simplifier API. Visit /docs for API documentation or /home for a simple frontend interface."}

# --- NEW: Add a frontend endpoint ---
@app.get("/home", response_class=HTMLResponse)
async def read_item(request: Request):
    """Serves the main HTML page for the frontend."""
    return templates.TemplateResponse("index.html", {"request": request})

def preprocess_image_for_ocr(image_bytes: bytes) -> np.ndarray:
    """
    Applies a more robust preprocessing pipeline for scanned documents.
    """
    # 1. Decode the image from bytes to an OpenCV image
    image_np_array = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(image_np_array, cv2.IMREAD_COLOR)

    # 2. Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 3. Apply a Gaussian blur to reduce noise, which helps Otsu's method
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # 4. Apply Otsu's Binarization. This automatically finds the best threshold.
    # We invert the image (THRESH_BINARY_INV) so the text is white and the background is black.
    _, binary_image = cv2.threshold(
        blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )
    
    return binary_image


def perform_ocr(image_bytes: bytes) -> str:
    """
    Performs OCR on an in-memory image file using the new preprocessing pipeline.
    """
    try:
        # Preprocess the image using our new, more robust function
        preprocessed_image = preprocess_image_for_ocr(image_bytes)

        # --- Tesseract Configuration Change ---
        # Switch to PSM 3 (fully automatic layout detection), which can be better for tables.
        custom_config = r'--oem 3 --psm 3'
        
        text = pytesseract.image_to_string(preprocessed_image, config=custom_config)
        return text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")

@app.post("/debug/preview-prompts/")
async def debug_preview_prompts(
    user_id: str = Form(...),
    report_image: Optional[UploadFile] = File(None),
    report_text: Optional[str] = Form(None),
):
    """
    A debug endpoint to see the generated prompts without calling the AI.
    """
    # This logic is copied from the main /simplify-report endpoint
    if not report_image and not report_text:
        raise HTTPException(status_code=400, detail="Please provide a report...")

    extracted_text = ""
    if report_text:
        extracted_text = report_text
    elif report_image:
        image_bytes = await report_image.read()
        preprocessed_image = preprocess_image_for_ocr(image_bytes)
        extracted_text = pytesseract.image_to_string(preprocessed_image, config=r'--oem 3 --psm 6')

    # Generate the first prompt
    extraction_prompt = create_extraction_prompt(extracted_text)

    # Simulate the data flow to generate the second prompt
    # NOTE: This uses a dummy extraction result for preview purposes
    dummy_extracted_tests = [
        {"name": "Hemoglobin", "value": 10.2, "unit": "g/dL", "status": "Low"},
        {"name": "WBC", "value": 11200, "unit": "/uL", "status": "High"}
    ]
    previous_report = get_latest_report(user_id)
    previous_tests = previous_report.get("tests") if previous_report else None
    if previous_tests:
        dummy_extracted_tests = analyze_trends(dummy_extracted_tests, previous_tests)
    
    summary_prompt = create_summary_prompt(dummy_extracted_tests, patient_details=None)
    
    return {
        "extraction_prompt": extraction_prompt,
        "summary_prompt_preview": summary_prompt
    }

@app.post("/simplify-report/")
async def simplify_report(
    user_id: str = Form(...),
    report_image: Optional[UploadFile] = File(None),
    report_text: Optional[str] = Form(None),
):
    # ... (code for this endpoint is unchanged)
    if not report_image and not report_text:
        raise HTTPException(status_code=400, detail="Please provide a report image or text.")
    
    extracted_text = ""
    if report_text:
        extracted_text = report_text
    elif report_image:
        image_bytes = await report_image.read()
        extracted_text = perform_ocr(image_bytes)
        print("--- RAW OCR OUTPUT ---")
        print(extracted_text)
        print("----------------------")


    previous_report = get_latest_report(user_id)
    previous_tests = previous_report.get("tests") if previous_report else None

    extraction_result = extract_test_data_from_text(extracted_text)
    current_tests = extraction_result.get("tests_raw", [])

    if not current_tests:
        raise HTTPException(
            status_code=422, 
            detail="The AI could not identify any valid medical tests in the provided text. Please check the input."
        )

    if previous_tests:
        current_tests = analyze_trends(current_tests, previous_tests)

    summary_data = get_personalized_summary(current_tests, patient_details=None)

    final_report = {
        "user_id": user_id,
        "tests": current_tests,
        "summary_data": summary_data
    }

    save_report(user_id, final_report)

    return final_report

@app.get("/history/{user_id}")
async def get_user_history(user_id: str):
    """
    Retrieves all saved reports for a specific user.
    """
    history = get_all_reports(user_id)
    if not history:
        raise HTTPException(status_code=404, detail="No history found for this user.")
    return history