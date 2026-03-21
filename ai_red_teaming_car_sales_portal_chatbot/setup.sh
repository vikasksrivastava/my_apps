#!/bin/bash
#
# AI Red Teaming - Car Sales Portal Chatbot Setup Script
# Starts the entire application with one command
#
# Usage: ./setup.sh [--skip-install] [--skip-ingest]
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║           AI Red Teaming - Car Sales Portal Chatbot                  ║"
echo "║                     Setup & Launch Script                            ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Parse arguments
SKIP_INSTALL=false
SKIP_INGEST=false

for arg in "$@"; do
    case $arg in
        --skip-install)
            SKIP_INSTALL=true
            shift
            ;;
        --skip-ingest)
            SKIP_INGEST=true
            shift
            ;;
    esac
done

# Check for Ollama
echo -e "${BLUE}[1/5] Checking Ollama...${NC}"

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${RED}❌ Ollama is not running${NC}"
    echo -e "${YELLOW}   Please start Ollama first:${NC}"
    echo -e "${YELLOW}     brew services start ollama${NC}"
    echo -e "${YELLOW}   Or run:${NC}"
    echo -e "${YELLOW}     ollama serve${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Ollama is running${NC}"

# Check for required models
CHAT_MODEL="qwen2.5:3b"
EMBED_MODEL="nomic-embed-text"

echo -e "${YELLOW}   Checking for required models...${NC}"

if ! ollama list | grep -q "$CHAT_MODEL"; then
    echo -e "${YELLOW}   Pulling $CHAT_MODEL...${NC}"
    ollama pull "$CHAT_MODEL"
fi
echo -e "${GREEN}✓ $CHAT_MODEL available${NC}"

if ! ollama list | grep -q "$EMBED_MODEL"; then
    echo -e "${YELLOW}   Pulling $EMBED_MODEL...${NC}"
    ollama pull "$EMBED_MODEL"
fi
echo -e "${GREEN}✓ $EMBED_MODEL available${NC}"

# Create virtual environment if it doesn't exist
echo -e "${BLUE}[2/5] Setting up Python virtual environment...${NC}"
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}   Creating virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo -e "${BLUE}[3/5] Installing dependencies...${NC}"
if [ "$SKIP_INSTALL" = true ]; then
    echo -e "${YELLOW}   Skipping installation (--skip-install flag)${NC}"
else
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    echo -e "${GREEN}✓ Dependencies installed${NC}"
fi

# Run data ingestion
echo -e "${BLUE}[4/5] Ingesting data into ChromaDB...${NC}"
if [ "$SKIP_INGEST" = true ]; then
    echo -e "${YELLOW}   Skipping ingestion (--skip-ingest flag)${NC}"
elif [ -d "chroma_db" ] && [ "$(ls -A chroma_db 2>/dev/null)" ]; then
    echo -e "${YELLOW}   ChromaDB already populated. Use --skip-ingest=false to re-ingest${NC}"
    echo -e "${GREEN}✓ Using existing ChromaDB data${NC}"
else
    echo -e "${YELLOW}   Running ingest.py to populate vector database...${NC}"
    python ingest.py
    echo -e "${GREEN}✓ Data ingested into ChromaDB${NC}"
fi

# Start the application
echo -e "${BLUE}[5/5] Starting the application...${NC}"
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════╗"
echo -e "║  Application URL: ${GREEN}http://localhost:8000${CYAN}                              ║"
echo -e "║                                                                      ║"
echo -e "║  Components:                                                         ║"
echo -e "║    • FastAPI Web Server (port 8000)                                  ║"
echo -e "║    • MCP Server (stdio subprocess - auto-managed)                    ║"
echo -e "║    • ChromaDB Vector Store (embedded)                                ║"
echo -e "║    • Ollama LLM (${CHAT_MODEL}, ${EMBED_MODEL})                      ║"
echo -e "║                                                                      ║"
echo -e "║  Features:                                                           ║"
echo -e "║    • Car inventory search via RAG                                    ║"
echo -e "║    • Financing calculator tools                                      ║"
echo -e "║    • Trade-in valuation                                              ║"
echo -e "║    • Test drive scheduling                                           ║"
echo -e "║                                                                      ║"
echo -e "║  Press Ctrl+C to stop the server                                     ║"
echo -e "╚══════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Run the app
python app.py
