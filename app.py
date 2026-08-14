import os
import tempfile
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse
from src.pipeline import PIIRedactionPipeline

# Set up logging with zero PII exposure policy
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pii_redactor_app")

app = FastAPI(title="PII Redaction Tool")

# Maximum upload size limit (15 MB)
MAX_UPLOAD_SIZE = 15 * 1024 * 1024

def cleanup_files(*filepaths):
    """Safely deletes temporary files after response completion."""
    for path in filepaths:
        try:
            if path and os.path.exists(path):
                os.remove(path)
                logger.info(f"Cleaned up temporary file: {path}")
        except Exception as e:
            logger.error(f"Error deleting temporary file {path}: {str(e)}")

# Mount static directory for style.css and script.js
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_index():
    """Serves the professional modern web UI."""
    try:
        with open("templates/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Index template not found.")


@app.post("/redact")
async def redact_docx(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Uploads a DOCX file, runs the redaction pipeline, and returns the redacted file."""
    # Validate file type
    if not file.filename.lower().endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only .docx files are accepted.")
        
    # Read first chunk of file to determine size
    contents = await file.read(1024)
    size = len(contents)
    
    # Read remaining file content in chunks
    chunks = [contents]
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        size += len(chunk)
        if size > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413, 
                detail=f"File exceeds maximum upload size of {MAX_UPLOAD_SIZE / (1024 * 1024)} MB."
            )
        chunks.append(chunk)
        
    full_content = b"".join(chunks)
    
    # Paths for temporary input/output files
    temp_dir = tempfile.gettempdir()
    temp_input_fd, temp_input_path = tempfile.mkstemp(suffix=".docx", dir=temp_dir)
    temp_output_path = os.path.join(temp_dir, f"redacted_{os.path.basename(temp_input_path)}")
    
    try:
        # Write contents to temporary input file
        with os.fdopen(temp_input_fd, "wb") as f:
            f.write(full_content)
            
        logger.info("Processing temporary uploaded file...")
        
        # Run existing pipeline (reusing current architecture)
        pipeline = PIIRedactionPipeline()
        summary = pipeline.run(temp_input_path, temp_output_path)
        
        logger.info("PII Redaction completed successfully.")
        
        # Clean up both temp files after response is sent
        background_tasks.add_task(cleanup_files, temp_input_path, temp_output_path)
        
        original_base, ext = os.path.splitext(file.filename)
        output_filename = f"{original_base}_redacted{ext}"
        
        headers = {
            "Access-Control-Expose-Headers": "X-Candidates-Detected, X-Candidates-Accepted, X-Candidates-Rejected",
            "X-Candidates-Detected": str(summary.candidates_detected),
            "X-Candidates-Accepted": str(summary.candidates_accepted),
            "X-Candidates-Rejected": str(summary.candidates_rejected)
        }
        
        return FileResponse(
            path=temp_output_path,
            filename=output_filename,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers=headers
        )
        
    except Exception as e:
        # Immediately cleanup input file in case of error
        cleanup_files(temp_input_path, temp_output_path)
        logger.exception("An error occurred during pipeline execution")
        raise HTTPException(status_code=500, detail=f"Failed to redact document: {str(e)}")
