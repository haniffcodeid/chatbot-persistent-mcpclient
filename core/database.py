import asyncpg
from typing import Optional
from config.settings import get_settings

settings = get_settings()


class Database:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """Create database connection pool"""
        self.pool = await asyncpg.create_pool(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database=settings.POSTGRES_DB,
            min_size=settings.DB_MIN_POOL_SIZE,
            max_size=settings.DB_MAX_POOL_SIZE
        )
    
    async def disconnect(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
    
    def get_pool(self) -> asyncpg.Pool:
        """Get the database pool"""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        return self.pool


class VectorDatabase:
    """Separate database connection for vector store (optional)"""
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """Create vector database connection pool"""
        # Use separate vector DB config if provided, otherwise use main DB
        host = settings.VECTOR_DB_HOST or settings.POSTGRES_HOST
        port = settings.VECTOR_DB_PORT or settings.POSTGRES_PORT
        user = settings.VECTOR_DB_USER or settings.POSTGRES_USER
        password = settings.VECTOR_DB_PASSWORD or settings.POSTGRES_PASSWORD
        database = settings.VECTOR_DB_NAME or settings.POSTGRES_DB
        
        self.pool = await asyncpg.create_pool(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            min_size=settings.VECTOR_DB_MIN_POOL_SIZE,
            max_size=settings.VECTOR_DB_MAX_POOL_SIZE,
            statement_cache_size=0  # Disable prepared statements for pgbouncer compatibility
        )
    
    async def disconnect(self):
        """Close vector database connection pool"""
        if self.pool:
            await self.pool.close()
    
    def get_pool(self) -> asyncpg.Pool:
        """Get the vector database pool"""
        if not self.pool:
            raise RuntimeError("Vector database pool not initialized")
        return self.pool


# Global database instances
db = Database()
vector_db = VectorDatabase()


async def get_db_pool() -> asyncpg.Pool:
    """Dependency for getting database pool"""
    return db.get_pool()


async def get_vector_db_pool() -> asyncpg.Pool:
    """Dependency for getting vector database pool"""
    return vector_db.get_pool()