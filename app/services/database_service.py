from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_
from sqlalchemy.exc import IntegrityError
from app.models.database_models import DBDocument, DBFolder, DBClassification
from app.models.document import Document, DocumentType, DocumentStatus
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_document(self, document: Document, folder_id: str = None) -> DBDocument:
        """Create a new document in the database."""
        try:
            # Check for existing document with same path in the same folder
            existing_doc = await self.session.execute(
                select(DBDocument).where(
                    and_(
                        DBDocument.path == document.path,
                        DBDocument.folder_id == folder_id
                    )
                )
            )
            existing_doc = existing_doc.scalar_one_or_none()

            if existing_doc:
                # Update existing document if it exists
                logger.info(f"Document already exists, updating: {document.path}")
                return await self.update_document(
                    existing_doc.id,
                    size=document.size,
                    modified_at=document.modified_at,
                    content=document.content,
                    sentiment_polarity=document.sentiment.polarity if document.sentiment else None,
                    sentiment_subjectivity=document.sentiment.subjectivity if document.sentiment else None,
                    sentiment_label=document.sentiment.sentiment if document.sentiment else None,
                    metadata=document.metadata,
                    status=document.status
                )

            # Create new document
            db_document = DBDocument(
                id=document.id,
                filename=document.filename,
                file_type=document.file_type,
                size=document.size,
                created_at=document.created_at,
                modified_at=document.modified_at,
                path=document.path,
                content=document.content,
                sentiment_polarity=document.sentiment.polarity if document.sentiment else None,
                sentiment_subjectivity=document.sentiment.subjectivity if document.sentiment else None,
                sentiment_label=document.sentiment.sentiment if document.sentiment else None,
                metadata=document.metadata,
                status=document.status,
                folder_id=folder_id
            )
            self.session.add(db_document)
            await self.session.commit()
            await self.session.refresh(db_document)
            return db_document

        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Integrity error creating document: {str(e)}")
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating document: {str(e)}")
            raise

    async def create_folder(self, name: str, path: str, parent_id: str = None) -> DBFolder:
        """Create a new folder in the database."""
        try:
            # Check for existing folder with same path
            existing_folder = await self.session.execute(
                select(DBFolder).where(DBFolder.path == path)
            )
            existing_folder = existing_folder.scalar_one_or_none()

            if existing_folder:
                # Update existing folder if it exists
                logger.info(f"Folder already exists, updating: {path}")
                return await self.update_folder(
                    existing_folder.id,
                    name=name,
                    parent_id=parent_id
                )

            # Create new folder
            folder_id = str(uuid.uuid4())
            db_folder = DBFolder(
                id=folder_id,
                name=name,
                path=path,
                parent_id=parent_id
            )
            self.session.add(db_folder)
            await self.session.commit()
            await self.session.refresh(db_folder)
            return db_folder

        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Integrity error creating folder: {str(e)}")
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating folder: {str(e)}")
            raise

    async def create_classification(self, document_id: str, category: str, confidence: float = None) -> DBClassification:
        """Create a new classification in the database."""
        try:
            # Check for existing classification
            existing_class = await self.session.execute(
                select(DBClassification).where(DBClassification.document_id == document_id)
            )
            existing_class = existing_class.scalar_one_or_none()

            if existing_class:
                # Update existing classification if it exists
                logger.info(f"Classification already exists, updating: {document_id}")
                return await self.update_classification(
                    existing_class.id,
                    category=category,
                    confidence=confidence
                )

            # Create new classification
            classification_id = str(uuid.uuid4())
            db_classification = DBClassification(
                id=classification_id,
                document_id=document_id,
                category=category,
                confidence=confidence
            )
            self.session.add(db_classification)
            await self.session.commit()
            await self.session.refresh(db_classification)
            return db_classification

        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Integrity error creating classification: {str(e)}")
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating classification: {str(e)}")
            raise

    async def update_folder(self, folder_id: str, **kwargs) -> DBFolder:
        """Update a folder's properties."""
        try:
            result = await self.session.execute(
                update(DBFolder)
                .where(DBFolder.id == folder_id)
                .values(**kwargs)
                .returning(DBFolder)
            )
            await self.session.commit()
            return result.scalar_one_or_none()
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Integrity error updating folder: {str(e)}")
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating folder: {str(e)}")
            raise

    async def update_classification(self, classification_id: str, **kwargs) -> DBClassification:
        """Update a classification's properties."""
        try:
            result = await self.session.execute(
                update(DBClassification)
                .where(DBClassification.id == classification_id)
                .values(**kwargs)
                .returning(DBClassification)
            )
            await self.session.commit()
            return result.scalar_one_or_none()
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Integrity error updating classification: {str(e)}")
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating classification: {str(e)}")
            raise

    async def delete_folder(self, folder_id: str) -> bool:
        """Delete a folder and all its contents."""
        try:
            # Delete all documents in the folder
            await self.session.execute(
                delete(DBDocument).where(DBDocument.folder_id == folder_id)
            )
            
            # Delete all subfolders recursively
            subfolders = await self.session.execute(
                select(DBFolder).where(DBFolder.parent_id == folder_id)
            )
            for subfolder in subfolders.scalars():
                await self.delete_folder(subfolder.id)
            
            # Delete the folder itself
            result = await self.session.execute(
                delete(DBFolder)
                .where(DBFolder.id == folder_id)
                .returning(DBFolder.id)
            )
            await self.session.commit()
            return bool(result.scalar_one_or_none())
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting folder: {str(e)}")
            raise

    async def get_document(self, document_id: str) -> DBDocument:
        """Get a document by ID."""
        result = await self.session.execute(
            select(DBDocument).where(DBDocument.id == document_id)
        )
        return result.scalar_one_or_none()

    async def get_folder(self, folder_id: str) -> DBFolder:
        """Get a folder by ID."""
        result = await self.session.execute(
            select(DBFolder).where(DBFolder.id == folder_id)
        )
        return result.scalar_one_or_none()

    async def get_folder_structure(self, folder_id: str) -> dict:
        """Get the complete folder structure starting from a specific folder."""
        folder = await self.get_folder(folder_id)
        if not folder:
            return None

        structure = {
            "id": folder.id,
            "name": folder.name,
            "path": folder.path,
            "files": [],
            "subfolders": []
        }

        # Get all documents in this folder
        documents = await self.session.execute(
            select(DBDocument).where(DBDocument.folder_id == folder_id)
        )
        for doc in documents.scalars():
            structure["files"].append({
                "id": doc.id,
                "name": doc.filename,
                "type": doc.file_type.value,
                "size": doc.size,
                "modified": doc.modified_at.isoformat()
            })

        # Get all subfolders
        subfolders = await self.session.execute(
            select(DBFolder).where(DBFolder.parent_id == folder_id)
        )
        for subfolder in subfolders.scalars():
            structure["subfolders"].append(
                await self.get_folder_structure(subfolder.id)
            )

        return structure

    async def update_document(self, document_id: str, **kwargs) -> DBDocument:
        """Update a document's properties."""
        result = await self.session.execute(
            update(DBDocument)
            .where(DBDocument.id == document_id)
            .values(**kwargs)
            .returning(DBDocument)
        )
        await self.session.commit()
        return result.scalar_one_or_none()

    async def delete_document(self, document_id: str) -> bool:
        """Delete a document by ID."""
        result = await self.session.execute(
            delete(DBDocument)
            .where(DBDocument.id == document_id)
            .returning(DBDocument.id)
        )
        await self.session.commit()
        return bool(result.scalar_one_or_none())

    async def get_all_documents(self, folder_id: str = None) -> list[DBDocument]:
        """Get all documents, optionally filtered by folder."""
        query = select(DBDocument)
        if folder_id:
            query = query.where(DBDocument.folder_id == folder_id)
        result = await self.session.execute(query)
        return result.scalars().all() 