"""
Banking & Finance Portal Chatbot - Main Application
====================================================

An AI-powered chatbot using:
- OpenAI SDK (with Ollama backend)
- RAG with ChromaDB
- MCP Tools for banking operations

This application is designed for AI Red Teaming research and security scanning.

Author: Vikas Srivastava
"""

import json
import asyncio
import sys
import time
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Optional

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

OPENAI_BASE_URL = "http://localhost:11434/v1"
OPENAI_API_KEY = "ollama"

CHAT_MODEL = "qwen2.5:3b"
EMBED_MODEL = "nomic-embed-text"

CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "banking_docs"

SYSTEM_PROMPT = """You are a helpful virtual assistant for a retail bank.

Your capabilities:
- Use retrieved knowledge for bank policies, fees, and general FAQs
- Use tools for account balances, transactions, loans, products, and branch info
- Never invent account balances or transaction details
- If a tool is available for a question, prefer using it
- Protect customer privacy - only share information about their own accounts

Always be helpful, professional, secure, and accurate."""


# =============================================================================
# OPENAI CLIENT SETUP
# =============================================================================

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
    chroma = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = chroma.get_or_create_collection(name=COLLECTION_NAME)
    app.state.collection = collection

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["mcp_server.py"],
    )

    stdio_ctx = stdio_client(server_params)
    read_stream, write_stream = await stdio_ctx.__aenter__()

    session_ctx = ClientSession(read_stream, write_stream)
    session = await session_ctx.__aenter__()
    await session.initialize()

    tools_result = await session.list_tools()
    app.state.mcp_session = session
    app.state.mcp_session_ctx = session_ctx
    app.state.stdio_ctx = stdio_ctx
    app.state.tools = [mcp_tool_to_openai_tool(t) for t in tools_result.tools]

    yield

    await session_ctx.__aexit__(None, None, None)
    await stdio_ctx.__aexit__(None, None, None)


# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

app = FastAPI(
    title="Banking & Finance Portal Chatbot",
    description="AI-powered chatbot for banking operations",
    version="1.0.0",
    lifespan=lifespan,
)

