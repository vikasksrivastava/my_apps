# AI Red Teaming - Banking & Finance Portal

An AI-powered banking chatbot designed for AI Red Teaming research and security testing.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface                            │
│                    (HTML/JS Chat Portal)                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                              │
│              (app.py - Streaming SSE Endpoint)                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│   ChromaDB    │   │    Ollama     │   │  MCP Server   │
│   (RAG/Vector)│   │   (LLM API)   │   │   (Banking    │
│               │   │               │   │    Tools)     │
└───────────────┘   └───────────────┘   └───────────────┘
```

## Features

- **RAG (Retrieval-Augmented Generation)**: ChromaDB vector store with banking FAQs
- **MCP Tools**: 14 banking operation tools via Model Context Protocol
- **Streaming UI**: Real-time response streaming with Server-Sent Events
- **Activity Monitor**: Verbose debugging sidebar showing all AI pipeline steps

## MCP Tools

| Category | Tool | Description |
|----------|------|-------------|
| Accounts | `get_account_balance` | Get balance and details for an account |
| Accounts | `get_customer_accounts` | List all accounts for a customer |
| Accounts | `check_account_status` | Check if account is active/frozen |
| Transactions | `get_transactions` | Get recent transactions with filters |
| Transactions | `get_spending_summary` | Spending breakdown by category |
| Transactions | `transfer_funds` | Initiate account transfer (demo) |
| Loans | `get_loan_details` | Get loan information |
| Loans | `estimate_loan_payment` | Calculate loan payments |
| Loans | `get_loan_payoff_quote` | Get payoff amount for loan |
| Products | `search_products` | Search banking products |
| Products | `get_product_details` | Get detailed product info |
| Products | `compare_products` | Compare multiple products |
| General | `get_branch_hours` | Branch and service hours |
| General | `get_interest_rates` | Current deposit/loan rates |
| General | `report_lost_card` | Report lost/stolen card (demo) |

## Quick Start

1. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

2. **Ensure Ollama is running:**
   ```bash
   ollama serve
   ollama pull qwen2.5:3b
   ollama pull nomic-embed-text
   ```

3. **Ingest documents:**
   ```bash
   python ingest.py
   ```

4. **Run the application:**
   ```bash
   python -m uvicorn app:app --host 0.0.0.0 --port 8001
   ```

5. **Open browser:** http://localhost:8001

## Project Structure

```
ai_red_teaming_banking_and_finance/
├── app.py              # FastAPI application
├── mcp_server.py       # MCP tools server
├── ingest.py           # RAG document ingestion
├── requirements.txt    # Python dependencies
├── data/
│   ├── accounts.json   # Customer accounts
│   ├── transactions.json # Transaction history
│   ├── products.json   # Banking products
│   └── loans.json      # Active loans
├── docs/
│   └── faq.txt         # Banking FAQ (for RAG)
├── templates/
│   └── index.html      # Chat UI
└── chroma_db/          # Vector store (created by ingest.py)
```

## Example Queries

### Account Queries
- "What is the balance for account ACC001?"
- "Show me all accounts for John Smith"
- "Is account ACC012 active or frozen?"

### Transaction Queries
- "Show recent transactions for ACC001"
- "Get spending summary for ACC003"
- "Transfer $500 from ACC001 to ACC002"

### Loan Queries
- "Show loan details for LOAN001"
- "Calculate payment for $30,000 loan at 7% for 60 months"
- "Get payoff quote for LOAN003"

### Product Queries
- "What savings accounts do you offer?"
- "Compare PROD003 and PROD004"
- "What CD rates do you offer?"

### General Queries
- "What are your branch hours?"
- "What are current interest rates?"
- "I lost my debit card for ACC001"

## Author

**Vikas Srivastava**

## License

For educational and research purposes only.
