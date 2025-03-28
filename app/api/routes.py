from fastapi import APIRouter, UploadFile, File, HTTPException, Path, Query
from typing import Optional, Dict
from app.services.document_service import DocumentService
from app.models.document import Document, FolderAnalysis
import shutil
from pathlib import Path

router = APIRouter()
document_service = DocumentService()

@router.post("/documents/upload", response_model=Document)
async def upload_document(file: UploadFile = File(...)):
    """Upload a new document."""
    try:
        # Create a temporary file to store the upload
        temp_path = Path(f"temp_{file.filename}")
        with temp_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process the document
        document = document_service.create_document(temp_path)
        
        # Move the file to the permanent location
        final_path = Path(document_service.base_directory) / document.path
        final_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(temp_path), str(final_path))
        
        return document
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/{document_id}", response_model=Document)
async def get_document(document_id: str):
    """Get a specific document by ID."""
    document = document_service.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document

@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document by ID."""
    success = document_service.delete_document(document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Document deleted successfully"}

@router.get("/folders/analysis", response_model=FolderAnalysis)
async def analyze_folder(folder_path: Optional[str] = None):
    """Analyze contents of a folder."""
    try:
        return await document_service.analyze_folder(folder_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/folders/insights", response_model=Dict)
async def get_folder_insights(
    folder_path: Optional[str] = None,
    include_classification: bool = Query(True, description="Include document classification analysis"),
    batch_size: int = Query(5, description="Number of documents to process in each batch")
):
    """Get comprehensive insights about a folder's contents."""
    try:
        return await document_service.get_folder_insights(folder_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents", response_model=list[Document])
async def list_documents():
    """List all documents in the system."""
    analysis = await document_service.analyze_folder()
    return analysis.documents 