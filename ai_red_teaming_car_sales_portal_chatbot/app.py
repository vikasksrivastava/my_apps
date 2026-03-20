"""
Car Sales Portal Chatbot - Main Application
============================================

An AI-powered chatbot using:
- OpenAI SDK (with Ollama backend)
- RAG with ChromaDB
- MCP Tools for dealership operations

This application is designed for AI Red Teaming research and security scanning.

Author: Vikas Srivastava
"""

import json
import asyncio
import sys
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

import chromadb
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
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


async def chat_completion_streaming(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]]
) -> AsyncGenerator[Any, None]:
    """Run streaming chat completion with tool support."""
    response = await client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        tools=tools if tools else None,
        tool_choice="auto" if tools else None,
        stream=True,
    )
    async for chunk in response:
        yield chunk


def format_sse(event: str, data: dict) -> str:
    """Format data as Server-Sent Event."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


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
        command=sys.executable,
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


@app.get("/api/tools")
async def get_tools():
    """Return list of available MCP tools with their schemas."""
    tools = []
    for tool in app.state.tools:
        tools.append({
            "name": tool["function"]["name"],
            "description": tool["function"]["description"],
            "parameters": tool["function"]["parameters"]
        })
    return {"tools": tools, "count": len(tools)}


@app.post("/chat/stream")
async def chat_stream_api(payload: ChatIn):
    """
    Streaming chat endpoint with verbose status updates.

    This endpoint uses Server-Sent Events (SSE) to stream:
    - Status updates (RAG retrieval, tool execution, etc.)
    - Content tokens as they're generated
    - Final completion signal

    Event types:
    - status: System status updates (type, message, details)
    - content: Streamed response tokens
    - tool_call: Tool being executed
    - tool_result: Tool execution result
    - done: Stream complete
    - error: Error occurred
    """
    user_text = payload.message.strip()

    # Get tool names for reference
    tool_names = [t["function"]["name"] for t in app.state.tools]

    async def generate_response() -> AsyncGenerator[str, None]:
        nonlocal user_text

        if not user_text:
            yield format_sse("error", {"message": "Please type a message."})
            yield format_sse("done", {})
            return

        # Step 0: Explain the pipeline
        yield format_sse("pipeline_start", {
            "type": "pipeline_info",
            "message": "Starting AI Pipeline",
            "explanation": "Every query goes through a multi-stage pipeline: (1) RAG retrieval to find relevant documents, (2) LLM processing with tool awareness, (3) Optional tool execution via MCP, (4) Final response generation.",
            "details": {
                "model": CHAT_MODEL,
                "embedding_model": EMBED_MODEL,
                "vector_store": "ChromaDB",
                "mcp_transport": "stdio",
                "available_tools": tool_names
            }
        })

        # Step 1: RAG Retrieval - with detailed explanation
        yield format_sse("rag_start", {
            "type": "rag_start",
            "message": "Step 1: RAG (Retrieval-Augmented Generation)",
            "explanation": "Before sending your question to the LLM, we first search our knowledge base to find relevant context. This helps the AI give more accurate answers based on actual dealership data.",
            "details": {
                "query": user_text,
                "vector_store": "ChromaDB",
                "collection": COLLECTION_NAME,
                "embedding_model": EMBED_MODEL,
                "top_k": 4,
                "curl_equivalent": f'curl -X POST http://localhost:11434/api/embeddings -d \'{{"model": "{EMBED_MODEL}", "prompt": "{user_text[:50]}..."}}\''
            }
        })

        rag_context = await retrieve_context(user_text, app.state.collection)

        if rag_context:
            # Extract sources and chunks from context
            sources = []
            chunks = []
            current_chunk = []
            for line in rag_context.split("\n"):
                if line.startswith("[source:"):
                    if current_chunk:
                        chunks.append("\n".join(current_chunk))
                        current_chunk = []
                    sources.append(line.split("]")[0].replace("[source: ", ""))
                else:
                    current_chunk.append(line)
            if current_chunk:
                chunks.append("\n".join(current_chunk))

            yield format_sse("rag_complete", {
                "type": "rag_complete",
                "message": f"Found {len(sources)} relevant document chunks",
                "explanation": f"ChromaDB returned {len(sources)} text chunks that are semantically similar to your query. These will be injected into the LLM prompt to provide context.",
                "details": {
                    "sources": sources,
                    "num_chunks": len(chunks),
                    "total_context_chars": len(rag_context),
                    "chunks_preview": [c[:150] + "..." if len(c) > 150 else c for c in chunks[:3]]
                }
            })
        else:
            yield format_sse("rag_complete", {
                "type": "rag_complete",
                "message": "No relevant documents found in knowledge base",
                "explanation": "The vector similarity search didn't find any documents above the relevance threshold. The LLM will rely on its training and available tools.",
                "details": {"searched_collection": COLLECTION_NAME}
            })

        # Step 2: Prepare augmented message
        user_message = user_text
        if rag_context:
            user_message = (
                f"Customer message:\n{user_text}\n\n"
                f"Knowledge base context:\n{rag_context}\n\n"
                "Use the knowledge base context when it is relevant."
            )

            yield format_sse("context_injection", {
                "type": "context_injection",
                "message": "Injecting RAG context into prompt",
                "explanation": "The retrieved documents are now being added to your message. The LLM will see both your original question AND the relevant context from our knowledge base.",
                "details": {
                    "original_message_length": len(user_text),
                    "augmented_message_length": len(user_message),
                    "context_added": True
                }
            })

        conversation.append({"role": "user", "content": user_message})

        # Step 3: Initial LLM call with tool awareness
        yield format_sse("llm_start", {
            "type": "llm_start",
            "message": "Step 2: LLM Processing with Tool Awareness",
            "explanation": f"Sending the augmented prompt to {CHAT_MODEL} via Ollama. The LLM is aware of {len(tool_names)} available tools and can decide to call them if needed to answer your question.",
            "details": {
                "model": CHAT_MODEL,
                "endpoint": OPENAI_BASE_URL,
                "tools_available": len(tool_names),
                "tool_names": tool_names,
                "conversation_turns": len(conversation),
                "curl_equivalent": f'curl -X POST {OPENAI_BASE_URL}/chat/completions -H "Content-Type: application/json" -d \'{{"model": "{CHAT_MODEL}", "messages": [...], "tools": [{len(tool_names)} tools], "stream": true}}\''
            }
        })

        # Collect streaming response
        full_content = ""
        tool_calls_data = {}
        current_tool_call_id = None

        async for chunk in chat_completion_streaming(conversation, app.state.tools):
            delta = chunk.choices[0].delta if chunk.choices else None
            if not delta:
                continue

            # Handle content streaming
            if delta.content:
                full_content += delta.content
                yield format_sse("content", {"token": delta.content})

            # Handle tool calls
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    tc_id = tc.id or current_tool_call_id
                    if tc.id:
                        current_tool_call_id = tc.id
                        tool_calls_data[tc_id] = {
                            "id": tc_id,
                            "name": tc.function.name if tc.function and tc.function.name else "",
                            "arguments": ""
                        }
                    if tc.function and tc.function.arguments:
                        if tc_id in tool_calls_data:
                            tool_calls_data[tc_id]["arguments"] += tc.function.arguments

        # Build assistant message
        msg_dict = {
            "role": "assistant",
            "content": full_content,
        }

        if tool_calls_data:
            msg_dict["tool_calls"] = [
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": tc["arguments"],
                    }
                }
                for tc in tool_calls_data.values()
            ]
        conversation.append(msg_dict)

        # Step 4: Agentic loop - Execute tools
        iteration = 0
        max_iterations = 10

        while tool_calls_data and iteration < max_iterations:
            iteration += 1

            for tc_id, tc in tool_calls_data.items():
                fn_name = tc["name"]
                try:
                    fn_args = json.loads(tc["arguments"])
                except json.JSONDecodeError:
                    fn_args = {}

                # Find tool description
                tool_desc = ""
                tool_params = {}
                for t in app.state.tools:
                    if t["function"]["name"] == fn_name:
                        tool_desc = t["function"]["description"]
                        tool_params = t["function"]["parameters"]
                        break

                # Emit detailed tool call event
                yield format_sse("tool_call", {
                    "type": "mcp_call",
                    "message": f"Step 3: MCP Tool Execution - {fn_name}",
                    "explanation": f"The LLM decided to call the '{fn_name}' tool to get real data. This is an MCP (Model Context Protocol) call to our local tool server.",
                    "details": {
                        "tool": fn_name,
                        "description": tool_desc,
                        "arguments": fn_args,
                        "mcp_transport": "stdio",
                        "mcp_server": "mcp_server.py",
                        "curl_equivalent": f'curl -X POST http://localhost:8000/mcp/call -H "Content-Type: application/json" -d \'{json.dumps({"tool": fn_name, "arguments": fn_args})}\'',
                        "mcp_json_rpc": {
                            "jsonrpc": "2.0",
                            "method": "tools/call",
                            "params": {
                                "name": fn_name,
                                "arguments": fn_args
                            }
                        }
                    }
                })

                # Execute tool via MCP
                mcp_result = await app.state.mcp_session.call_tool(fn_name, fn_args)
                result_text = extract_text_from_mcp_result(mcp_result)

                # Emit detailed tool result event
                yield format_sse("tool_result", {
                    "type": "mcp_result",
                    "message": f"Tool '{fn_name}' returned successfully",
                    "explanation": "The MCP tool executed and returned data. This result will be sent back to the LLM so it can formulate a response based on real data.",
                    "details": {
                        "tool": fn_name,
                        "result_length": len(result_text),
                        "result_full": result_text,
                        "next_step": "Sending result back to LLM for final response generation"
                    }
                })

                # Add tool result to conversation
                conversation.append({
                    "role": "tool",
                    "tool_call_id": tc_id,
                    "content": result_text,
                })

            # Get next response with streaming
            yield format_sse("llm_continue", {
                "type": "llm_continue",
                "message": f"Step 4: LLM Processing Tool Results (iteration {iteration})",
                "explanation": "The tool results have been added to the conversation. Now the LLM will process them and either call more tools or generate the final response.",
                "details": {
                    "iteration": iteration,
                    "max_iterations": max_iterations,
                    "tools_executed_this_round": len(tool_calls_data),
                    "conversation_length": len(conversation)
                }
            })

            full_content = ""
            tool_calls_data = {}
            current_tool_call_id = None

            async for chunk in chat_completion_streaming(conversation, app.state.tools):
                delta = chunk.choices[0].delta if chunk.choices else None
                if not delta:
                    continue

                if delta.content:
                    full_content += delta.content
                    yield format_sse("content", {"token": delta.content})

                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        tc_id = tc.id or current_tool_call_id
                        if tc.id:
                            current_tool_call_id = tc.id
                            tool_calls_data[tc_id] = {
                                "id": tc_id,
                                "name": tc.function.name if tc.function and tc.function.name else "",
                                "arguments": ""
                            }
                        if tc.function and tc.function.arguments:
                            if tc_id in tool_calls_data:
                                tool_calls_data[tc_id]["arguments"] += tc.function.arguments

            msg_dict = {
                "role": "assistant",
                "content": full_content,
            }
            if tool_calls_data:
                msg_dict["tool_calls"] = [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": tc["arguments"],
                        }
                    }
                    for tc in tool_calls_data.values()
                ]
            conversation.append(msg_dict)

        yield format_sse("done", {
            "type": "pipeline_complete",
            "message": "Pipeline Complete",
            "explanation": "The AI pipeline has finished processing your request. All stages completed successfully.",
            "details": {
                "total_tool_iterations": iteration,
                "rag_used": bool(rag_context),
                "final_response_length": len(full_content),
                "conversation_turns": len(conversation)
            }
        })

    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
