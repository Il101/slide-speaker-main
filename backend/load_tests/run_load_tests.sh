#!/bin/bash
# Load Testing Execution Script for Slide Speaker
# Usage: ./run_load_tests.sh [scenario] [host]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
SCENARIO="${1:-light}"
HOST="${2:-http://localhost:8000}"
REPORT_DIR="./reports/$(date +%Y%m%d_%H%M%S)_${SCENARIO}"

# Create reports directory
mkdir -p "$REPORT_DIR"

echo -e "${BLUE}=== Slide Speaker Load Testing ===${NC}"
echo -e "${BLUE}Scenario: ${YELLOW}${SCENARIO}${NC}"
echo -e "${BLUE}Target Host: ${YELLOW}${HOST}${NC}"
echo -e "${BLUE}Report Directory: ${YELLOW}${REPORT_DIR}${NC}"
echo ""

# Check if backend is accessible
echo -e "${BLUE}Checking backend availability...${NC}"
if curl -s -f "${HOST}/health" > /dev/null; then
    echo -e "${GREEN}✓ Backend is accessible${NC}"
else
    echo -e "${RED}✗ Backend is not accessible at ${HOST}${NC}"
    echo -e "${YELLOW}Please ensure the backend is running:${NC}"
    echo "  docker-compose up -d backend"
    exit 1
fi

# Check if locust is installed
if ! command -v locust &> /dev/null; then
    echo -e "${RED}✗ Locust is not installed${NC}"
    echo -e "${YELLOW}Installing locust...${NC}"
    pip install locust
fi

# Load test configuration
case $SCENARIO in
    light)
        USERS=10
        SPAWN_RATE=2
        RUN_TIME="5m"
        DESCRIPTION="Light load - Normal operation"
        ;;
    medium)
        USERS=50
        SPAWN_RATE=5
        RUN_TIME="10m"
        DESCRIPTION="Medium load - Peak hours"
        ;;
    heavy)
        USERS=100
        SPAWN_RATE=10
        RUN_TIME="15m"
        DESCRIPTION="Heavy load - High traffic"
        ;;
    stress)
        USERS=500
        SPAWN_RATE=50
        RUN_TIME="20m"
        DESCRIPTION="Stress test - Breaking point"
        ;;
    spike)
        USERS=200
        SPAWN_RATE=100
        RUN_TIME="5m"
        DESCRIPTION="Spike test - Sudden traffic increase"
        ;;
    endurance)
        USERS=30
        SPAWN_RATE=3
        RUN_TIME="2h"
        DESCRIPTION="Endurance test - Long running"
        ;;
    api-only)
        USERS=100
        SPAWN_RATE=20
        RUN_TIME="10m"
        DESCRIPTION="API-only test - No heavy operations"
        EXCLUDE_TAGS="--exclude-tags upload,export"
        ;;
    resource-intensive)
        USERS=20
        SPAWN_RATE=2
        RUN_TIME="15m"
        DESCRIPTION="Resource-intensive test - Uploads and exports"
        TAGS="--tags upload,export"
        ;;
    *)
        echo -e "${RED}Unknown scenario: ${SCENARIO}${NC}"
        echo "Available scenarios: light, medium, heavy, stress, spike, endurance, api-only, resource-intensive"
        exit 1
        ;;
esac

echo -e "${BLUE}Test Configuration:${NC}"
echo -e "  Description: ${DESCRIPTION}"
echo -e "  Users: ${USERS}"
echo -e "  Spawn Rate: ${SPAWN_RATE} users/sec"
echo -e "  Duration: ${RUN_TIME}"
echo ""

# Start monitoring (if available)
echo -e "${BLUE}Starting resource monitoring...${NC}"
./monitor_resources.sh "$REPORT_DIR" &
MONITOR_PID=$!

# Capture initial metrics
echo -e "${BLUE}Capturing baseline metrics...${NC}"
curl -s "${HOST}/metrics" > "${REPORT_DIR}/metrics_before.txt" || echo "Metrics endpoint not available"
curl -s "${HOST}/health/detailed" > "${REPORT_DIR}/health_before.json" || echo "Health endpoint not available"

# Run load test
echo -e "${GREEN}Starting load test...${NC}"
echo ""

cd "$(dirname "$0")"

locust \
    -f locustfile.py \
    --headless \
    -u "$USERS" \
    -r "$SPAWN_RATE" \
    -t "$RUN_TIME" \
    --host "$HOST" \
    --html "${REPORT_DIR}/report.html" \
    --csv "${REPORT_DIR}/results" \
    --logfile "${REPORT_DIR}/locust.log" \
    --loglevel INFO \
    ${TAGS:-} \
    ${EXCLUDE_TAGS:-} \
    2>&1 | tee "${REPORT_DIR}/output.log"

TEST_EXIT_CODE=$?

# Stop monitoring
kill $MONITOR_PID 2>/dev/null || true

# Capture final metrics
echo -e "${BLUE}Capturing final metrics...${NC}"
curl -s "${HOST}/metrics" > "${REPORT_DIR}/metrics_after.txt" || echo "Metrics endpoint not available"
curl -s "${HOST}/health/detailed" > "${REPORT_DIR}/health_after.json" || echo "Health endpoint not available"

# Generate summary report
echo -e "${BLUE}Generating summary report...${NC}"
python3 analyze_results.py "${REPORT_DIR}" > "${REPORT_DIR}/summary.txt"

# Display results
echo ""
echo -e "${BLUE}=== Test Results ===${NC}"
cat "${REPORT_DIR}/summary.txt"

echo ""
echo -e "${BLUE}=== Full Report ===${NC}"
echo -e "HTML Report: ${GREEN}${REPORT_DIR}/report.html${NC}"
echo -e "CSV Results: ${GREEN}${REPORT_DIR}/results_*.csv${NC}"
echo -e "Logs: ${GREEN}${REPORT_DIR}/locust.log${NC}"

# Check for failures
if [ $TEST_EXIT_CODE -ne 0 ]; then
    echo -e "${RED}✗ Load test failed with exit code ${TEST_EXIT_CODE}${NC}"
    exit $TEST_EXIT_CODE
fi

# Analyze results and check thresholds
echo ""
echo -e "${BLUE}Checking performance thresholds...${NC}"
python3 check_thresholds.py "${REPORT_DIR}/results_stats.csv"
THRESHOLD_EXIT_CODE=$?

if [ $THRESHOLD_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All performance thresholds met${NC}"
else
    echo -e "${YELLOW}⚠ Some performance thresholds exceeded${NC}"
fi

echo ""
echo -e "${GREEN}Load test completed successfully!${NC}"
echo -e "${BLUE}Open ${REPORT_DIR}/report.html in a browser to view detailed results${NC}"

exit 0
