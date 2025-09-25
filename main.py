import pytesseract
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from typing import Optional
from PIL import Image
import io

# --- Configuration for Tesseract ---
# If you're on Windows, you might need to specify the path to the Tesseract executable.
# For example: pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

app = FastAPI(
    title="AI-Powered Medical Report Simplifier",
    description="An API that simplifies medical reports using AI.",
    version="1.0.0"
)

def perform_ocr(image_bytes: bytes) -> str:
    """
    Performs OCR on an in-memory image file.
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        # Convert image to grayscale for better OCR accuracy
        grayscale_image = image.convert('L')
        text = pytesseract.image_to_string(grayscale_image)
        return text
    except Exception as e:
        # Raise an exception if OCR fails
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")

@app.get("/")
def read_root():
    """
    A simple endpoint to check if the API is running.
    """
    return {"status": "ok", "message": "Welcome to the Medical Report Simplifier API!"}

@app.post("/simplify-report/")
async def simplify_report(
    report_image: Optional[UploadFile] = File(None),
    report_text: Optional[str] = Form(None)
):
    """
    Accepts a medical report (either as an image or text) and returns the extracted raw text.
    """
    # --- Input Validation ---
    if not report_image and not report_text:
        raise HTTPException(status_code=400, detail="Please provide either a report image or report text.")
    if report_image and report_text:
        raise HTTPException(status_code=400, detail="Please provide either a report image or report text, not both.")
    
    extracted_text = ""
    
    # --- Process Input ---
    if report_text:
        extracted_text = report_text
    elif report_image:
        # Read the image file into memory as bytes
        image_bytes = await report_image.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="The uploaded image file is empty.")
       
        # Perform OCR on the image bytes
        extracted_text = perform_ocr(image_bytes)
    
    # For now, we just return the extracted text.
    # In the next steps, this text will be fed into our AI pipeline.
    return {"extracted_text": extracted_text}