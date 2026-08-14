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

@app.get("/", response_class=HTMLResponse)
async def read_index():
    """Serves the simple upload HTML page."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PII Redaction Tool</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                background-color: #f9fafb;
                color: #111827;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                margin: 0;
            }
            .card {
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
                padding: 32px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
                max-width: 450px;
                width: 100%;
                box-sizing: border-box;
                text-align: center;
            }
            h1 {
                font-size: 24px;
                font-weight: 700;
                margin-top: 0;
                margin-bottom: 12px;
            }
            p {
                font-size: 14px;
                color: #4b5563;
                margin-bottom: 24px;
                line-height: 1.5;
            }
            input[type="file"] {
                display: block;
                width: 100%;
                margin-bottom: 24px;
                font-size: 14px;
            }
            button {
                background-color: #2563eb;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                width: 100%;
                transition: background-color 0.2s;
            }
            button:hover {
                background-color: #1d4ed8;
            }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>PII Redaction Tool</h1>
            <p>Upload a DOCX document to detect and replace supported PII.</p>
            <form action="/redact" method="post" enctype="multipart/form-data">
                <input type="file" name="file" accept=".docx" required>
                <button type="submit">Redact Document</button>
            </form>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

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
        pipeline.run(temp_input_path, temp_output_path)
        
        logger.info("PII Redaction completed successfully.")
        
        # Clean up both temp files after response is sent
        background_tasks.add_task(cleanup_files, temp_input_path, temp_output_path)
        
        original_base, ext = os.path.splitext(file.filename)
        output_filename = f"{original_base}_redacted{ext}"
        
        return FileResponse(
            path=temp_output_path,
            filename=output_filename,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
    except Exception as e:
        # Immediately cleanup input file in case of error
        cleanup_files(temp_input_path, temp_output_path)
        logger.exception("An error occurred during pipeline execution")
        raise HTTPException(status_code=500, detail=f"Failed to redact document: {str(e)}")
