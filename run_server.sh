#!/usr/bin/env bash 

# Description: Check if venv is active, if not, activate it and run uvicorn

# Colors for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if virtual environment is active
check_venv() {
    if [[ -n "$VIRTUAL_ENV" ]]; then
        return 0  # venv is active
    else
        return 1  # venv is not active
    fi
}

# Function to activate venv
activate_venv() {
    if [[ -f "venv/bin/activate" ]]; then
        echo -e "${BLUE}🔧 Activating virtual environment...${NC}"
        source venv/bin/activate
        if [[ -n "$VIRTUAL_ENV" ]]; then
            echo -e "${GREEN}✅ Virtual environment activated successfully!${NC}"
            return 0
        else
            echo -e "${RED}❌ Failed to activate virtual environment!${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ venv/bin/activate not found! Please create a virtual environment first.${NC}"
        return 1
    fi
}

# Main script execution
echo -e "${BLUE}🚀 Starting server script...${NC}"

# Check if venv is active
if check_venv; then
    echo -e "${GREEN}✅ Virtual environment is already active!${NC}"
    echo -e "${YELLOW}📦 Current Python: $(which python)${NC}"
else
    echo -e "${YELLOW}⚠️  Virtual environment is not active.${NC}"
    echo -e "${BLUE}🔧 Attempting to activate venv...${NC}"
    
    if activate_venv; then
        echo -e "${GREEN}✅ Environment activated successfully!${NC}"
    else
        echo -e "${RED}❌ Failed to activate environment. Exiting...${NC}"
        exit 1
    fi
fi

# Check if uvicorn is installed
if ! command -v uvicorn &> /dev/null; then
    echo -e "${RED}❌ uvicorn is not installed! Please install it with: pip install uvicorn${NC}"
    exit 1
fi

# Run the uvicorn server
echo -e "${GREEN}🚀 Starting uvicorn server...${NC}"
echo -e "${BLUE}📡 Server will run at: http://localhost:8000${NC}"
echo -e "${YELLOW}🔄 Press Ctrl+C to stop the server${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Run uvicorn with reload
uvicorn app.main:app --reload

# This will execute when the server stops
echo -e "${YELLOW}🛑 Server stopped.${NC}"