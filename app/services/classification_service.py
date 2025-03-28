import os
from typing import Dict, List, Optional
import asyncio
from pathlib import Path
import spacy
import asent
from openai import AsyncOpenAI
from functools import lru_cache
import time
from app.models.document import Document, DocumentType, DocumentStatus
import uuid
from datetime import datetime

class ClassificationService:
    def __init__(self, use_openai: bool = False):
        self.use_openai = use_openai
        if use_openai:
            self.client = AsyncOpenAI()
        else:
            # Load the English language model
            self.nlp = spacy.load("en_core_web_sm")
            # Add sentiment analysis pipeline
            self.nlp.add_pipe("asent_en_v1")

    @lru_cache(maxsize=1000)
    def _determine_document_type(self, content: str) -> str:
        """Determine document type based on content with caching."""
        content_lower = content.lower()
        
        # Define keywords for different document types
        type_keywords = {
            "Contract": ["agreement", "contract", "terms", "conditions", "signature"],
            "Report": ["report", "summary", "conclusion", "findings", "analysis"],
            "Email": ["dear", "regards", "sincerely", "best regards", "email"],
            "Memo": ["memo", "memorandum", "internal", "confidential"],
            "Proposal": ["proposal", "offer", "quote", "pricing", "estimate"],
            "Invoice": ["invoice", "bill", "payment", "amount due", "total"],
            "Resume": ["resume", "cv", "experience", "education", "skills"],
            "Presentation": ["slide", "presentation", "agenda", "overview"],
            "Manual": ["manual", "guide", "instructions", "how to", "steps"],
            "Policy": ["policy", "procedure", "guidelines", "rules", "compliance"]
        }
        
        # Check for keywords and return the most likely type
        max_matches = 0
        best_type = "Other"
        
        for doc_type, keywords in type_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in content_lower)
            if matches > max_matches:
                max_matches = matches
                best_type = doc_type
        
        return best_type

    @lru_cache(maxsize=1000)
    async def analyze_document(self, document: Document) -> Dict:
        """Analyze a text document using spaCy and sentiment analysis."""
        try:
            # Read file content
            with open(document.path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Process with spaCy
            doc = self.nlp(content)
            
            # Get sentiment analysis
            sentiment = doc._.sentiment
            
            # Determine document type based on content
            doc_type = self._determine_document_type(content)
            
            return {
                "classification": {
                    "type": doc_type,
                    "sentiment": sentiment,
                    "confidence": 0.8
                },
                "method": "spaCy",
                "sentiment_score": sentiment,
                "subjectivity": 0.5  # Default value
            }
        except Exception as e:
            print(f"Error analyzing document {document.filename}: {str(e)}")
            return self._create_default_analysis(document)

    def _create_default_analysis(self, document: Document) -> Dict:
        """Create a default analysis for non-text documents or analysis failures."""
        return {
            "classification": {
                "type": str(document.file_type.value),
                "sentiment": "Neutral",
                "confidence": 0.5
            },
            "method": "default",
            "sentiment_score": 0,
            "subjectivity": 0.5
        }

    async def process_documents_batch(self, documents: List[Document]) -> List[Dict]:
        """Process a batch of documents concurrently."""
        tasks = []
        for doc in documents:
            if doc.file_type == DocumentType.TXT:
                # Create a coroutine for text documents
                tasks.append(self.analyze_document(doc))
            else:
                # For non-text documents, create a coroutine that returns the default analysis
                tasks.append(asyncio.create_task(asyncio.sleep(0, result=self._create_default_analysis(doc))))
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks)
        return results

    async def analyze_folder(self, folder_path: str) -> Dict:
        """Analyze all documents in a folder and return aggregated statistics."""
        folder = Path(folder_path)
        if not folder.exists():
            return {"error": "Folder not found"}

        documents = []
        total_size = 0
        sentiment_scores = []
        document_types = {}

        # Process all files in the folder and its subfolders
        for file_path in folder.rglob("*"):
            if file_path.is_file():
                try:
                    # Get file size
                    size = file_path.stat().st_size
                    total_size += size

                    # Create a Document object
                    doc = Document(
                        id=str(uuid.uuid4()),
                        filename=file_path.name,
                        file_type=self._get_file_type(str(file_path)),
                        size=size,
                        created_at=datetime.fromtimestamp(file_path.stat().st_ctime),
                        modified_at=datetime.fromtimestamp(file_path.stat().st_mtime),
                        path=str(file_path.relative_to(folder)),
                        metadata={},
                        classification=None,
                        status=DocumentStatus.COMPLETED
                    )

                    # Analyze document if it's a text file
                    if doc.file_type == DocumentType.TXT:
                        analysis = await self.analyze_document(doc)
                        doc.classification = analysis["classification"]
                        doc.metadata.update({
                            "classification_method": analysis["method"],
                            "confidence": analysis["classification"]["confidence"],
                            "sentiment_score": analysis["sentiment_score"],
                            "subjectivity": analysis["subjectivity"]
                        })
                    else:
                        # For non-text files, create a default analysis
                        analysis = self._create_default_analysis(doc)
                        doc.classification = analysis["classification"]
                        doc.metadata.update({
                            "classification_method": "default",
                            "confidence": 0.5,
                            "sentiment_score": 0,
                            "subjectivity": 0.5
                        })

                    documents.append(doc)

                    # Update statistics
                    sentiment_scores.append(doc.metadata.get("sentiment_score", 0))
                    doc_type = doc.classification["type"]
                    document_types[doc_type] = document_types.get(doc_type, 0) + 1

                except Exception as e:
                    print(f"Error processing {file_path}: {str(e)}")

        # Calculate statistics
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        sentiment_distribution = {
            "Positive": sum(1 for s in sentiment_scores if s > 0.2),
            "Neutral": sum(1 for s in sentiment_scores if -0.2 <= s <= 0.2),
            "Negative": sum(1 for s in sentiment_scores if s < -0.2)
        }

        return {
            "total_documents": len(documents),
            "total_size": total_size,
            "average_sentiment": avg_sentiment,
            "sentiment_distribution": sentiment_distribution,
            "document_types": document_types,
            "documents": [doc.dict() for doc in documents]
        }

    async def analyze_document_with_openai(self, file_path: str) -> Dict:
        """Analyze a document using OpenAI's API."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Truncate content if too long
            max_tokens = 4000
            if len(content) > max_tokens:
                content = content[:max_tokens] + "..."

            prompt = f"""Analyze the following document and provide:
            1. Document type (Contract, Report, Email, Invoice, Proposal, Meeting, Policy, or Other)
            2. Sentiment (Positive, Negative, or Neutral)
            3. Sentiment score (-1 to 1)
            4. Subjectivity score (0 to 1)

            Document content:
            {content}

            Provide the response in JSON format with keys: type, sentiment, sentiment_score, subjectivity"""

            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )

            # Parse the response
            result = eval(response.choices[0].message.content)
            return result

        except Exception as e:
            print(f"Error analyzing document with OpenAI: {str(e)}")
            return {
                "type": "Unknown",
                "sentiment": "Neutral",
                "sentiment_score": 0.0,
                "subjectivity": 0.0
            } 