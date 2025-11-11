from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database-tabular
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DB_MIN_POOL_SIZE: int = 10
    DB_MAX_POOL_SIZE: int = 20
    
    MCP_SERVER_URL: str
    
    # llm
    GOOGLE_GEMINI_MODEL: str
    GOOGLE_API_KEY: str
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "FastAPI Chat"

    # Vector Store (Supabase or PostgreSQL with pgvector)
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_TABLE_NAME: str = "documents_rag"
    SUPABASE_QUERY_NAME: str = "match_documents_rag"

    # Vector Database (optional - uses same as chat DB if not specified)
    VECTOR_DB_HOST: str = ""
    VECTOR_DB_PORT: int = 5432
    VECTOR_DB_USER: str = ""
    VECTOR_DB_PASSWORD: str = ""
    VECTOR_DB_NAME: str = ""
    VECTOR_DB_MIN_POOL_SIZE: int = 10
    VECTOR_DB_MAX_POOL_SIZE: int = 20
    
    # Embeddings
    EMBEDDING_MODEL: str = "models/text-embedding-004"
    EMBEDDING_DIMENSION: int = 768

    # Document Processing
    DEFAULT_CHUNK_SIZE: int = 2000
    DEFAULT_CHUNK_OVERLAP: int = 200
    MAX_CHUNK_SIZE: int = 2000
    MIN_CHUNK_SIZE: int = 500
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()