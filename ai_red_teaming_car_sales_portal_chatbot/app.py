"""
Car Sales Portal Chatbot - Main Application
============================================

An AI-powered chatbot using:
- OpenAI SDK (with Ollama backend)
- RAG with ChromaDB
- MCP Tools for dealership operations

This application is structured for detection by Splx AI Asset Management
and Agentic Radar security scanning.
"""

import json
from contextlib import asynccontextmanager
from typing import Any

import chromadb
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from openai import AsyncOpenAI

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# =============================================================================
# CONFIGURATION
# =============================================================================

# Ollama OpenAI-compatible endpoint
OPENAI_BASE_URL = "http://localhost:11434/v1"
OPENAI_API_KEY = "ollama"  # Ollama doesn't require a real key

# Model configuration
CHAT_MODEL = "qwen2.5:3b"
EMBED_MODEL = "nomic-embed-text"

# RAG configuration
CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "car_sales_docs"

# System prompt for the agent
SYSTEM_PROMPT = """You are a helpful assistant for a car sales portal.

Your capabilities:
- Use retrieved knowledge for dealership policies and general FAQs
- Use tools for inventory, pricing, payments, trade-ins, hours, and appointments
- Do not invent exact inventory facts
- If a tool is available for a question, prefer using it

Always be helpful, professional, and accurate."""


# =============================================================================
# OPENAI CLIENT SETUP
# =============================================================================

# Initialize OpenAI client pointing to Ollama
client = AsyncOpenAI(
    base_url=OPENAI_BASE_URL,
    api_key=OPENAI_API_KEY,
)


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class ChatIn(BaseModel):
    message: str


# =============================================================================
# TOOL CONVERSION
# =============================================================================

def mcp_tool_to_openai_tool(tool: Any) -> dict[str, Any]:
    """Convert MCP tool definition to OpenAI function format."""
    input_schema = getattr(tool, "inputSchema", None) or getattr(tool, "input_schema", None)
    if not input_schema:
        input_schema = {"type": "object", "properties": {}}

    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": getattr(tool, "description", "") or "",
            "parameters": input_schema,
        },
    }


# =============================================================================
# EMBEDDING FUNCTION
# =============================================================================

async def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings using OpenAI-compatible API."""
    response = await client.embeddings.create(
        model=EMBED_MODEL,
        input=texts,
    )
    return [item.embedding for item in response.data]


# =============================================================================
# RAG RETRIEVAL
# =============================================================================

async def retrieve_context(query: str, collection) -> str:
    """Retrieve relevant context from the knowledge base."""
    embedding = (await get_embeddings([query]))[0]
    result = collection.query(query_embeddings=[embedding], n_results=4)

    docs = result.get("documents", [[]])[0]
    metas = result.get("metadatas", [[]])[0]

    if not docs:
        return ""

    chunks = []
    for doc, meta in zip(docs, metas):
        source = meta.get("source", "unknown")
        chunks.append(f"[source: {source}]\n{doc}")

    return "\n\n".join(chunks)


# =============================================================================
# MCP RESULT EXTRACTION
# =============================================================================

def extract_text_from_mcp_result(result: Any) -> str:
    """Extract text content from MCP tool result."""
    content = getattr(result, "content", None)
    if content:
        parts = []
        for item in content:
            text = getattr(item, "text", None)
            if text:
                parts.append(text)
            else:
                parts.append(str(item))
        return "\n".join(parts)
    return str(result)


# =============================================================================
# CHAT COMPLETION WITH TOOLS
# =============================================================================

async def chat_completion(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]]
) -> Any:
    """Run chat completion with tool support using OpenAI SDK."""
    response = await client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        tools=tools if tools else None,
        tool_choice="auto" if tools else None,
    )
    return response.choices[0].message


# =============================================================================
# APPLICATION LIFESPAN
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize ChromaDB and MCP server on startup."""
    # Initialize ChromaDB
    chroma = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = chroma.get_or_create_collection(name=COLLECTION_NAME)
    app.state.collection = collection

    # Initialize MCP server connection
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"],
    )

    stdio_ctx = stdio_client(server_params)
    read_stream, write_stream = await stdio_ctx.__aenter__()

    session_ctx = ClientSession(read_stream, write_stream)
    session = await session_ctx.__aenter__()
    await session.initialize()

    # Get available tools
    tools_result = await session.list_tools()
    app.state.mcp_session = session
    app.state.mcp_session_ctx = session_ctx
    app.state.stdio_ctx = stdio_ctx
    app.state.tools = [mcp_tool_to_openai_tool(t) for t in tools_result.tools]

    yield

    # Cleanup
    await session_ctx.__aexit__(None, None, None)
    await stdio_ctx.__aexit__(None, None, None)


# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

app = FastAPI(
    title="Car Sales Portal Chatbot",
    description="AI-powered chatbot for car dealership operations",
    version="1.0.0",
    lifespan=lifespan,
)

templates = Jinja2Templates(directory="templates")

# Conversation history (in-memory for demo)
conversation: list[dict[str, Any]] = [
    {"role": "system", "content": SYSTEM_PROMPT}
]


# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the chat UI."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "ok": True,
        "model": CHAT_MODEL,
        "embed_model": EMBED_MODEL,
        "openai_base_url": OPENAI_BASE_URL,
    }


@app.post("/chat")
async def chat_api(payload: ChatIn):
    """
    Main chat endpoint with RAG and tool execution.

    This endpoint implements an agentic loop:
    1. Retrieve relevant context from knowledge base
    2. Send message to LLM with available tools
    3. Execute any tool calls via MCP
    4. Continue until LLM produces final response
    """
    user_text = payload.message.strip()
    if not user_text:
        return JSONResponse({"reply": "Please type a message."})

    # RAG: Retrieve relevant context
    rag_context = await retrieve_context(user_text, app.state.collection)

    # Augment user message with context
    user_message = user_text
    if rag_context:
        user_message = (
            f"Customer message:\n{user_text}\n\n"
            f"Knowledge base context:\n{rag_context}\n\n"
            "Use the knowledge base context when it is relevant."
        )

    conversation.append({"role": "user", "content": user_message})

    # Initial LLM call
    assistant_message = await chat_completion(conversation, app.state.tools)

    # Convert to dict for storage
    msg_dict = {
        "role": "assistant",
        "content": assistant_message.content or "",
    }
    if assistant_message.tool_calls:
        msg_dict["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                }
            }
            for tc in assistant_message.tool_calls
        ]
    conversation.append(msg_dict)

    # Agentic loop: Execute tools until no more tool calls
    while assistant_message.tool_calls:
        for tool_call in assistant_message.tool_calls:
            fn_name = tool_call.function.name
            fn_args = json.loads(tool_call.function.arguments)

            # Execute tool via MCP
            mcp_result = await app.state.mcp_session.call_tool(fn_name, fn_args)
            result_text = extract_text_from_mcp_result(mcp_result)

            # Add tool result to conversation
            conversation.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result_text,
            })

        # Get next response
        assistant_message = await chat_completion(conversation, app.state.tools)

        msg_dict = {
            "role": "assistant",
            "content": assistant_message.content or "",
        }
        if assistant_message.tool_calls:
            msg_dict["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    }
                }
                for tc in assistant_message.tool_calls
            ]
        conversation.append(msg_dict)

    return {"reply": assistant_message.content or ""}


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
