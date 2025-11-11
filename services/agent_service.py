import os
from typing import List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from config.settings import get_settings
import os
from dotenv import load_dotenv

TOKEN = os.getenv('BEARER_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

settings = get_settings()
if settings.GOOGLE_API_KEY:
    os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY

SYSTEM_PROMPT = """
You are a helpful assistant for an AI Retail Platform website.
Your role is to use the available tools to answer questions and perform operations related to users, products, merchants, promotions, orders, etc.

When answering a question, follow these guidelines:
- Be concise and clear in your responses.
- When you return data, format it nicely.
- If a tool call fails, explain the error to the user in a helpful way.
- Always check for a user's purchase history before suggesting a new purchase.
- Display JSON as tables if the JSON contains more than one record.
"""


class AgentService:
    def __init__(self):
        self.agent_executor = None
        self.system_message = SystemMessage(content=SYSTEM_PROMPT)
    
    async def initialize(self):
        """Initialize the agent with MCP client and tools"""
        tools = []
        
        # Only try to connect if MCP_SERVER_URL is provided
        if settings.MCP_SERVER_URL:
            try:
                mcp_client = MultiServerMCPClient(
                    {
                        "retailmcp": {
                            "url": "https://airetail-mcp.codeoffice.net/mcp",
                            "transport": "streamable_http",
                            "headers": {
                                "Authorization": f"Bearer {TOKEN}"
                            }
                        }
                    }
                )
                
                # Fetch tools from MCP client
                tools = await mcp_client.get_tools()
                print(f"Successfully loaded {len(tools)} tools from MCP server")
            except Exception as e:
                print(f"Warning: Could not connect to MCP server: {e}")
                print("Agent will initialize without MCP tools")
        else:
            print("No MCP_SERVER_URL configured, agent will run without MCP tools")
        
        # Initialize chat model
        llm = ChatGroq(
            model="openai/gpt-oss-20b",
            temperature=0.1,
            api_key=GROQ_API_KEY,
        )
        
        # Create agent using langgraph (no state_modifier parameter)
        self.agent_executor = create_react_agent(
            model=llm,
            tools=tools
        )
    
    async def get_response(self, user_input: str, chat_history: List) -> str:
        """Get response from the agent with chat history"""
        if not self.agent_executor:
            raise RuntimeError("Agent not initialized")
        
        try:
            # Build messages list with system message first
            messages = [self.system_message]
            
            # Add chat history
            for msg in chat_history:
                if isinstance(msg, (HumanMessage, AIMessage)):
                    messages.append(msg)
            
            # Add current user input
            messages.append(HumanMessage(content=user_input))
            
            # Invoke agent
            result = await self.agent_executor.ainvoke({"messages": messages})
            
            # Extract response from result
            if "messages" in result and len(result["messages"]) > 0:
                # Get the last AI message
                for msg in reversed(result["messages"]):
                    if isinstance(msg, AIMessage):
                        return msg.content
            
            return "I apologize, but I couldn't generate a response."
            
        except Exception as e:
            print(f"Agent error: {e}")
            return f"I encountered an error: {str(e)}"


agent_service = AgentService()

async def get_agent_service() -> AgentService:
    """Dependency for getting agent service"""
    return agent_service