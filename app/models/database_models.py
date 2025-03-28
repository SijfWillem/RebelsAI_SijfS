from sqlalchemy import Column, String, Integer, DateTime, Float, JSON, ForeignKey, Enum as SQLEnum, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
from app.models.document import DocumentType, DocumentStatus

class DBDocument(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    file_type = Column(SQLEnum(DocumentType), nullable=False)
    size = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False)
    modified_at = Column(DateTime, nullable=False)
    path = Column(String, nullable=False)
    content = Column(String, nullable=True)
    sentiment_polarity = Column(Float, nullable=True)
    sentiment_subjectivity = Column(Float, nullable=True)
    sentiment_label = Column(String, nullable=True)
    metadata = Column(JSON, nullable=True)
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.COMPLETED)
    folder_id = Column(String, ForeignKey("folders.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    folder = relationship("DBFolder", back_populates="documents")
    classification = relationship("DBClassification", back_populates="document", uselist=False, cascade="all, delete-orphan")

    # Indexes and constraints
    __table_args__ = (
        UniqueConstraint('path', 'folder_id', name='uix_document_path_folder'),
        Index('ix_document_filename', 'filename'),
        Index('ix_document_file_type', 'file_type'),
        Index('ix_document_status', 'status'),
        Index('ix_document_modified_at', 'modified_at'),
    )

class DBFolder(Base):
    __tablename__ = "folders"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    path = Column(String, nullable=False)
    parent_id = Column(String, ForeignKey("folders.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    modified_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    parent = relationship("DBFolder", remote_side=[id], backref="subfolders")
    documents = relationship("DBDocument", back_populates="folder", cascade="all, delete-orphan")

    # Indexes and constraints
    __table_args__ = (
        UniqueConstraint('path', name='uix_folder_path'),
        Index('ix_folder_name', 'name'),
        Index('ix_folder_parent_id', 'parent_id'),
    )

class DBClassification(Base):
    __tablename__ = "classifications"

    id = Column(String, primary_key=True)
    document_id = Column(String, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    category = Column(String, nullable=False)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    document = relationship("DBDocument", back_populates="classification")

    # Indexes and constraints
    __table_args__ = (
        UniqueConstraint('document_id', name='uix_classification_document'),
        Index('ix_classification_category', 'category'),
    ) 