templates = Jinja2Templates(directory="templates")

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
    Streaming chat endpoint with EXTREMELY verbose status updates.

    This endpoint uses Server-Sent Events (SSE) to stream:
    - Full API request/response bodies
    - curl commands and Python equivalents
    - MCP JSON-RPC structures
    - Timing breakdowns
    - Educational explanations

    Event types:
    - pipeline_start: Full architecture overview
    - embedding_start/complete: Embedding API details
    - rag_start/complete: ChromaDB search details
    - context_injection: Prompt augmentation
    - llm_start: LLM API call with full body
    - tool_call/result: MCP tool execution
    - content: Streamed response tokens
    - done: Pipeline summary with learnings
    """
    user_text = payload.message.strip()
    tool_names = [t["function"]["name"] for t in app.state.tools]
    tools_full = app.state.tools

    async def generate_response() -> AsyncGenerator[str, None]:
        nonlocal user_text

        if not user_text:
            yield format_sse("error", {"message": "Please type a message."})
            yield format_sse("done", {})
            return

        pipeline_start_time = time.time()

        # =====================================================================
        # STEP 0: PIPELINE OVERVIEW
        # =====================================================================
        yield format_sse("pipeline_start", {
            "type": "pipeline_info",
            "message": "🚀 Starting AI Pipeline",
            "explanation": "Every query goes through a multi-stage pipeline. Here's exactly what happens:\n\n1️⃣ EMBEDDING: Your question is converted to a 768-dimensional vector using nomic-embed-text\n2️⃣ RAG SEARCH: ChromaDB searches for semantically similar documents using cosine similarity\n3️⃣ CONTEXT INJECTION: Retrieved docs are prepended to your message\n4️⃣ LLM INFERENCE: The augmented prompt + tool definitions are sent to the LLM\n5️⃣ TOOL EXECUTION: If LLM requests tools, we execute them via MCP\n6️⃣ RESPONSE GENERATION: Final answer is streamed back",
            "details": {
                "architecture": {
                    "llm_provider": "Ollama (OpenAI-compatible API)",
                    "llm_model": CHAT_MODEL,
                    "llm_endpoint": OPENAI_BASE_URL,
                    "embedding_model": EMBED_MODEL,
                    "embedding_dimensions": 768,
                    "vector_store": "ChromaDB (persistent)",
                    "vector_store_path": CHROMA_DIR,
                    "collection_name": COLLECTION_NAME,
                    "mcp_transport": "stdio (subprocess)",
                    "mcp_server_script": "mcp_server.py"
                },
                "available_tools": tool_names,
                "tool_count": len(tool_names),
                "system_prompt_preview": SYSTEM_PROMPT[:200] + "..."
            }
        })

        # =====================================================================
        # STEP 1: EMBEDDING GENERATION
        # =====================================================================
        embed_start_time = time.time()

        # Full embedding request body
        embed_request_body = {
            "model": EMBED_MODEL,
            "input": [user_text]
        }

        yield format_sse("embedding_start", {
            "type": "embedding_start",
            "message": "📊 Step 1a: Generating Query Embedding",
            "explanation": f"Converting your question into a numerical vector (embedding) that captures its semantic meaning. This allows us to find similar documents even if they don't share exact keywords.\n\nThe embedding model '{EMBED_MODEL}' converts text into a 768-dimensional vector where similar meanings cluster together in vector space.",
            "details": {
                "why_this_step": "Embeddings enable semantic search. 'What's my balance' will match documents about 'account funds' even without exact word matches.",
                "model": EMBED_MODEL,
                "input_text": user_text,
                "input_length_chars": len(user_text),
                "expected_output_dimensions": 768,
                "api_endpoint": f"{OPENAI_BASE_URL}/embeddings",
                "full_request_body": embed_request_body,
                "curl_command": f'''curl -X POST "{OPENAI_BASE_URL}/embeddings" \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer {OPENAI_API_KEY}" \\
  -d '{json.dumps(embed_request_body, indent=2)}' ''',
                "equivalent_python": f'''from openai import OpenAI
client = OpenAI(base_url="{OPENAI_BASE_URL}", api_key="{OPENAI_API_KEY}")
response = client.embeddings.create(model="{EMBED_MODEL}", input=["{user_text[:50]}..."])
embedding = response.data[0].embedding  # 768-dim vector'''
            }
        })

        # Actually get the embedding
        query_embedding = (await get_embeddings([user_text]))[0]
        embed_time = time.time() - embed_start_time

        yield format_sse("embedding_complete", {
            "type": "embedding_complete",
            "message": f"✅ Embedding Generated ({embed_time:.3f}s)",
            "explanation": "Your question has been converted to a 768-dimensional vector. Here's a sample of the values - these numbers represent the semantic meaning of your text in a way computers can process.",
            "details": {
                "embedding_preview": query_embedding[:20],  # First 20 dimensions
                "embedding_stats": {
                    "dimensions": len(query_embedding),
                    "min_value": round(min(query_embedding), 6),
                    "max_value": round(max(query_embedding), 6),
                    "sample_values": [round(v, 6) for v in query_embedding[:10]]
                },
                "processing_time_ms": round(embed_time * 1000, 2),
                "api_response_format": {
                    "object": "list",
                    "data": [{
                        "object": "embedding",
                        "embedding": f"[{query_embedding[0]:.6f}, {query_embedding[1]:.6f}, ... {len(query_embedding)} total values]",
                        "index": 0
                    }],
                    "model": EMBED_MODEL
                }
            }
        })

        # =====================================================================
        # STEP 2: CHROMADB VECTOR SEARCH
        # =====================================================================
        chroma_start_time = time.time()

        yield format_sse("rag_start", {
            "type": "rag_start",
            "message": "🔍 Step 1b: RAG Vector Search in ChromaDB",
            "explanation": f"Now we search ChromaDB for documents with similar embeddings. ChromaDB uses cosine similarity to find the top-k most similar document chunks.\n\nCosine similarity measures the angle between two vectors - vectors pointing in similar directions (similar meaning) have similarity close to 1.0.",
            "details": {
                "why_this_step": "RAG (Retrieval-Augmented Generation) grounds the LLM's response in actual bank policy data, reducing hallucinations and providing accurate information.",
                "query": user_text,
                "vector_store": "ChromaDB",
                "collection": COLLECTION_NAME,
                "storage_path": CHROMA_DIR,
                "search_algorithm": "cosine_similarity",
                "top_k": 4,
                "chromadb_query": {
                    "method": "collection.query()",
                    "parameters": {
                        "query_embeddings": f"[[{query_embedding[0]:.4f}, {query_embedding[1]:.4f}, ... 768 dims]]",
                        "n_results": 4,
                        "include": ["documents", "metadatas", "distances"]
                    }
                },
                "equivalent_python": f'''import chromadb
client = chromadb.PersistentClient(path="{CHROMA_DIR}")
collection = client.get_collection("{COLLECTION_NAME}")
results = collection.query(
    query_embeddings=[embedding],  # Your 768-dim vector
    n_results=4
)'''
            }
        })

        # Perform the actual ChromaDB query
        result = app.state.collection.query(
            query_embeddings=[query_embedding],
            n_results=4,
            include=["documents", "metadatas", "distances"]
        )

        chroma_time = time.time() - chroma_start_time

        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        # Build context
        rag_context = ""
        if docs:
            chunks = []
            for doc, meta in zip(docs, metas):
                source = meta.get("source", "unknown")
                chunks.append(f"[source: {source}]\n{doc}")
            rag_context = "\n\n".join(chunks)

        if docs:
            yield format_sse("rag_complete", {
                "type": "rag_complete",
                "message": f"✅ Found {len(docs)} Relevant Documents ({chroma_time:.3f}s)",
                "explanation": f"ChromaDB returned {len(docs)} document chunks ranked by semantic similarity. Lower distance = higher similarity. These documents will be injected into the LLM prompt.",
                "details": {
                    "num_results": len(docs),
                    "processing_time_ms": round(chroma_time * 1000, 2),
                    "results": [
                        {
                            "rank": i + 1,
                            "source": metas[i].get("source", "unknown"),
                            "distance": round(distances[i], 4),
                            "similarity_score": round(1 - distances[i], 4),
                            "content_preview": docs[i][:300] + "..." if len(docs[i]) > 300 else docs[i],
                            "content_length": len(docs[i])
                        }
                        for i in range(len(docs))
                    ],
                    "chromadb_raw_response": {
                        "ids": result.get("ids", []),
                        "distances": [round(d, 4) for d in distances],
                        "metadatas": metas
                    },
                    "total_context_chars": len(rag_context)
                }
            })
        else:
            yield format_sse("rag_complete", {
                "type": "rag_complete",
                "message": "⚠️ No Relevant Documents Found",
                "explanation": "The vector search didn't find documents with high enough similarity scores. The LLM will rely on its training and available tools instead.",
                "details": {
                    "searched_collection": COLLECTION_NAME,
                    "processing_time_ms": round(chroma_time * 1000, 2)
                }
            })

        # =====================================================================
        # STEP 3: CONTEXT INJECTION (Prompt Augmentation)
        # =====================================================================
        user_message = user_text
        if rag_context:
            user_message = (
                f"Customer message:\n{user_text}\n\n"
                f"Knowledge base context:\n{rag_context}\n\n"
                "Use the knowledge base context when it is relevant."
            )

            yield format_sse("context_injection", {
                "type": "context_injection",
                "message": "📝 Step 2: Context Injection (Prompt Augmentation)",
                "explanation": "The retrieved documents are now prepended to your message. This is the 'Augmented' part of RAG - we're augmenting your prompt with retrieved knowledge.\n\nThe LLM will see:\n1. System prompt (defining its role)\n2. Your message + RAG context\n3. Tool definitions (what it can call)",
                "details": {
                    "why_this_step": "By injecting relevant context, we give the LLM specific bank policy information to reference, making responses more accurate and grounded in actual data.",
                    "original_message": user_text,
                    "original_length": len(user_text),
                    "augmented_length": len(user_message),
                    "context_added_chars": len(user_message) - len(user_text),
                    "augmented_message_full": user_message,
                    "prompt_structure": {
                        "system_prompt": SYSTEM_PROMPT,
                        "user_message_with_context": user_message[:500] + "..." if len(user_message) > 500 else user_message
                    }
                }
            })

        conversation.append({"role": "user", "content": user_message})

        # =====================================================================
        # STEP 4: LLM INFERENCE WITH TOOLS
        # =====================================================================
        llm_start_time = time.time()

        # Build the full messages array for display
        messages_for_display = []
        for msg in conversation:
            display_msg = {"role": msg["role"]}
            if msg["role"] == "system":
                display_msg["content"] = msg["content"]
            elif msg["role"] == "user":
                display_msg["content"] = msg["content"][:500] + "..." if len(msg["content"]) > 500 else msg["content"]
            elif msg["role"] == "assistant":
                display_msg["content"] = msg.get("content", "")
                if msg.get("tool_calls"):
                    display_msg["tool_calls"] = msg["tool_calls"]
            elif msg["role"] == "tool":
                display_msg["tool_call_id"] = msg.get("tool_call_id")
                display_msg["content"] = msg["content"][:200] + "..." if len(msg["content"]) > 200 else msg["content"]
            messages_for_display.append(display_msg)

        # Full request body that would be sent to the API
        llm_request_body = {
            "model": CHAT_MODEL,
            "messages": messages_for_display,
            "tools": tools_full,
            "tool_choice": "auto",
            "stream": True
        }

        yield format_sse("llm_start", {
            "type": "llm_start",
            "message": "🤖 Step 3: LLM Inference with Tool Awareness",
            "explanation": f"Sending the augmented prompt to {CHAT_MODEL} via Ollama's OpenAI-compatible API. The model will:\n\n1. Read the system prompt to understand its role\n2. Process the conversation history\n3. See the {len(tool_names)} available banking tools and their schemas\n4. Decide whether to respond directly OR call a tool\n\nIf it needs real-time data (balances, transactions, etc.), it will output a tool_call instead of text.",
            "details": {
                "why_this_step": "The LLM acts as the 'brain' - it understands your question, decides if tools are needed, and generates the response.",
                "model": CHAT_MODEL,
                "api_endpoint": f"{OPENAI_BASE_URL}/chat/completions",
                "api_type": "OpenAI-compatible (Ollama)",
                "streaming_enabled": True,
                "conversation_turns": len(conversation),
                "tools_available": len(tool_names),
                "tool_choice_mode": "auto (LLM decides)",
                "full_request_body": llm_request_body,
                "curl_command": f'''curl -X POST "{OPENAI_BASE_URL}/chat/completions" \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer {OPENAI_API_KEY}" \\
  -d '{json.dumps(llm_request_body, indent=2)}' ''',
                "equivalent_python": f'''from openai import AsyncOpenAI
client = AsyncOpenAI(base_url="{OPENAI_BASE_URL}", api_key="{OPENAI_API_KEY}")
response = await client.chat.completions.create(
    model="{CHAT_MODEL}",
    messages=[...{len(conversation)} messages...],
    tools=[...{len(tool_names)} tool definitions...],
    tool_choice="auto",
    stream=True
)
async for chunk in response:
    print(chunk.choices[0].delta)''',
                "tool_definitions": tools_full
            }
        })

        # Collect streaming response
        full_content = ""
        tool_calls_data = {}
        current_tool_call_id = None
        token_count = 0
        first_token = True
        stream_start_time = time.time()

        async for chunk in chat_completion_streaming(conversation, app.state.tools):
            delta = chunk.choices[0].delta if chunk.choices else None
            if not delta:
                continue

            # Handle content streaming
            if delta.content:
                if first_token:
                    first_token = False
                    time_to_first_token = time.time() - stream_start_time
                    yield format_sse("streaming_start", {
                        "type": "streaming_start",
                        "message": f"📝 Response Streaming Started ({time_to_first_token:.3f}s to first token)",
                        "explanation": "The LLM is now generating text token-by-token. SSE (Server-Sent Events) streams each token to the browser as soon as it's generated, giving you real-time output.\n\n**How SSE Works:**\n- Server keeps HTTP connection open\n- Each token sent as 'event: content\\ndata: {token}\\n\\n'\n- Browser's EventSource API receives and displays tokens",
                        "details": {
                            "time_to_first_token_ms": round(time_to_first_token * 1000, 2),
                            "sse_format": "event: content\\ndata: {\"token\": \"...\"}\\n\\n",
                            "content_type": "text/event-stream"
                        }
                    })
                token_count += 1
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

        # =====================================================================
        # STEP 5: AGENTIC TOOL EXECUTION LOOP
        # =====================================================================
        iteration = 0
        max_iterations = 10
        total_tools_executed = 0

        while tool_calls_data and iteration < max_iterations:
            iteration += 1

            yield format_sse("tool_loop_start", {
                "type": "tool_loop_iteration",
                "message": f"🔄 Agentic Loop - Iteration {iteration}",
                "explanation": f"The LLM requested {len(tool_calls_data)} tool call(s). In an 'agentic' pattern, the LLM can make multiple tool calls and even chain them together, using results from one tool to inform the next.\n\nThis loop continues until the LLM produces a final text response without requesting more tools.",
                "details": {
                    "iteration": iteration,
                    "max_iterations": max_iterations,
                    "tools_to_execute": list(tool_calls_data.keys()),
                    "why_agentic": "Agentic = the AI can autonomously decide which tools to call and how to use results. It's not just Q&A - it's planning and executing."
                }
            })

            for tc_id, tc in tool_calls_data.items():
                fn_name = tc["name"]
                tool_call_start_time = time.time()
                try:
                    fn_args = json.loads(tc["arguments"])
                except json.JSONDecodeError:
                    fn_args = {}

                total_tools_executed += 1

                # Find full tool definition
                tool_def = None
                for t in app.state.tools:
                    if t["function"]["name"] == fn_name:
                        tool_def = t["function"]
                        break

                # Build MCP JSON-RPC request
                mcp_request = {
                    "jsonrpc": "2.0",
                    "id": tc_id,
                    "method": "tools/call",
                    "params": {
                        "name": fn_name,
                        "arguments": fn_args
                    }
                }

                # Emit very detailed tool call event
                yield format_sse("tool_call", {
                    "type": "mcp_call",
                    "message": f"🔧 MCP Tool Call: {fn_name}",
                    "explanation": f"The LLM is calling '{fn_name}' via MCP (Model Context Protocol).\n\n**Why MCP?** MCP is a standardized protocol for AI-tool communication. It uses JSON-RPC 2.0 over stdio (subprocess pipes). This allows:\n- Language-agnostic tools (Python, TypeScript, Rust, etc.)\n- Secure sandboxing\n- Standardized discovery and schemas",
                    "details": {
                        "tool_name": fn_name,
                        "tool_description": tool_def.get("description", "") if tool_def else "",
                        "tool_parameters_schema": tool_def.get("parameters", {}) if tool_def else {},
                        "arguments_provided": fn_args,
                        "tool_call_id": tc_id,
                        "mcp_protocol": {
                            "transport": "stdio (subprocess)",
                            "server_command": f"{sys.executable} mcp_server.py",
                            "protocol_version": "2024-11-05",
                            "message_format": "JSON-RPC 2.0"
                        },
                        "mcp_request_full": mcp_request,
                        "stdio_communication": {
                            "direction": "Parent → Child (stdin)",
                            "data_sent": json.dumps(mcp_request),
                            "explanation": "We write this JSON to the MCP server's stdin, then read the response from its stdout"
                        },
                        "python_mcp_call": f'''# Using MCP Python SDK
from mcp import ClientSession
result = await session.call_tool("{fn_name}", {json.dumps(fn_args)})'''
                    }
                })

                # Execute tool via MCP
                mcp_result = await app.state.mcp_session.call_tool(fn_name, fn_args)
                result_text = extract_text_from_mcp_result(mcp_result)
                tool_call_time = time.time() - tool_call_start_time

                # Build MCP JSON-RPC response
                mcp_response = {
                    "jsonrpc": "2.0",
                    "id": tc_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": result_text
                            }
                        ]
                    }
                }

                # Emit very detailed tool result event
                yield format_sse("tool_result", {
                    "type": "mcp_result",
                    "message": f"✅ Tool '{fn_name}' Completed ({tool_call_time:.3f}s)",
                    "explanation": f"The MCP server executed the tool and returned results. This data is now added to the conversation as a 'tool' message, which the LLM will read to formulate its response.\n\n**Data Flow:**\n1. MCP server received JSON-RPC request via stdin\n2. Server executed Python function '{fn_name}'\n3. Server returned JSON-RPC response via stdout\n4. We parse and inject result into conversation",
                    "details": {
                        "tool_name": fn_name,
                        "execution_time_ms": round(tool_call_time * 1000, 2),
                        "result_length_chars": len(result_text),
                        "result_full": result_text,
                        "mcp_response_full": mcp_response,
                        "stdio_communication": {
                            "direction": "Child → Parent (stdout)",
                            "data_received": json.dumps(mcp_response)
                        },
                        "conversation_injection": {
                            "role": "tool",
                            "tool_call_id": tc_id,
                            "content_preview": result_text[:300] + "..." if len(result_text) > 300 else result_text
                        },
                        "next_step": "Result will be sent back to LLM in the next iteration"
                    }
                })

                # Add tool result to conversation
                conversation.append({
                    "role": "tool",
                    "tool_call_id": tc_id,
                    "content": result_text,
                })

            # Get next response with streaming
            llm_continue_start = time.time()

            # Build updated messages for display
            updated_messages = []
            for msg in conversation[-5:]:  # Last 5 messages for context
                display_msg = {"role": msg["role"]}
                if msg["role"] == "tool":
                    display_msg["tool_call_id"] = msg.get("tool_call_id")
                    display_msg["content"] = msg["content"][:200] + "..." if len(msg["content"]) > 200 else msg["content"]
                else:
                    display_msg["content"] = msg.get("content", "")[:200] + "..." if len(msg.get("content", "")) > 200 else msg.get("content", "")
                updated_messages.append(display_msg)

            yield format_sse("llm_continue", {
                "type": "llm_continue",
                "message": f"🤖 LLM Processing Tool Results (Iteration {iteration})",
                "explanation": f"Tool results have been added to the conversation. The LLM now sees:\n\n1. Original system prompt\n2. All previous messages\n3. The assistant's tool_call request\n4. The tool's response (what we just got)\n\nThe LLM will decide: generate final answer, or call more tools?",
                "details": {
                    "iteration": iteration,
                    "max_iterations": max_iterations,
                    "tools_executed_this_round": len(tool_calls_data),
                    "total_tools_executed": total_tools_executed,
                    "conversation_length": len(conversation),
                    "recent_messages": updated_messages,
                    "llm_decision_options": [
                        "1. Generate text response (conversation complete)",
                        "2. Call more tools (continue loop)",
                        "3. Call different tools based on results"
                    ]
                }
            })

            full_content = ""
            tool_calls_data = {}
            current_tool_call_id = None
            first_token_in_iteration = True
            iteration_stream_start = time.time()

            async for chunk in chat_completion_streaming(conversation, app.state.tools):
                delta = chunk.choices[0].delta if chunk.choices else None
                if not delta:
                    continue

                if delta.content:
                    if first_token_in_iteration:
                        first_token_in_iteration = False
                        ttft = time.time() - iteration_stream_start
                        yield format_sse("streaming_start", {
                            "type": "streaming_start",
                            "message": f"📝 Response Streaming (Iteration {iteration}) - {ttft:.3f}s to first token",
                            "explanation": "After processing tool results, the LLM is now generating its response.",
                            "details": {
                                "iteration": iteration,
                                "time_to_first_token_ms": round(ttft * 1000, 2)
                            }
                        })
                    token_count += 1
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

        pipeline_total_time = time.time() - pipeline_start_time

        yield format_sse("done", {
            "type": "pipeline_complete",
            "message": f"🎉 Pipeline Complete ({pipeline_total_time:.2f}s total)",
            "explanation": f"The AI pipeline has finished processing your request.\n\n**Pipeline Summary:**\n1. ✅ Embedding generated for semantic search\n2. ✅ ChromaDB searched for relevant documents\n3. ✅ Context injected into prompt\n4. ✅ LLM inference completed\n5. ✅ {total_tools_executed} tool(s) executed via MCP\n6. ✅ Final response generated and streamed",
            "details": {
                "timing": {
                    "total_time_seconds": round(pipeline_total_time, 3),
                    "total_time_ms": round(pipeline_total_time * 1000, 2)
                },
                "pipeline_summary": {
                    "rag_used": bool(rag_context),
                    "documents_retrieved": len(docs) if docs else 0,
                    "tool_iterations": iteration,
                    "total_tools_executed": total_tools_executed,
                    "final_response_length": len(full_content),
                    "conversation_turns": len(conversation)
                },
                "conversation_state": {
                    "total_messages": len(conversation),
                    "system_messages": 1,
                    "user_messages": len([m for m in conversation if m["role"] == "user"]),
                    "assistant_messages": len([m for m in conversation if m["role"] == "assistant"]),
                    "tool_messages": len([m for m in conversation if m["role"] == "tool"])
                },
                "what_you_learned": [
                    f"1. Your query was embedded using '{EMBED_MODEL}' into a 768-dim vector",
                    f"2. ChromaDB found {len(docs) if docs else 0} relevant document chunks",
                    f"3. The LLM '{CHAT_MODEL}' processed your augmented prompt",
                    f"4. {total_tools_executed} MCP tool calls were executed via JSON-RPC over stdio",
                    "5. The response was streamed back token-by-token via SSE"
                ]
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
