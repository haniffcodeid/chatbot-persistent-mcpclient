from fastapi import APIRouter, HTTPException, Depends
import asyncpg
from api.v1.schemas.user import UserCreate, UserResponse
from core.database import get_db_pool

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponse)
async def create_user(
    user: UserCreate,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Create a new user"""
    async with pool.acquire() as conn:
        try:
            row = await conn.fetchrow(
                "INSERT INTO users (username) VALUES ($1) RETURNING user_id, username, created_at",
                user.username
            )
            return UserResponse(
                user_id=row['user_id'],
                username=row['username'],
                created_at=row['created_at']
            )
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=400, detail="Username already exists")


@router.get("/{user_id}")
async def get_user(
    user_id: int,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Get user by ID"""
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT user_id, username, created_at FROM users WHERE user_id = $1",
            user_id
        )
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        
        return dict(row)