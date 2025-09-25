from fastapi import FastAPI

# Create an instance of the FastAPI class
app = FastAPI(
    title="AI-Powered Medical Report Simplifier",
    description="An API that simplifies medical reports using AI.",
    version="1.0.0"
)

# Define a root endpoint
@app.get("/")
def read_root():
    """
    A simple endpoint to check if the API is running.
    """
    return {"status": "ok", "message": "Welcome to the Medical Report Simplifier API!"}