#!/bin/bash
#
# AI Red Teaming - Banking & Finance Portal Setup Script
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
echo "║         AI Red Teaming - Banking & Finance Portal                    ║"
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

# Check for OpenAI API key
echo -e "${BLUE}[1/5] Checking environment...${NC}"
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  OPENAI_API_KEY not set in environment${NC}"
    echo -e "${YELLOW}   You can set it with: export OPENAI_API_KEY='your-key-here'${NC}"
    echo -e "${YELLOW}   Or create a .env file with: OPENAI_API_KEY=your-key-here${NC}"

    # Check for .env file
    if [ -f ".env" ]; then
        echo -e "${GREEN}   Found .env file, sourcing it...${NC}"
        export $(grep -v '^#' .env | xargs)
    fi

    if [ -z "$OPENAI_API_KEY" ]; then
        echo -e "${RED}❌ OPENAI_API_KEY is required. Please set it and try again.${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}✓ OPENAI_API_KEY is set${NC}"

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
echo -e "║  Application URL: ${GREEN}http://localhost:8001${CYAN}                              ║"
echo -e "║                                                                      ║"
echo -e "║  Components:                                                         ║"
echo -e "║    • FastAPI Web Server (port 8001)                                  ║"
echo -e "║    • MCP Server (stdio subprocess - auto-managed)                    ║"
echo -e "║    • ChromaDB Vector Store (embedded)                                ║"
echo -e "║    • OpenAI GPT Integration                                          ║"
echo -e "║                                                                      ║"
echo -e "║  Press Ctrl+C to stop the server                                     ║"
echo -e "╚══════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Run the app
python app.py
