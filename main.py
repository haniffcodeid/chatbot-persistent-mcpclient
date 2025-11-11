from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config.settings import get_settings
from core.database import db, vector_db
from services.agent_service import agent_service
from services.vector_store_service import vector_store_service
from api.v1.endpoints import users, sessions, messages, documents

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown"""
    # Startup
    await db.connect()  # Chat database
    await vector_db.connect()  # Vector database (can be same or different)
    await agent_service.initialize()
    
    # Initialize vector store service with vector database pool
    await vector_store_service.initialize(vector_db.get_pool())
    
    # Initialize RAG service
    # await initialize_rag_service(vector_store_service)
    
    yield
    
    # Shutdown
    await db.disconnect()
    await vector_db.disconnect()


app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan
)

origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # <- or use ["*"] for all (not safe for production)
    allow_credentials=True,
    allow_methods=["*"],              # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],              # Allow all headers
)


app.include_router(users.router, prefix=settings.API_V1_PREFIX)
app.include_router(sessions.router, prefix=settings.API_V1_PREFIX)
app.include_router(messages.router, prefix=settings.API_V1_PREFIX)
app.include_router(documents.router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "FastAPI Chat API is running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected" if db.pool else "disconnected",
        "agent": "initialized" if agent_service.agent_executor else "not initialized"
    }