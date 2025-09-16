from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from celery_worker import process_file
from transformers import pipeline
import os
from document_manager import DocumentManager
from auth import verify_user, Role
from typing import List
from celery.result import AsyncResult

app = FastAPI()

# Initialize Hugging Face Summarization Model
summarizer = pipeline("summarization", model="t5-small")

# Directory for uploaded documents
UPLOAD_DIRECTORY = "./uploaded_documents"

# Initialize Document Manager for handling document lifecycle (versioning, etc.)
document_manager = DocumentManager()

# Upload multiple documents with user role verification
@app.post("/upload/")
async def upload_documents(
    background_tasks: BackgroundTasks, 
    files: List[UploadFile] = File(...), 
    user_role: Role = Role.EDITOR
):
    if not verify_user(user_role, required_role=Role.EDITOR):
        raise HTTPException(status_code=403, detail="Insufficient permissions.")

    task_ids = []
    for file in files:
        file_type = file.filename.split('.')[-1]
        file_path = os.path.join(UPLOAD_DIRECTORY, file.filename)

        # Save the uploaded file
        with open(file_path, "wb") as buffer:
            buffer.write(file.file.read())

        # Add file to document manager with metadata
        document_manager.add_document(file.filename, file_path, file_size=file.size, file_type=file.content_type)

        # Initiate background processing and track task ID
        task = background_tasks.add_task(process_file, file_path, file_type)
        task_ids.append(task.id)

    return {"message": f"{len(files)} files uploaded successfully.", "task_ids": task_ids}

# Fetch document details, including metadata and version history
@app.get("/document/{doc_id}")
async def get_document(doc_id: str):
    # Retrieve document details from the document manager
    doc = document_manager.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    return JSONResponse(content=doc)

# Revert to a specific document version
@app.post("/document/{doc_id}/revert/")
async def revert_document(doc_id: str, version: str, user_role: Role = Role.EDITOR):
    # Verify if the user has required permissions (Editor or Admin)
    if not verify_user(user_role, required_role=Role.EDITOR):
        raise HTTPException(status_code=403, detail="Insufficient permissions.")

    # Revert the document to the specified version
    result = document_manager.revert_document(doc_id, version)
    
    return {"message": result}

# Summarize document content using Hugging Face model
@app.post("/document/{doc_id}/summarize/")
async def summarize_document(doc_id: str):
    # Fetch the document content
    doc_content = document_manager.get_document_content(doc_id)

    if not doc_content:
        raise HTTPException(status_code=404, detail="Document content not found.")

    # Generate the summary using Hugging Face summarizer
    summary = summarizer(doc_content, max_length=150, min_length=50, do_sample=False)
    
    return {"summary": summary[0]['summary_text']}

# Summarize multiple documents
@app.post("/summarize_multiple/")
async def summarize_multiple_documents(files: List[UploadFile] = File(...)):
    combined_text = ""
    for file in files:
        file_content = await file.read()
        combined_text += file_content.decode("utf-8") + "\n"

    # Generate a combined summary from all document content
    summary = summarizer(combined_text, max_length=300, min_length=100, do_sample=False)

    return {"summary": summary[0]['summary_text']}

# Fetch task progress status
@app.get("/task_status/{task_id}")
async def get_task_status(task_id: str):
    task_result = AsyncResult(task_id)
    if task_result.state == 'PENDING':
        return {"status": "Pending..."}
    elif task_result.state == 'PROGRESS':
        return {"status": "In Progress", "progress": task_result.info.get('progress', 0)}
    elif task_result.state == 'SUCCESS':
        return {"status": "Completed", "result": task_result.result}
    else:
        return {"status": str(task_result.state)}
