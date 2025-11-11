from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from typing import List, Optional
from api.v1.schemas.document import (
    DocumentUploadResponse, 
    DocumentProcessResponse,
    RAGQueryRequest,
    RAGQueryResponse,
    DocumentStatsResponse
)
from services.document_service import get_document_service, DocumentService
from services.vector_store_service import get_vector_store_service, VectorStoreService
# from services.rag_service import get_rag_service, RAGService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentProcessResponse)
async def upload_documents(
    files: List[UploadFile] = File(...),
    user_id: Optional[int] = Query(None, description="User ID to associate documents with"),
    chunk_size: Optional[int] = Query(None, description="Custom chunk size"),
    chunk_overlap: Optional[int] = Query(None, description="Custom chunk overlap"),
    doc_service: DocumentService = Depends(get_document_service),
    vector_service: VectorStoreService = Depends(get_vector_store_service)
):
    """
    Upload and process documents (PDF or TXT files)
    
    - **files**: List of files to upload
    - **user_id**: Optional user ID to associate documents with
    - **chunk_size**: Optional custom chunk size
    - **chunk_overlap**: Optional custom chunk overlap
    """
    # Initialize document service with custom settings if provided
    if chunk_size or chunk_overlap:
        doc_service = DocumentService(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    
    all_documents = []
    results = []
    successful = 0
    failed = 0
    
    for file in files:
        try:
            # Validate file type
            if file.content_type not in ["application/pdf", "text/plain"]:
                results.append(DocumentUploadResponse(
                    filename=file.filename,
                    chunks=0,
                    status="error",
                    error=f"Unsupported file type: {file.content_type}"
                ))
                failed += 1
                continue
            
            # Read file content
            content = await file.read()
            
            # Process file
            documents, chunk_count = doc_service.process_file(
                content, 
                file.filename, 
                file.content_type,
                user_id
            )
            
            all_documents.extend(documents)
            results.append(DocumentUploadResponse(
                filename=file.filename,
                chunks=chunk_count,
                status="success"
            ))
            successful += 1
            
        except Exception as e:
            results.append(DocumentUploadResponse(
                filename=file.filename,
                chunks=0,
                status="error",
                error=str(e)
            ))
            failed += 1
    
    # Add documents to vector store
    total_chunks_added = 0
    if all_documents:
        try:
            await vector_service.add_documents(all_documents)
            total_chunks_added = len(all_documents)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to add documents to vector store: {str(e)}"
            )
    
    return DocumentProcessResponse(
        total_files=len(files),
        successful=successful,
        failed=failed,
        results=results,
        total_chunks_added=total_chunks_added
    )


# @router.post("/query", response_model=RAGQueryResponse)
# async def query_documents(
#     request: RAGQueryRequest,
#     rag_service: RAGService = Depends(get_rag_service)
# ):
#     """
#     Query the document knowledge base using RAG
    
#     - **question**: The question to ask
#     - **user_id**: Optional user ID to filter documents
#     """
#     try:
#         answer = await rag_service.query(request.question, request.user_id)
#         return RAGQueryResponse(
#             question=request.question,
#             answer=answer
#         )
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Error processing query: {str(e)}"
#         )


@router.get("/stats", response_model=DocumentStatsResponse)
async def get_document_stats(
    user_id: Optional[int] = Query(None, description="User ID to filter stats"),
    vector_service: VectorStoreService = Depends(get_vector_store_service)
):
    """
    Get document statistics
    
    - **user_id**: Optional user ID to get user-specific stats
    """
    try:
        total_documents = await vector_service.get_document_count()
        user_documents = None
        
        if user_id:
            user_documents = await vector_service.get_document_count(user_id)
        
        return DocumentStatsResponse(
            total_documents=total_documents,
            user_documents=user_documents
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting stats: {str(e)}"
        )


@router.delete("/clear")
async def clear_documents(
    user_id: Optional[int] = Query(None, description="User ID to clear documents for (if not provided, clears all)"),
    vector_service: VectorStoreService = Depends(get_vector_store_service)
):
    """
    Clear documents from the vector store
    
    - **user_id**: Optional user ID to clear only that user's documents
    """
    try:
        await vector_service.clear_all_documents(user_id)
        message = f"Cleared documents for user {user_id}" if user_id else "Cleared all documents"
        return {"message": message, "status": "success"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing documents: {str(e)}"
        )