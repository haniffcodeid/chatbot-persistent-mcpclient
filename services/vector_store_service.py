from typing import List, Optional
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import asyncpg
import json
from config.settings import get_settings

settings = get_settings()


class VectorStoreService:
    """Manage PostgreSQL vector store operations with pgvector"""
    
    def __init__(self):
        self.embeddings = GoogleGenerativeAIEmbeddings(model=settings.EMBEDDING_MODEL)
        self.table_name = settings.SUPABASE_TABLE_NAME
        self.initialized = False
    
    async def initialize(self, pool: asyncpg.Pool):
        """Initialize the vector store service"""
        self.pool = pool
        self.initialized = True
    
    async def add_documents(self, documents: List[Document]) -> bool:
        """Add documents to PostgreSQL vector store"""
        if not documents:
            return False
        
        texts = [doc.page_content for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        embeddings_list = self.embeddings.embed_documents(texts)
        
        async with self.pool.acquire() as conn:
            # Use a transaction for batch insert
            async with conn.transaction():
                # Insert one by one to avoid prepared statement issues with pgbouncer
                for text, metadata, embedding in zip(texts, metadatas, embeddings_list):
                    # Convert embedding list to PostgreSQL vector format string
                    embedding_str = '[' + ','.join(map(str, embedding)) + ']'
                    
                    await conn.execute(
                        f"INSERT INTO {self.table_name} (content, metadata, embedding) VALUES ($1, $2::jsonb, $3::vector)",
                        text,
                        json.dumps(metadata),
                        embedding_str
                    )
        
        return True
    
    async def similarity_search(self, query: str, k: int = 4, filter_metadata: dict = None) -> List[Document]:
        """Perform similarity search using the match function"""
        if not self.initialized:
            return []
        
        # Generate query embedding
        query_embedding = self.embeddings.embed_query(query)
        
        async with self.pool.acquire() as conn:
            # Call the match_documents_rag function
            filter_json = filter_metadata if filter_metadata else {}
            
            rows = await conn.fetch(
                f"SELECT * FROM {settings.SUPABASE_QUERY_NAME}($1::vector, $2, $3::jsonb)",
                query_embedding,
                k,
                filter_json
            )
            
            # Convert to Document objects
            documents = []
            for row in rows:
                doc = Document(
                    page_content=row['content'],
                    metadata=row['metadata']
                )
                documents.append(doc)
            
            return documents
    
    async def clear_all_documents(self, user_id: Optional[int] = None) -> bool:
        """Clear documents from PostgreSQL (optionally filter by user_id)"""
        try:
            async with self.pool.acquire() as conn:
                if user_id:
                    # Delete only user's documents
                    await conn.execute(
                        f"DELETE FROM {self.table_name} WHERE metadata->>'user_id' = $1",
                        str(user_id)
                    )
                else:
                    # Delete all documents
                    await conn.execute(f"DELETE FROM {self.table_name}")
            
            return True
            
        except Exception as e:
            raise Exception(f"Error clearing documents: {str(e)}")
    
    async def get_document_count(self, user_id: Optional[int] = None) -> int:
        """Get total document count in vector store"""
        try:
            async with self.pool.acquire() as conn:
                if user_id:
                    count = await conn.fetchval(
                        f"SELECT COUNT(*) FROM {self.table_name} WHERE metadata->>'user_id' = $1",
                        str(user_id)
                    )
                else:
                    count = await conn.fetchval(f"SELECT COUNT(*) FROM {self.table_name}")
                
                return count or 0
            
        except Exception as e:
            print(f"Warning: Could not get document count: {str(e)}")
            return 0


# Global vector store service instance
vector_store_service = VectorStoreService()


async def get_vector_store_service() -> VectorStoreService:
    """Dependency for getting vector store service"""
    return vector_store_service