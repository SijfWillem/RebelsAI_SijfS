from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
import os
import json
import magic
from datetime import datetime
import shutil
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
from dotenv import load_dotenv
import asyncio
from concurrent.futures import ThreadPoolExecutor
import hashlib
import pickle
from pathlib import Path
import docx
import PyPDF2
import csv
import io
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Document Analysis API",
    description="API for analyzing and classifying documents using AI",
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

# Initialize Mistral client
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
if not MISTRAL_API_KEY:
    raise ValueError("MISTRAL_API_KEY environment variable is not set")

mistral_client = MistralClient(api_key=MISTRAL_API_KEY)

# Create cache directory
CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

# Classification prompt in English
CLASSIFICATION_PROMPT = """
Analyze the following text and determine its main subject or theme.
Return only the main subject as a single word or short phrase (maximum 3 words), without any additional text or explanation.
Focus on the most relevant subject that best describes the document.
The subject can be in any language that best represents the content.

Text:
{text}
"""

# Create upload directory if it doesn't exist
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Maximum text length for classification (to avoid processing very large files)
MAX_TEXT_LENGTH = 5000

def get_file_type(file_path: str) -> str:
    """Get the file extension in uppercase."""
    return os.path.splitext(file_path)[1].upper().lstrip('.')

def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX files."""
    try:
        doc = docx.Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text[:MAX_TEXT_LENGTH]
    except Exception as e:
        logger.error(f"Error extracting text from DOCX {file_path}: {str(e)}")
        return ""

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF files."""
    try:
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
                if len(text) >= MAX_TEXT_LENGTH:
                    break
        return text[:MAX_TEXT_LENGTH]
    except Exception as e:
        logger.error(f"Error extracting text from PDF {file_path}: {str(e)}")
        return ""

