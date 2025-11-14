#!/bin/bash
# Quick Start Script for Load Testing
# Sets up environment and runs a basic load test

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}=== Slide Speaker Load Testing - Quick Start ===${NC}\n"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}Python 3 is required but not installed.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python 3 found${NC}"

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo -e "${YELLOW}pip3 is required but not installed.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ pip3 found${NC}"

# Install requirements
echo -e "\n${BLUE}Installing load testing dependencies...${NC}"
pip3 install -q -r requirements.txt

echo -e "${GREEN}✓ Dependencies installed${NC}"

# Check if backend is running
echo -e "\n${BLUE}Checking if backend is accessible...${NC}"
if ! curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Backend is not accessible at http://localhost:8000${NC}"
    echo -e "${BLUE}Starting backend with docker-compose...${NC}"
    
    cd ../..
    docker-compose up -d backend postgres redis minio
    
    echo -e "${BLUE}Waiting for services to be ready...${NC}"
    sleep 15
    
    # Check again
    if ! curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${YELLOW}Backend still not accessible. Please start it manually:${NC}"
        echo "  docker-compose up -d"
        exit 1
    fi
fi

echo -e "${GREEN}✓ Backend is accessible${NC}"

# Create reports directory
mkdir -p reports

# Run a quick light load test
echo -e "\n${BLUE}Running light load test (10 users for 2 minutes)...${NC}\n"

cd /Users/iliazarikov/Documents/Python_crypto/Barahlo/slide-speaker-main/backend/load_tests

locust \
    -f locustfile.py \
    --headless \
    -u 10 \
    -r 2 \
    -t 2m \
    --host http://localhost:8000 \
    --html reports/quickstart_report.html \
    --csv reports/quickstart_results \
    --loglevel INFO

echo -e "\n${GREEN}=== Quick Start Test Complete! ===${NC}\n"
echo -e "${BLUE}View results:${NC}"
echo -e "  HTML Report: ${GREEN}reports/quickstart_report.html${NC}"
echo -e "  CSV Results: ${GREEN}reports/quickstart_results_*.csv${NC}"
echo -e "\n${BLUE}Next steps:${NC}"
echo -e "  1. Open the HTML report in your browser"
echo -e "  2. Review the README.md for more test scenarios"
echo -e "  3. Run heavier load tests: ${YELLOW}./run_load_tests.sh medium${NC}"
echo -e "  4. Generate test data: ${YELLOW}python3 generate_test_data.py${NC}"

# Open report in browser (macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "\n${BLUE}Opening report in browser...${NC}"
    open reports/quickstart_report.html
fi
