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
from services.llm_service import extract_test_data_from_text, get_personalized_summary
from services.analysis_service import analyze_trends
from database.db_manager import setup_database, save_report, get_latest_report

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

# --- NEW: Add a frontend endpoint ---
@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    """Serves the main HTML page for the frontend."""
    return templates.TemplateResponse("index.html", {"request": request})

def preprocess_image_for_ocr(image_bytes: bytes) -> np.ndarray:
    """
    Applies a series of preprocessing steps to an image to improve OCR accuracy.
    """
    # 1. Decode the image from bytes to an OpenCV image
    image_np_array = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(image_np_array, cv2.IMREAD_COLOR)

    # 2. Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 3. Apply adaptive thresholding to binarize the image (pure black and white)
    # This is highly effective for cleaning up document backgrounds.
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )

    # 4. (Optional) Denoise the image. Useful for noisy scans.
    denoised = cv2.medianBlur(binary, 3)
    
    return denoised

# (OCR function and /simplify-report/ endpoint remain the same)
def perform_ocr(image_bytes: bytes) -> str:
    """
    Performs OCR on an in-memory image file after preprocessing.
    """
    try:
        # --- NEW: Preprocess the image first ---
        preprocessed_image = preprocess_image_for_ocr(image_bytes)

        # --- NEW: Add Tesseract configuration for better accuracy ---
        # --psm 6 assumes a single uniform block of text, which is good for many reports.
        custom_config = r'--oem 3 --psm 8'
        
        # Pass the preprocessed image directly to pytesseract
        text = pytesseract.image_to_string(preprocessed_image, config=custom_config)
        return text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")

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