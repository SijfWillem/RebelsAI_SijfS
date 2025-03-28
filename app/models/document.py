from enum import Enum
from datetime import datetime
from typing import Optional, Dict, List
from pydantic import BaseModel, Field
import uuid

class DocumentType(str, Enum):
    """Supported document types."""
    PDF = "PDF"
    DOCX = "DOCX"
    TXT = "TXT"
    XLSX = "XLSX"
    PPTX = "PPTX"
    JPG = "JPG"
    PNG = "PNG"
    MARKDOWN = "MARKDOWN"
    OTHER = "OTHER"

class DocumentStatus(str, Enum):
    """Document processing status."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"

class SentimentAnalysis(BaseModel):
    polarity: float
    subjectivity: float
    sentiment: str

class Document(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    file_type: DocumentType
    size: int
    created_at: datetime
    modified_at: datetime
    path: str
    content: Optional[str] = None
    sentiment: Optional[SentimentAnalysis] = None
    metadata: Dict = Field(default_factory=dict)

class DocumentCreate(Document):
    pass

class Document(Document):
    status: DocumentStatus = DocumentStatus.COMPLETED

    class Config:
        from_attributes = True

class FolderAnalysis(BaseModel):
    total_documents: int
    total_size: int
    document_types: Dict[str, int]
    average_file_size: float
    last_modified: datetime
    documents: List[Document] 