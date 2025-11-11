from fastapi import APIRouter, Depends
import asyncpg
from langchain_core.messages import HumanMessage, AIMessage  # Updated import
from api.v1.schemas.message import MessageRequest, AIResponse
from core.database import get_db_pool
from services.agent_service import get_agent_service, AgentService

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("/", response_model=AIResponse)
async def send_message(
    request: MessageRequest,
    pool: asyncpg.Pool = Depends(get_db_pool),
    agent: AgentService = Depends(get_agent_service)
):
    """Send a message and get AI response"""
    async with pool.acquire() as conn:
        # Start a transaction
        async with conn.transaction():
            session_id = request.session_id
            if session_id is None:
                # Create a new session if one is not provided
                session_id = await conn.fetchval(
                    "INSERT INTO sessions (user_id, start_time) VALUES ($1, CURRENT_TIMESTAMP) RETURNING session_id",
                    request.user_id
                )

            # Fetch recent messages for context
            recent_messages = await conn.fetch(
                """
                SELECT sender, message_text FROM messages
                WHERE session_id = $1
                ORDER BY created_at DESC
                LIMIT 10
                """,
                session_id
            )

            # Build chat history for the agent
            chat_history = []
            
            # Add conversation history (in reverse order since we fetched DESC)
            for message in reversed(recent_messages):
                if message['sender'] == 'User':
                    chat_history.append(HumanMessage(content=message['message_text']))
                elif message['sender'] == 'AI':
                    chat_history.append(AIMessage(content=message['message_text']))

            # Get AI response using agent service
            ai_response = await agent.get_response(request.message, chat_history)

            # Log the conversation in the database
            await conn.execute(
                "INSERT INTO messages (session_id, sender, message_text) VALUES ($1, $2, $3)",
                session_id, "User", request.message
            )
            await conn.execute(
                "INSERT INTO messages (session_id, sender, message_text) VALUES ($1, $2, $3)",
                session_id, "AI", ai_response
            )

            # Return the AI's response along with the current session_id for continuity
            return AIResponse(ai_response=ai_response, session_id=session_id)