def extract_text_from_csv(file_path: str) -> str:
    """Extract text from CSV files."""
    try:
        text = ""
        with open(file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                text += " ".join(row) + "\n"
                if len(text) >= MAX_TEXT_LENGTH:
                    break
        return text[:MAX_TEXT_LENGTH]
    except Exception as e:
        logger.error(f"Error extracting text from CSV {file_path}: {str(e)}")
        return ""

def read_text_file(file_path: str) -> str:
    """Read text content from a file with length limit."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read(MAX_TEXT_LENGTH)
            return content
    except UnicodeDecodeError:
        logger.error(f"Unicode decode error for file {file_path}")
        return ""

def extract_text_content(file_path: str, mime_type: str) -> str:
    """Extract text content from various file types."""
    if mime_type.startswith('text/'):
        return read_text_file(file_path)
    elif mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        return extract_text_from_docx(file_path)
    elif mime_type == 'application/pdf':
        return extract_text_from_pdf(file_path)
    elif mime_type == 'text/csv':
        return extract_text_from_csv(file_path)
    logger.warning(f"Unsupported file type: {mime_type} for {file_path}")
    return ""

def get_cache_key(text: str, file_path: str) -> str:
    """Generate a cache key for the text content and file path."""
    combined = f"{text}:{file_path}"
    return hashlib.md5(combined.encode()).hexdigest()

def get_cached_classification(text: str, file_path: str) -> Dict[str, Any]:
    """Get classification from cache if available."""
    cache_key = get_cache_key(text, file_path)
    cache_file = CACHE_DIR / f"{cache_key}.pkl"
    
    if cache_file.exists():
        try:
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logger.error(f"Error reading cache for {file_path}: {str(e)}")
            return None
    return None

def save_to_cache(text: str, file_path: str, classification: Dict[str, Any]):
    """Save classification to cache."""
    cache_key = get_cache_key(text, file_path)
    cache_file = CACHE_DIR / f"{cache_key}.pkl"
    
    try:
        with open(cache_file, 'wb') as f:
            pickle.dump(classification, f)
    except Exception as e:
        logger.error(f"Error saving to cache for {file_path}: {str(e)}")

def classify_document(text: str, file_path: str) -> Dict[str, Any]:
    """Classify document using Mistral AI with caching."""
    if not text.strip():
        return {
            "category": "No subject",
            "confidence": 0.5
        }
    
    # Check cache first
    cached_result = get_cached_classification(text, file_path)
    if cached_result:
        logger.info(f"Using cached classification for {file_path}")
        return cached_result
    
    try:
        messages = [
            ChatMessage(role="user", content=CLASSIFICATION_PROMPT.format(text=text))
        ]
        
        logger.info(f"Sending text to AI for {file_path}")
        chat_response = mistral_client.chat(
            model="mistral-tiny",
            messages=messages
        )
        
        # Extract the classification from the response
        raw_response = chat_response.choices[0].message.content.strip()
        logger.info(f"Raw AI response for {file_path}: {raw_response}")
        
        # Clean up the classification (remove any extra text or punctuation)
        classification = raw_response.split('\n')[0].strip('.,!?')
        logger.info(f"Cleaned classification for {file_path}: {classification}")
        
        result = {
            "category": classification,
            "confidence": 0.8  # Default confidence since Mistral doesn't provide it
        }
        
        # Save to cache
        save_to_cache(text, file_path, result)
        return result
        
    except Exception as e:
        logger.error(f"Error classifying document {file_path}: {str(e)}")
        return {
            "category": "No subject",
            "confidence": 0.5
        }

async def process_file(file_path: str) -> Dict[str, Any]:
    """Process a single file asynchronously."""
    try:
        file_size = os.path.getsize(file_path)
        file_type = get_file_type(file_path)
        
        # Extract and classify text content
        classification = None
        mime_type = magic.Magic(mime=True).from_file(file_path)
        text_content = extract_text_content(file_path, mime_type)
        
        if text_content:
            # Run classification in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as pool:
                classification = await loop.run_in_executor(pool, classify_document, text_content, file_path)
                logger.info(f"Final classification for {file_path}: {classification['category']}")
        
        return {
            "filename": os.path.basename(file_path),
            "file_type": file_type,
            "size": file_size,
            "modified_at": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
            "classification": classification
        }
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {str(e)}")
        return {
            "filename": os.path.basename(file_path),
            "error": str(e)
        }

@app.post("/api/analyze-folder")
async def analyze_folder(folder_path: str):
    """Analyze all documents in a folder."""
    try:
        if not os.path.exists(folder_path):
            raise HTTPException(status_code=404, detail="Folder not found")
            
        documents = []
        total_size = 0
        document_types = {}
        classification_distribution = {}
        
        # Collect all files first
        files_to_process = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                files_to_process.append(file_path)
        
        logger.info(f"Processing {len(files_to_process)} files...")
        
        # Process files concurrently
        tasks = [process_file(file_path) for file_path in files_to_process]
        documents = await asyncio.gather(*tasks)
        
        # Process results
        for doc in documents:
            if "error" in doc:
                logger.error(f"Error processing document: {doc['error']}")
                continue
                
            total_size += doc["size"]
            document_types[doc["file_type"]] = document_types.get(doc["file_type"], 0) + 1
            
            if doc["classification"]:
                category = doc["classification"]["category"]
                classification_distribution[category] = classification_distribution.get(category, 0) + 1
        
        return {
            "total_files": len(documents),
            "total_size": total_size,
            "document_types": document_types,
            "classification_distribution": classification_distribution,
            "documents": documents
        }
        
    except Exception as e:
        logger.error(f"Error analyzing folder: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/folder-insights")
async def get_folder_insights(folder_path: str):
    """Get insights for a folder."""
    try:
        if not os.path.exists(folder_path):
            raise HTTPException(status_code=404, detail="Folder not found")
            
        # Reuse the analyze_folder endpoint for insights
        analysis = await analyze_folder(folder_path)
        
        return {
            "summary": {
                "total_files": analysis["total_files"],
                "total_size": analysis["total_size"],
                "document_types": analysis["document_types"],
                "classification_distribution": analysis["classification_distribution"]
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting folder insights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents")
async def get_documents(folder_path: str):
    """Get list of documents in a folder."""
    try:
        if not os.path.exists(folder_path):
            raise HTTPException(status_code=404, detail="Folder not found")
            
        documents = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                doc_info = await process_file(file_path)
                documents.append(doc_info)
        
        return {"documents": documents}
        
    except Exception as e:
        logger.error(f"Error getting documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 