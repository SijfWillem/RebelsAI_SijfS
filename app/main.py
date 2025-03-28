from fastapi import FastAPI, HTTPException, Query, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, Dict, List
from app.services.document_service import DocumentService
from app.services.classification_service import ClassificationService
from app.models.document import Document, DocumentType, DocumentStatus, FolderAnalysis
import asyncio
from pathlib import Path
import time
from functools import lru_cache
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Document Management and Analysis API",
    description="API for managing and analyzing documents within folders",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency injection for services
@lru_cache()
def get_document_service():
    return DocumentService()

@lru_cache()
def get_classification_service():
    return ClassificationService()

@app.get("/")
async def root():
    return {
        "message": "Welcome to Document Management and Analysis API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

@app.get("/api/folder-insights")
async def get_folder_insights(folder_path: str):
    """Get insights about a folder."""
    try:
        logger.info(f"Getting insights for folder: {folder_path}")
        if not os.path.exists(folder_path):
            logger.error(f"Folder path does not exist: {folder_path}")
            raise HTTPException(status_code=404, detail="Folder path does not exist")
        
        analysis, _ = await get_document_service().analyze_folder(folder_path)
        return analysis
    except Exception as e:
        logger.error(f"Error getting folder insights: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents")
async def get_documents(folder_path: str):
    """Get a list of documents in a folder."""
    try:
        logger.info(f"Getting documents for folder: {folder_path}")
        if not os.path.exists(folder_path):
            logger.error(f"Folder path does not exist: {folder_path}")
            raise HTTPException(status_code=404, detail="Folder path does not exist")
        
        analysis, _ = await get_document_service().analyze_folder(folder_path)
        return {"documents": analysis.documents}
    except Exception as e:
        logger.error(f"Error getting documents: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents/{document_id}")
async def get_document(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service)
):
    """Get a specific document by ID."""
    try:
        document = await document_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document.dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/documents/{document_id}")
async def delete_document(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service)
):
    """Delete a specific document by ID."""
    try:
        success = await document_service.delete_document(document_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"message": "Document deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/document-types")
async def get_document_types():
    """Get a list of all supported document types."""
    return {"document_types": [doc_type.value for doc_type in DocumentType]}

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time()
    }

@app.post("/api/analyze-folder")
async def analyze_folder(folder_path: str):
    """Analyze a folder and return insights."""
    try:
        logger.info(f"Received request to analyze folder: {folder_path}")
        if not os.path.exists(folder_path):
            logger.error(f"Folder path does not exist: {folder_path}")
            raise HTTPException(status_code=404, detail="Folder path does not exist")
        
        analysis, total_documents = await get_document_service().analyze_folder(folder_path)
        logger.info(f"Analysis completed. Total documents: {total_documents}")
        return analysis
    except Exception as e:
        logger.error(f"Error analyzing folder: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload-folder")
async def upload_folder(
    files: List[UploadFile] = File(...),
    document_service: DocumentService = Depends(get_document_service)
):
    """Upload a folder of files and analyze its contents."""
    try:
        # Create a temporary directory for uploads
        upload_dir = "temp_uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save all files
        for file in files:
            if file.filename:
                file_path = os.path.join(upload_dir, file.filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "wb") as f:
                    content = await file.read()
                    f.write(content)
                logger.info(f"Saved file: {file_path}")
        
        # Analyze the uploaded folder
        insights = await document_service.analyze_folder(upload_dir)
        return {"data": insights}
    except Exception as e:
        logger.error(f"Error uploading folder: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents")
async def get_documents():
    try:
        documents = get_document_service().get_all_documents()
        return {"data": documents}
    except Exception as e:
        logger.error(f"Error getting documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/folder-insights")
async def get_folder_insights():
    try:
        insights = get_document_service().get_folder_insights()
        return {"data": insights}
    except Exception as e:
        logger.error(f"Error getting folder insights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 