# Car Sales Portal Chatbot (Ollama + RAG + MCP)

A local-first AI chatbot demo for a car dealership portal. This application combines Retrieval-Augmented Generation (RAG) for knowledge retrieval with Model Context Protocol (MCP) tools for real dealership operations like inventory search, financing calculations, and appointment scheduling.

## Table of Contents

- [Features](#features)
- [Architecture Overview](#architecture-overview)
- [How It Works](#how-it-works)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Demo Prompts](#demo-prompts)
- [Splx AI Asset Management](#splx-ai-asset-management)
- [Security Scanning](#security-scanning)
- [Troubleshooting](#troubleshooting)

## Features

- **Web Chat UI** - Clean, responsive chat interface built with FastAPI and Jinja2
- **Local LLM** - Runs entirely locally using Ollama (no external API calls)
- **RAG Knowledge Base** - ChromaDB vector store with Ollama embeddings for FAQ retrieval
- **MCP Tool Server** - 12 dealership-oriented tools for real operations:
  - `search_inventory` - Search vehicles with filters (make, model, price, etc.)
  - `get_vehicle_details` - Get detailed info by stock ID
  - `compare_vehicles` - Compare multiple vehicles side-by-side
  - `check_vehicle_availability` - Check if a vehicle is available/sold/pending
  - `estimate_monthly_payment` - Calculate payments with APR, down payment, term
  - `estimate_payment_for_stock` - Payment estimation for a specific vehicle
  - `estimate_trade_in` - Trade-in value estimation
  - `get_finance_programs` - Available financing options
  - `dealership_hours` - Showroom and service department hours
  - `schedule_test_drive` - Book a test drive appointment
  - `save_customer_lead` - Capture customer inquiry
  - `get_warranty_summary` - Warranty status based on vehicle age

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           User Browser                                   │
│                         http://localhost:8000                            │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        FastAPI Server (app.py)                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐  │
│  │   Chat UI       │  │   RAG Pipeline  │  │   MCP Client            │  │
│  │   (index.html)  │  │   (ChromaDB)    │  │   (Tool Orchestration)  │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
           │                      │                        │
           │                      ▼                        ▼
           │         ┌────────────────────┐    ┌─────────────────────────┐
           │         │  Ollama Server     │    │  MCP Server             │
           │         │  (localhost:11434) │    │  (mcp_server.py)        │
           │         │                    │    │                         │
           │         │  - qwen2.5:3b      │    │  - inventory.json       │
           │         │  - nomic-embed-text│    │  - leads.json           │
           │         └────────────────────┘    │  - appointments.json    │
           │                                   └─────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Data Layer                                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐  │
│  │  chroma_db/     │  │  data/          │  │  templates/             │  │
│  │  (Vector Store) │  │  (JSON + FAQ)   │  │  (HTML UI)              │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

## How It Works

### 1. Request Flow

When a user sends a message through the chat interface:

1. **User Input** - The message is sent via POST to `/chat` endpoint
2. **RAG Context Retrieval** - The system embeds the query using Ollama and searches ChromaDB for relevant FAQ content
3. **Context Augmentation** - Retrieved knowledge is appended to the user's message
4. **LLM Processing** - The augmented message is sent to Ollama with available MCP tools
5. **Tool Execution** - If the LLM decides to use tools, it calls the MCP server
6. **Agentic Loop** - The system continues calling tools until the LLM produces a final response
7. **Response** - The assistant's reply is returned to the chat UI

### 2. RAG Pipeline (Retrieval-Augmented Generation)

The RAG system enhances the chatbot's knowledge with dealership-specific information:

- **Ingestion (`ingest.py`)**:
  - Reads text files from `data/` directory (e.g., `faq.txt`)
  - Chunks text into 600-character segments with 120-character overlap
  - Generates embeddings using Ollama's embedding model
  - Stores vectors in ChromaDB with metadata (source, chunk index)

- **Retrieval (`app.py`)**:
  - Embeds the user's query
  - Searches ChromaDB for the 4 most similar chunks
  - Includes source attribution in retrieved context

### 3. MCP Tool System (Model Context Protocol)

MCP provides a standardized way for the LLM to interact with external tools:

- **Server (`mcp_server.py`)**: Defines 12 tools using FastMCP decorators
- **Client (`app.py`)**: Connects to the MCP server via stdio
- **Tool Calling**:
  - Tools are converted to Ollama's function format
  - LLM receives tool definitions and can invoke them
  - Results are fed back for further reasoning

### 4. Agentic Loop

The chatbot operates in an agentic loop:

```
User Message → LLM (with tools) → Tool Calls?
                                      │
                    ┌─────────────────┴─────────────────┐
                    ▼                                   ▼
              Yes: Execute                        No: Return
              tools via MCP                       final response
                    │
                    ▼
              Feed results
              back to LLM
                    │
                    └──────────► Repeat until no more tool calls
```

### 5. Conversation Management

- Maintains conversation history with a system prompt
- System prompt instructs the LLM to:
  - Use retrieved knowledge for FAQs and policies
  - Use tools for inventory, pricing, scheduling
  - Not invent facts about inventory

## Prerequisites

Before running the application, ensure you have:

1. **Python 3.10+** installed
2. **Ollama** installed and running ([Download Ollama](https://ollama.com/download))

## Quick Start

### Step 1: Clone and Navigate

```bash
cd ai_red_teaming_car_sales_portal_chatbot
```

### Step 2: Install Ollama Models

Make sure Ollama is running, then pull the required models:

```bash
# Pull the chat model
ollama pull qwen2.5:3b

# Pull the embedding model
ollama pull nomic-embed-text

# Verify Ollama is serving
curl http://localhost:11434/api/tags
```

### Step 3: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Ingest Documents for RAG

```bash
python ingest.py
```

You should see: `Ingested X chunks into 'car_sales_docs'`

### Step 6: Run the Application

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

### Step 7: Open in Browser

Navigate to: **http://localhost:8000**

## Project Structure

```
ai_red_teaming_car_sales_portal_chatbot/
├── app.py                 # FastAPI main application (OpenAI SDK)
├── agents.py              # Agent & tool definitions for scanning
├── mcp_server.py          # MCP tool server with 12 dealership tools
├── ingest.py              # RAG document ingestion script
├── requirements.txt       # Python dependencies
├── pyproject.toml         # Project metadata with AI asset annotations
├── README.md              # This file
│
├── # AI Asset Configuration (for Splx)
├── ai-assets.yaml         # Centralized AI asset manifest
├── mcp.json               # MCP server configuration
├── .splx/
│   └── config.yaml        # Splx scan configuration
│
├── # CI/CD
├── .github/
│   └── workflows/
│       └── agentic-radar-scan.yaml  # Security scanning workflow
│
├── templates/
│   └── index.html         # Chat UI template
├── data/
│   ├── inventory.json     # Vehicle inventory (8 vehicles)
│   ├── faq.txt            # FAQ knowledge base for RAG
│   ├── leads.json         # Customer leads (generated)
│   └── appointments.json  # Test-drive appointments (generated)
├── chroma_db/             # ChromaDB vector store (generated)
└── venv/                  # Virtual environment (generated)
```

## Configuration

Key configuration constants in `app.py`:

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE` | `http://localhost:11434` | Ollama server URL |
| `CHAT_MODEL` | `qwen2.5:3b` | LLM for chat responses |
| `EMBED_MODEL` | `nomic-embed-text` | Model for embeddings |
| `CHROMA_DIR` | `./chroma_db` | ChromaDB storage path |
| `COLLECTION_NAME` | `car_sales_docs` | Vector collection name |

To change models, update the constants in both `app.py` and `ingest.py`.

## Demo Prompts

Try these prompts to explore the chatbot's capabilities:

**Inventory Search:**
- "Show me electric vehicles under $45,000"
- "What SUVs do you have?"
- "Show me cars with less than 20,000 miles"

**Vehicle Details:**
- "Tell me about CS1003"
- "What features does the Tesla Model 3 have?"

**Comparison:**
- "Compare CS1003 and CS1006"
- "Compare the Camry, CR-V, and Model 3"

**Availability:**
- "Is CS1007 still available?"
- "Which vehicles are available right now?"

**Financing:**
- "Estimate payment for CS1008 with $6000 down for 60 months"
- "What would my monthly payment be on a $40,000 car?"
- "What financing options do you offer?"

**Trade-In:**
- "Can you estimate a trade-in for my 2019 Honda Accord with 62,000 miles in good condition?"

**Scheduling:**
- "I want to schedule a test drive for CS1002 next Saturday afternoon"
- "My name is John, email john@example.com, I'd like to test drive the Tesla"

**General Info:**
- "What are your showroom hours?"
- "When is the service department open?"
- "What's your return policy?"

## Splx AI Asset Management

This project is configured for automatic detection by [Splx AI Asset Management](https://splx.ai/). When you connect this GitHub repository to Splx, it will automatically discover and catalog all AI assets.

### What Gets Detected

| Asset Type | Assets Detected |
|------------|-----------------|
| **Models** | `gpt-4o` (agent), `qwen2.5:3b` (chat), `nomic-embed-text` (embedding) |
| **AI Workflows** | Car Sales Chatbot Workflow (RAG + Agent) |
| **MCP Servers** | `car-sales-tools-http` (HTTP/SSE, 12 tools) |
| **Issues** | Security vulnerabilities, PII handling |

### Running the HTTP MCP Server for Splx Scanning

Splx scans remote MCP servers via HTTP/SSE. To enable MCP Server scanning:

```bash
# Start the HTTP MCP server
python mcp_server_http.py
```

The server will be available at: `http://localhost:8080/sse`

For production/remote scanning, deploy this server to a publicly accessible endpoint and update the URL in:
- `mcp.json` (servers.car-sales-tools-http.url)
- `car_sales_agent.py` (MCPServerSse params.url)
- `.splx/config.yaml` (mcp_servers[1].url)

### Configuration Files

The following files enable Splx detection:

| File | Purpose |
|------|---------|
| `ai-assets.yaml` | Centralized AI asset manifest |
| `mcp.json` | MCP server configuration |
| `pyproject.toml` | Project metadata with AI asset annotations |
| `.splx/config.yaml` | Splx-specific scan configuration |

### Connecting to Splx

1. **Install Splx GitHub App** on your organization
2. Navigate to **Splx AI Asset Management** → **Environments**
3. Click **Connect Environment** → **GitHub**
4. Enter the GitHub App Installation ID
5. Run scans for **Models**, **AI Workflows**, and **MCP Servers**

### Detected Components

#### Models
```yaml
- qwen2.5:3b        # Chat model (Ollama, 3B params, Apache-2.0)
- nomic-embed-text  # Embedding model (Ollama, 768 dims, Apache-2.0)
```

#### AI Workflow
```
User Input → RAG Retrieval → LLM Processing → Tool Execution → Response
                  ↓                ↓                ↓
            ChromaDB        qwen2.5:3b      MCP Server (12 tools)
```

#### MCP Server Tools (by category)
- **Inventory**: search, details, compare, availability, warranty
- **Financing**: payment calculator, trade-in estimator, programs
- **Scheduling**: test drive booking
- **CRM**: lead capture
- **General**: business hours

### Security Issues Detected

Splx will identify the following potential issues:

| Issue | Severity | Description |
|-------|----------|-------------|
| Prompt Injection | Medium | User input passed directly to LLM |
| PII Handling | Medium | Customer data in `schedule_test_drive`, `save_customer_lead` |
| No Authentication | Low | API endpoints lack authentication |

## Security Scanning

### Agentic Radar Integration

This project includes [Agentic Radar](https://github.com/splx-ai/agentic-radar) scanning via GitHub Actions.

#### Manual Scan

```bash
# Install Agentic Radar
pip install agentic-radar

# Scan the application
agentic-radar scan custom app.py --output-dir ./reports
```

#### Automated CI/CD Scanning

The `.github/workflows/agentic-radar-scan.yaml` workflow automatically:
- Runs on every push to `main`
- Scans all AI workflow components
- Uploads security reports as artifacts
- Comments findings on pull requests

### Security Considerations

| Component | Risk Level | Mitigation |
|-----------|------------|------------|
| `search_inventory` | Low | Read-only, no PII |
| `get_vehicle_details` | Low | Read-only, no PII |
| `schedule_test_drive` | Medium | Stores PII locally |
| `save_customer_lead` | Medium | Stores PII locally |
| System Prompt | Medium | Tool-preference guardrail |

## Troubleshooting

### Ollama Connection Error

```
httpx.ConnectError: Connection refused
```

**Solution:** Ensure Ollama is running:
```bash
ollama serve
```

### Model Not Found

```
Error: model 'qwen2.5:3b' not found
```

**Solution:** Pull the required models:
```bash
ollama pull qwen2.5:3b
ollama pull nomic-embed-text
```

### ChromaDB Empty / No RAG Context

**Solution:** Re-run the ingestion:
```bash
python ingest.py
```

### Port Already in Use

```
Address already in use
```

**Solution:** Use a different port:
```bash
uvicorn app:app --port 8001
```

### MCP Server Connection Issues

If tools aren't working, check that `mcp_server.py` is in the same directory as `app.py` and that the Python path is correct.

## Data Files

| File | Purpose |
|------|---------|
| `inventory.json` | 8 demo vehicles with full details (price, mileage, features, etc.) |
| `faq.txt` | Dealership FAQ content used for RAG retrieval |
| `leads.json` | Stores captured customer leads (created on first use) |
| `appointments.json` | Stores test-drive requests (created on first use) |

## License

This is a demo application for educational and testing purposes.
