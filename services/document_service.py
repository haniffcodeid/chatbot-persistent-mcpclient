import fitz  # PyMuPDF
import tempfile
import os
from uuid import uuid4
from datetime import datetime
from typing import List, BinaryIO
# from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from config.settings import get_settings

settings = get_settings()


class DocumentService:
    """Handle document extraction, chunking, and metadata creation"""
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or settings.DEFAULT_CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.DEFAULT_CHUNK_OVERLAP
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            add_start_index=True,
            separators=["\n\n", "\n", ".", " ", ""],
        )
    
    def extract_text_from_pdf(self, pdf_content: bytes) -> str:
        """Extract text from PDF bytes"""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(pdf_content)
            tmp_file_path = tmp_file.name
        
        try:
            doc = fitz.open(tmp_file_path)
            text = "\n".join([page.get_text() for page in doc])
            doc.close()
            return text
        finally:
            os.unlink(tmp_file_path)
    
    def extract_text_from_txt(self, txt_content: bytes) -> str:
        """Extract text from TXT bytes"""
        return txt_content.decode('utf-8')
    
    def extract_text(self, file_content: bytes, content_type: str) -> tuple[str, str]:
        """Extract text from file based on content type"""
        if content_type == "application/pdf":
            return self.extract_text_from_pdf(file_content), "application/pdf"
        elif content_type in ["text/plain", "text/txt"]:
            return self.extract_text_from_txt(file_content), "text/plain"
        else:
            raise ValueError(f"Unsupported file type: {content_type}")
    
    def chunk_text(self, text: str) -> List[str]:
        """Split text into chunks"""
        return self.text_splitter.split_text(text)
    
    def create_documents(self, chunks: List[str], filename: str, file_type: str, user_id: int = None) -> List[Document]:
        """Create Document objects with metadata"""
        documents = []
        file_id = str(uuid4())
        total_chunks = len(chunks)
        
        for idx, chunk in enumerate(chunks):
            lines_from = idx * (self.chunk_size // 50)
            lines_to = lines_from + (len(chunk) // 50)
            
            metadata = {
                "source": filename,
                "file_type": file_type,
                "file_id": file_id,
                "chunk_index": idx,
                "total_chunks": total_chunks,
                "chunk_size": len(chunk),
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "loc": {
                    "lines": {
                        "from": lines_from,
                        "to": lines_to
                    }
                }
            }
            
            documents.append(Document(page_content=chunk, metadata=metadata))
        
        return documents
    
    def process_file(self, file_content: bytes, filename: str, content_type: str, user_id: int = None) -> tuple[List[Document], int]:
        """Process a single file and return documents and chunk count"""
        text, file_type = self.extract_text(file_content, content_type)
        
        if not text.strip():
            raise ValueError(f"No text extracted from {filename}")
        
        chunks = self.chunk_text(text)
        documents = self.create_documents(chunks, filename, file_type, user_id)
        
        return documents, len(chunks)


# Global document service instance
document_service = DocumentService()


def get_document_service() -> DocumentService:
    """Dependency for getting document service"""
    return document_service