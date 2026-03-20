
import json
from contextlib import asynccontextmanager
from typing import Any

import chromadb
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


OLLAMA_BASE = "http://localhost:11434"
CHAT_MODEL = "qwen2.5:3b"
EMBED_MODEL = "nomic-embed-text"
CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "car_sales_docs"


class ChatIn(BaseModel):
    message: str


def mcp_tool_to_ollama_tool(tool: Any) -> dict[str, Any]:
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


async def ollama_embed(texts: list[str]) -> list[list[float]]:
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{OLLAMA_BASE}/api/embed",
            json={"model": EMBED_MODEL, "input": texts},
        )
        resp.raise_for_status()
        return resp.json()["embeddings"]


async def ollama_chat(messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=300) as client:
        resp = await client.post(
            f"{OLLAMA_BASE}/api/chat",
            json={
                "model": CHAT_MODEL,
                "messages": messages,
                "tools": tools,
                "stream": False,
            },
        )
        resp.raise_for_status()
        return resp.json()["message"]


def extract_text_from_mcp_result(result: Any) -> str:
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


async def retrieve_context(query: str, collection) -> str:
    embedding = (await ollama_embed([query]))[0]
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    chroma = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = chroma.get_or_create_collection(name=COLLECTION_NAME)
    app.state.collection = collection

    server_params = StdioServerParameters(
        command="python",
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
    app.state.tools = [mcp_tool_to_ollama_tool(t) for t in tools_result.tools]

    yield

    await session_ctx.__aexit__(None, None, None)
    await stdio_ctx.__aexit__(None, None, None)


app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

conversation: list[dict[str, Any]] = [
    {
        "role": "system",
        "content": (
            "You are a helpful assistant for a car sales portal. "
            "Use retrieved knowledge for dealership policies and general FAQs. "
            "Use tools for inventory, pricing, payments, trade-ins, hours, and appointments. "
            "Do not invent exact inventory facts. If a tool is available for a question, prefer using it."
        ),
    }
]


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health():
    return {"ok": True, "model": CHAT_MODEL, "embed_model": EMBED_MODEL}


@app.post("/chat")
async def chat_api(payload: ChatIn):
    user_text = payload.message.strip()
    if not user_text:
        return JSONResponse({"reply": "Please type a message."})

    rag_context = await retrieve_context(user_text, app.state.collection)

    user_message = user_text
    if rag_context:
        user_message = (
            f"Customer message:\n{user_text}\n\n"
            f"Knowledge base context:\n{rag_context}\n\n"
            "Use the knowledge base context when it is relevant."
        )

    conversation.append({"role": "user", "content": user_message})

    assistant_message = await ollama_chat(conversation, app.state.tools)
    conversation.append(assistant_message)

    tool_calls = assistant_message.get("tool_calls", [])

    while tool_calls:
        for call in tool_calls:
            fn_name = call["function"]["name"]
            fn_args = call["function"].get("arguments", {})

            mcp_result = await app.state.mcp_session.call_tool(fn_name, fn_args)
            result_text = extract_text_from_mcp_result(mcp_result)

            conversation.append({
                "role": "tool",
                "name": fn_name,
                "content": result_text,
            })

        assistant_message = await ollama_chat(conversation, app.state.tools)
        conversation.append(assistant_message)
        tool_calls = assistant_message.get("tool_calls", [])

    return {"reply": assistant_message.get("content", "")}
