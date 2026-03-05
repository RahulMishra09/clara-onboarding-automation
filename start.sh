#!/bin/bash

# Clara AI Automation Pipeline - Production Startup Script
# This script performs health checks and starts the system

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}🚀 Clara AI Automation Pipeline - Starting...${NC}"
echo "================================================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found${NC}"
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"

    # Activate and install dependencies
    source venv/bin/activate
    echo "Installing dependencies..."
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    echo -e "${GREEN}✅ Dependencies installed${NC}"
else
    # Activate existing virtual environment
    source venv/bin/activate
fi

# Verify we're in virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${RED}❌ Failed to activate virtual environment${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Virtual environment activated${NC}"
echo ""

# Run health check
echo -e "${BLUE}🏥 Running system health check...${NC}"
echo ""
python3 scripts/health_check.py

HEALTH_STATUS=$?

if [ $HEALTH_STATUS -ne 0 ]; then
    echo ""
    echo -e "${RED}❌ Health check failed. Please fix the issues above.${NC}"
    echo ""
    echo "Common fixes:"
    echo "  • Ollama not running? Run: ollama serve"
    echo "  • Model not downloaded? Run: ollama pull llama3.1"
    echo "  • Supabase not configured? Update .env with your credentials"
    exit 1
fi

echo ""
echo "================================================================"
echo -e "${GREEN}✅ SYSTEM READY${NC}"
echo "================================================================"
echo ""
echo "Available commands:"
echo ""
echo -e "${YELLOW}1. Process Demo Call (creates v1 Account Memo + Agent Spec):${NC}"
echo "   python scripts/pipeline_a.py data/demo_calls/test_demo.txt"
echo ""
echo -e "${YELLOW}2. Process Onboarding Call (creates v2 + Changelog):${NC}"
echo "   python scripts/pipeline_b.py data/onboarding_calls/test.txt <account-id>"
echo ""
echo -e "${YELLOW}3. Batch Process All Calls:${NC}"
echo "   python scripts/batch_process.py"
echo ""
echo -e "${YELLOW}4. View Dashboard:${NC}"
echo "   python scripts/dashboard_server.py"
echo "   Then open: http://localhost:8000/viewer.html"
echo ""
echo -e "${YELLOW}5. Setup Supabase Schema:${NC}"
echo "   python setup_schema.py"
echo ""
echo -e "${YELLOW}6. Run Tests:${NC}"
echo "   cd tests && python test_schemas.py"
echo ""
echo "================================================================"
echo ""
