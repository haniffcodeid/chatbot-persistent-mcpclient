from pydantic import BaseModel
from typing import Optional, List


class DocumentUploadResponse(BaseModel):
    filename: str
    chunks: int
    status: str
    error: Optional[str] = None


class DocumentProcessResponse(BaseModel):
    total_files: int
    successful: int
    failed: int
    results: List[DocumentUploadResponse]
    total_chunks_added: int


class RAGQueryRequest(BaseModel):
    question: str
    user_id: Optional[int] = None


class RAGQueryResponse(BaseModel):
    question: str
    answer: str


class DocumentStatsResponse(BaseModel):
    total_documents: int
    user_documents: Optional[int] = None