#!/bin/bash
# Setup script for the Document Converter API development environment

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'  # No Color

echo -e "${GREEN}Setting up Document Converter API development environment...${NC}"

# Check if uv is installed
if command -v uv &> /dev/null; then
    echo -e "${GREEN}uv is installed, using it for dependency management${NC}"
else
    echo -e "${RED}uv is not installed. Please install it first:${NC}"
    echo -e "${YELLOW}curl -sSf https://astral.sh/uv/install.sh | bash${NC}"
    echo -e "${RED}Exiting setup...${NC}"
    exit 1
fi

# Create virtual environment
echo -e "${GREEN}Creating virtual environment...${NC}"
uv venv

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source .venv/bin/activate

# Install dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
uv pip install -e ".[dev,examples]"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${GREEN}Creating .env file from template...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}Please review the .env file and adjust settings as needed${NC}"
else
    echo -e "${YELLOW}.env file already exists, skipping...${NC}"
fi

# Create data directories
echo -e "${GREEN}Creating data directories...${NC}"
mkdir -p data/uploads data/logs

echo -e "${GREEN}Setup complete!${NC}"
echo -e "${GREEN}To activate the virtual environment, run:${NC}"
echo -e "${YELLOW}source .venv/bin/activate${NC}"
echo -e "${GREEN}To run the application, run:${NC}"
echo -e "${YELLOW}./run.py${NC}"
echo -e "${GREEN}To run tests, run:${NC}"
echo -e "${YELLOW}pytest${NC}"
