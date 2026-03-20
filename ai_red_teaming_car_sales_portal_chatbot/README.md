# Car Sales Portal Chatbot - AI Red Teaming Demo

**Author: Vikas Srivastava**

A comprehensive AI chatbot demo for learning about RAG (Retrieval-Augmented Generation), MCP (Model Context Protocol), and agentic AI workflows. This application serves as an educational tool for understanding how modern AI systems work together.

## What Makes This Special for Learning

This project is designed to be **fully transparent** about what's happening under the hood:

- **Real-time Activity Monitor** - Watch every step of the AI pipeline as it happens
- **Verbose Status Updates** - Understand WHY each operation is performed
- **Curl Commands** - See the actual API calls being made
- **Collapsible Details** - Drill down into JSON-RPC calls, tool arguments, and results
- **Markdown Rendering** - Beautiful formatted responses with tables, lists, and code blocks
- **35+ Example Prompts** - Categorized examples to explore every feature

---

## Table of Contents

- [Quick Start](#quick-start)
- [Understanding the Architecture](#understanding-the-architecture)
- [Deep Dive: How Each Component Works](#deep-dive-how-each-component-works)
- [The AI Pipeline Explained](#the-ai-pipeline-explained)
- [MCP Tools Reference](#mcp-tools-reference)
- [Activity Monitor Guide](#activity-monitor-guide)
- [Example Prompts by Category](#example-prompts-by-category)
- [Technical Configuration](#technical-configuration)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites

1. **Python 3.10+**
2. **Ollama** - [Download here](https://ollama.com/download)

### Setup (5 minutes)

```bash
# 1. Navigate to project
cd ai_red_teaming_car_sales_portal_chatbot

# 2. Pull required Ollama models
ollama pull qwen2.5:3b
ollama pull nomic-embed-text

# 3. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Ingest documents into vector database
python ingest.py

# 6. Start the server
python app.py
```

### Open in Browser

Navigate to: **http://localhost:8000**

You'll see:
- **Left side**: Chat interface with markdown support
- **Right side**: Activity Monitor showing real-time pipeline execution
- **Bottom**: 35+ categorized example prompts to try

---

## Understanding the Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            YOUR BROWSER                                      │
│                         http://localhost:8000                                │
│  ┌─────────────────────────────────┬────────────────────────────────────┐   │
│  │         CHAT AREA               │        ACTIVITY MONITOR            │   │
│  │                                 │                                    │   │
│  │  ┌───────────────────────────┐  │  [PIPELINE] System Ready           │   │
│  │  │ You: Compare CS1002...    │  │  [RAG] Searching knowledge base    │   │
│  │  └───────────────────────────┘  │  [LLM] Thinking with 12 tools      │   │
│  │  ┌───────────────────────────┐  │  [TOOL] Calling compare_vehicles   │   │
│  │  │ Assistant: Here's the... │  │  [MCP] Tool returned results       │   │
│  │  │ (Markdown rendered)       │  │  [DONE] Pipeline complete          │   │
│  │  └───────────────────────────┘  │                                    │   │
│  │                                 │  Stats: RAG:1 Tools:1 Tokens:234   │   │
│  └─────────────────────────────────┴────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FASTAPI SERVER (app.py)                              │
│                                                                              │
│   POST /chat/stream  ──────────────────────────────────────────────────▶    │
│                                                                              │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌────────────┐  │
│   │  1. RAG     │───▶│  2. LLM     │───▶│  3. MCP     │───▶│  4. Stream │  │
│   │  Retrieval  │    │  Processing │    │  Tool Call  │    │  Response  │  │
│   └─────────────┘    └─────────────┘    └─────────────┘    └────────────┘  │
│         │                  │                  │                             │
│         ▼                  ▼                  ▼                             │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────────┐    │
│   │  ChromaDB   │    │   Ollama    │    │      MCP Server             │    │
│   │  Vector DB  │    │   LLM API   │    │   (mcp_server.py)           │    │
│   │             │    │             │    │                             │    │
│   │ nomic-embed │    │ qwen2.5:3b  │    │ 12 Dealership Tools:        │    │
│   │   (768-dim) │    │ (3B params) │    │ - search_inventory          │    │
│   │             │    │             │    │ - compare_vehicles          │    │
│   │ Collection: │    │ Tool-aware  │    │ - estimate_payment          │    │
│   │ car_sales_  │    │ streaming   │    │ - schedule_test_drive       │    │
│   │ docs        │    │             │    │ - ... and 8 more            │    │
│   └─────────────┘    └─────────────┘    └─────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Deep Dive: How Each Component Works

### 1. RAG (Retrieval-Augmented Generation)

**What is RAG?**
RAG enhances LLM responses by first searching a knowledge base for relevant information, then injecting that context into the prompt.

**How it works in this app:**

```
User Query: "What's your return policy?"
         │
         ▼
┌─────────────────────────────────────────┐
│  STEP 1: EMBED THE QUERY                │
│                                         │
│  POST http://localhost:11434/api/embeddings
│  {                                      │
│    "model": "nomic-embed-text",         │
│    "prompt": "What's your return policy?"
│  }                                      │
│                                         │
│  Returns: [0.023, -0.156, 0.089, ...]   │
│           (768-dimensional vector)      │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  STEP 2: SEARCH CHROMADB                │
│                                         │
│  collection.query(                      │
│    query_embeddings=[embedding],        │
│    n_results=4  # Top 4 matches         │
│  )                                      │
│                                         │
│  Uses cosine similarity to find the     │
│  most semantically similar text chunks  │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  STEP 3: INJECT CONTEXT                 │
│                                         │
│  Original: "What's your return policy?" │
│                                         │
│  Augmented:                             │
│  "Customer message:                     │
│   What's your return policy?            │
│                                         │
│   Knowledge base context:               │
│   [source: faq.txt]                     │
│   Our 7-day return policy allows...     │
│   ...                                   │
│                                         │
│   Use the knowledge base context when   │
│   it is relevant."                      │
└─────────────────────────────────────────┘
```

**Why RAG matters:**
- LLMs have training cutoff dates and don't know your specific data
- RAG injects current, domain-specific knowledge
- The model can cite sources and provide accurate information

### 2. MCP (Model Context Protocol)

**What is MCP?**
MCP is a standardized protocol for LLMs to interact with external tools and data sources. It defines how tools are discovered, called, and how results are returned.

**How it works in this app:**

```
┌─────────────────────────────────────────────────────────────────┐
│                    MCP ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐         ┌──────────────────────────────┐  │
│  │   MCP CLIENT     │  stdio  │      MCP SERVER              │  │
│  │   (app.py)       │◀───────▶│   (mcp_server.py)            │  │
│  │                  │         │                              │  │
│  │ - Connects on    │         │ - Defines 12 tools           │  │
│  │   app startup    │         │ - Uses FastMCP decorators    │  │
│  │ - Lists tools    │         │ - Reads/writes JSON files    │  │
│  │ - Calls tools    │         │ - Returns structured data    │  │
│  └──────────────────┘         └──────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

JSON-RPC Messages:

1. LIST TOOLS REQUEST:
{
  "jsonrpc": "2.0",
  "method": "tools/list",
  "id": 1
}

2. TOOL CALL REQUEST:
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "compare_vehicles",
    "arguments": {
      "stock_ids": "CS1002,CS1005"
    }
  },
  "id": 2
}

3. TOOL RESULT:
{
  "jsonrpc": "2.0",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "| Feature | CS1002 | CS1005 |..."
      }
    ]
  },
  "id": 2
}
```

**Why MCP matters:**
- Standardized protocol for tool integration
- LLM can dynamically discover available tools
- Clean separation between AI logic and business logic

### 3. Streaming with Server-Sent Events (SSE)

**What is SSE?**
Server-Sent Events allow the server to push updates to the browser in real-time over a single HTTP connection.

**How it works:**

```
Browser                                    Server
   │                                         │
   │  POST /chat/stream                      │
   │  {"message": "Compare CS1002..."}       │
   │────────────────────────────────────────▶│
   │                                         │
   │  event: pipeline_start                  │
   │  data: {"message": "Starting..."}       │
   │◀────────────────────────────────────────│
   │                                         │
   │  event: rag_start                       │
   │  data: {"message": "Searching..."}      │
   │◀────────────────────────────────────────│
   │                                         │
   │  event: rag_complete                    │
   │  data: {"message": "Found 3 docs"}      │
   │◀────────────────────────────────────────│
   │                                         │
   │  event: llm_start                       │
   │  data: {"model": "qwen2.5:3b", ...}     │
   │◀────────────────────────────────────────│
   │                                         │
   │  event: tool_call                       │
   │  data: {"tool": "compare_vehicles",...} │
   │◀────────────────────────────────────────│
   │                                         │
   │  event: tool_result                     │
   │  data: {"result_full": "| CS1002..."}   │
   │◀────────────────────────────────────────│
   │                                         │
   │  event: content                         │
   │  data: {"token": "Here"}                │
   │◀────────────────────────────────────────│
   │                                         │
   │  event: content                         │
   │  data: {"token": "'s"}                  │
   │◀────────────────────────────────────────│
   │                                         │
   │  ... (more tokens) ...                  │
   │                                         │
   │  event: done                            │
   │  data: {"total_tool_iterations": 1}     │
   │◀────────────────────────────────────────│
   │                                         │
```

---

## The AI Pipeline Explained

When you send a message, here's exactly what happens:

### Step 1: Pipeline Start
```
[PIPELINE] Starting AI Pipeline
└─ Explanation: Every query goes through: RAG → LLM → Tools → Response
└─ Details:
   - Model: qwen2.5:3b
   - Embedding: nomic-embed-text
   - Vector Store: ChromaDB
   - Available Tools: [search_inventory, compare_vehicles, ...]
```

### Step 2: RAG Retrieval
```
[RAG] Step 1: RAG (Retrieval-Augmented Generation)
└─ Explanation: Before sending to LLM, we search our knowledge base
└─ Details:
   - Query: "Compare CS1002 and CS1005"
   - Collection: car_sales_docs
   - Top-K: 4 chunks
   - Curl Equivalent:
     curl -X POST http://localhost:11434/api/embeddings \
       -d '{"model": "nomic-embed-text", "prompt": "Compare..."}'
```

### Step 3: Context Injection
```
[RAG] Injecting RAG context into prompt
└─ Explanation: Retrieved docs are added to your message
└─ Details:
   - Original length: 25 chars
   - Augmented length: 1,847 chars
   - Context added: true
```

### Step 4: LLM Processing
```
[LLM] Step 2: LLM Processing with Tool Awareness
└─ Explanation: Sending augmented prompt to qwen2.5:3b via Ollama
└─ Details:
   - Model: qwen2.5:3b
   - Tools available: 12
   - Conversation turns: 3
   - Curl Equivalent:
     curl -X POST http://localhost:11434/v1/chat/completions \
       -d '{"model": "qwen2.5:3b", "messages": [...], "tools": [12 tools]}'
```

### Step 5: Tool Execution (if needed)
```
[TOOL] Step 3: MCP Tool Execution - compare_vehicles
└─ Explanation: The LLM decided to call 'compare_vehicles' for real data
└─ Details:
   - Tool: compare_vehicles
   - Description: Compare multiple vehicles side by side
   - Arguments: {"stock_ids": "CS1002,CS1005"}
   - MCP Transport: stdio
   - JSON-RPC:
     {
       "jsonrpc": "2.0",
       "method": "tools/call",
       "params": {"name": "compare_vehicles", "arguments": {...}}
     }
```

### Step 6: Tool Result
```
[MCP] Tool 'compare_vehicles' returned successfully
└─ Explanation: MCP tool executed. Result sent back to LLM.
└─ Details:
   - Tool: compare_vehicles
   - Result length: 1,234 chars
   - Result: "| Feature | CS1002 | CS1005 |..."
   - Next step: LLM generates final response
```

### Step 7: Response Streaming
```
[CONTENT] Tokens streaming...
"Here" → "'s" → " a" → " comparison" → " of" → ...

[DONE] Pipeline Complete
└─ Details:
   - Total tool iterations: 1
   - RAG used: true
   - Response length: 856 chars
```

---

## MCP Tools Reference

### Inventory Tools (5)

| Tool | Description | Parameters |
|------|-------------|------------|
| `search_inventory` | Search vehicles with filters | make, model, body_type, fuel_type, drivetrain, min/max year, min/max price, max_mileage |
| `get_vehicle_details` | Get full details for a vehicle | stock_id (required) |
| `compare_vehicles` | Compare 2-5 vehicles side by side | stock_ids (comma-separated) |
| `check_vehicle_availability` | Check if vehicle is available | stock_id (required) |
| `get_warranty_summary` | Get warranty info based on age | stock_id (required) |

### Financing Tools (4)

| Tool | Description | Parameters |
|------|-------------|------------|
| `estimate_monthly_payment` | Calculate monthly payment | vehicle_price, down_payment, apr_percent, term_months |
| `estimate_payment_for_stock` | Payment for specific vehicle | stock_id, down_payment, apr_percent, term_months |
| `estimate_trade_in` | Estimate trade-in value | make, model, year, mileage, condition |
| `get_finance_programs` | List available programs | (none) |

### Scheduling & CRM Tools (2)

| Tool | Description | Parameters |
|------|-------------|------------|
| `schedule_test_drive` | Book a test drive | name, email, stock_id, preferred_date, preferred_time |
| `save_customer_lead` | Capture customer inquiry | name, email, phone, intent, notes |

### General Tool (1)

| Tool | Description | Parameters |
|------|-------------|------------|
| `dealership_hours` | Get business hours | department (showroom/service) |

---

## Activity Monitor Guide

The Activity Monitor sidebar shows real-time pipeline execution. Here's how to read it:

### Color Coding

| Color | Category | Meaning |
|-------|----------|---------|
| 🟣 Purple | RAG | Knowledge base operations |
| 🔵 Blue | LLM | Language model processing |
| 🟠 Orange | TOOL | Tool being called |
| 🟢 Green | MCP | Tool result received |
| 🔴 Red | ERROR | Something went wrong |

### Collapsible Details

Click on any status item to expand it and see:
- **Curl Equivalent**: Actual HTTP command you could run
- **JSON-RPC**: The MCP protocol message
- **Arguments**: What was passed to the tool
- **Result**: What the tool returned

### Stats Bar

- **RAG**: Number of knowledge base searches
- **Tools**: Number of MCP tool calls
- **Tokens**: Response tokens streamed
- **Iterations**: Tool execution loops

---

## Example Prompts by Category

### 🚗 Inventory Search
- "Show me all SUVs under $35,000 with AWD"
- "What sedans do you have available?"
- "List all electric vehicles in stock"
- "Show me trucks with less than 30,000 miles"
- "What's your cheapest car?"
- "Do you have any hybrid vehicles?"
- "What Toyota models do you have?"

### 📋 Vehicle Details
- "Tell me about vehicle CS1001"
- "What features does CS1003 have?"
- "Is CS1005 still available?"
- "What's the mileage on CS1002?"

### ⚖️ Vehicle Comparison
- "Compare CS1002 and CS1005"
- "Compare CS1001, CS1003, and CS1004"
- "Which is better: CS1002 or CS1006?"
- "Compare all your SUVs"

### 💰 Financing
- "Estimate payment for CS1003 with $5000 down for 72 months"
- "What financing options do you offer?"
- "Calculate monthly payment for a $30,000 car"
- "What's the APR for a 60-month loan?"
- "How much would CS1001 cost per month?"

### 🔄 Trade-In
- "Estimate trade-in for my 2019 Honda Civic with 45,000 miles"
- "What's my 2020 Toyota Camry worth?"
- "Trade-in value for a 2018 Ford F-150 in good condition"
- "How do you evaluate trade-ins?"

### 📅 Scheduling
- "Schedule a test drive for CS1001 next Tuesday at 2pm"
- "I want to test drive the Model 3"
- "Can I schedule a test drive for this weekend?"

### ℹ️ General Info
- "What are your business hours?"
- "What's your return policy?"
- "Do you offer warranties?"
- "What EV charging options do you have?"

### 🧩 Complex Queries
- "I need an AWD SUV under $40k with good fuel economy"
- "Help me find a family car with the best warranty"
- "I'm trading in my car and want to finance the rest"

---

## Technical Configuration

### Environment Variables (in app.py)

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_BASE_URL` | `http://localhost:11434/v1` | Ollama API endpoint |
| `CHAT_MODEL` | `qwen2.5:3b` | LLM for chat |
| `EMBED_MODEL` | `nomic-embed-text` | Embedding model |
| `CHROMA_DIR` | `./chroma_db` | Vector DB path |
| `COLLECTION_NAME` | `car_sales_docs` | Collection name |

### RAG Configuration (in ingest.py)

| Setting | Value | Description |
|---------|-------|-------------|
| Chunk Size | 600 chars | Size of text chunks |
| Chunk Overlap | 120 chars | Overlap between chunks |
| Top-K | 4 | Number of results to retrieve |

### Project Structure

```
ai_red_teaming_car_sales_portal_chatbot/
├── app.py                 # Main FastAPI application with streaming
├── mcp_server.py          # MCP tool server (12 tools)
├── mcp_server_http.py     # HTTP/SSE MCP server for remote scanning
├── ingest.py              # RAG document ingestion
├── agents.py              # Agent definitions
├── car_sales_agent.py     # OpenAI Agents SDK implementation
│
├── templates/
│   └── index.html         # Chat UI with Activity Monitor
│
├── data/
│   ├── inventory.json     # 8 demo vehicles
│   ├── faq.txt            # FAQ for RAG
│   ├── leads.json         # Customer leads (generated)
│   └── appointments.json  # Test drives (generated)
│
├── chroma_db/             # Vector database (generated)
│
├── # Configuration
├── ai-assets.yaml         # AI asset manifest
├── mcp.json               # MCP server config
├── pyproject.toml         # Python project config
├── requirements.txt       # Dependencies
└── .splx/config.yaml      # AI Red Teaming config
```

---

## Troubleshooting

### "Connection refused" to Ollama

```bash
# Make sure Ollama is running
ollama serve

# Verify it's accessible
curl http://localhost:11434/api/tags
```

### "Model not found"

```bash
# Pull required models
ollama pull qwen2.5:3b
ollama pull nomic-embed-text
```

### "No RAG context found"

```bash
# Re-run ingestion
python ingest.py
```

### "Port 8000 already in use"

```bash
# Kill existing process
lsof -ti:8000 | xargs kill -9

# Or use different port
python -c "import uvicorn; uvicorn.run('app:app', host='0.0.0.0', port=8001)"
```

### "MCP tools not working"

The MCP server runs as a subprocess. Ensure:
1. `mcp_server.py` is in the same directory as `app.py`
2. Virtual environment is activated
3. Check server logs for errors

---

## Learning Resources

- **RAG**: [What is RAG?](https://www.pinecone.io/learn/retrieval-augmented-generation/)
- **MCP**: [Model Context Protocol](https://modelcontextprotocol.io/)
- **ChromaDB**: [Documentation](https://docs.trychroma.com/)
- **Ollama**: [Getting Started](https://ollama.com/)
- **FastAPI**: [Tutorial](https://fastapi.tiangolo.com/tutorial/)

---

## License

MIT License - Educational and demonstration purposes.

**Built by Vikas Srivastava** | [GitHub](https://github.com/vikassri)
