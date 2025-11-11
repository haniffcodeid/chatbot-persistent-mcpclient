from fastapi import APIRouter, HTTPException, Depends
import asyncpg
from api.v1.schemas.session import SessionCreate, SessionResponse
from core.database import get_db_pool

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/", response_model=SessionResponse)
async def create_session(
    session: SessionCreate,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Create a new chat session for a user"""
    async with pool.acquire() as conn:
        # Check if user exists
        user_exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM users WHERE user_id = $1)",
            session.user_id
        )
        
        if not user_exists:
            raise HTTPException(status_code=404, detail="User not found")
        
        row = await conn.fetchrow(
            "INSERT INTO sessions (user_id, start_time) VALUES ($1, CURRENT_TIMESTAMP) RETURNING session_id, user_id, start_time",
            session.user_id
        )
        
        return SessionResponse(
            session_id=row['session_id'],
            user_id=row['user_id'],
            start_time=row['start_time']
        )


@router.get("/users/{user_id}")
async def get_user_sessions(
    user_id: int,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Get all sessions for a user"""
    async with pool.acquire() as conn:
        sessions = await conn.fetch(
            """
            SELECT session_id, user_id, start_time, end_time
            FROM sessions
            WHERE user_id = $1
            ORDER BY start_time DESC
            """,
            user_id
        )
        return [dict(session) for session in sessions]


@router.get("/{session_id}/messages")
async def get_session_messages(
    session_id: int,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Get all messages for a session"""
    async with pool.acquire() as conn:
        # Check if session exists
        session_exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM sessions WHERE session_id = $1)",
            session_id
        )
        
        if not session_exists:
            raise HTTPException(status_code=404, detail="Session not found")
        
        messages = await conn.fetch(
            """
            SELECT message_id, session_id, sender, message_text, created_at
            FROM messages
            WHERE session_id = $1
            ORDER BY created_at ASC
            """,
            session_id
        )
        return [dict(message) for message in messages]