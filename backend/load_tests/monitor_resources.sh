#!/bin/bash
# Resource Monitoring Script for Load Testing
# Monitors CPU, memory, disk, database, and Redis during load tests

REPORT_DIR="${1:-.}"
INTERVAL=5  # seconds between measurements

echo "Starting resource monitoring (interval: ${INTERVAL}s)"
echo "Saving to: ${REPORT_DIR}"

# Create monitoring CSV files
SYSTEM_CSV="${REPORT_DIR}/system_resources.csv"
DOCKER_CSV="${REPORT_DIR}/docker_resources.csv"
DB_CSV="${REPORT_DIR}/database_metrics.csv"

# Headers
echo "timestamp,cpu_percent,memory_percent,disk_percent,load_avg_1m,load_avg_5m,load_avg_15m" > "$SYSTEM_CSV"
echo "timestamp,container,cpu_percent,memory_usage_mb,memory_limit_mb,memory_percent,network_rx_mb,network_tx_mb" > "$DOCKER_CSV"
echo "timestamp,active_connections,idle_connections,total_connections,transactions_committed,transactions_rolled_back" > "$DB_CSV"

# Monitor loop
while true; do
    TIMESTAMP=$(date +%s)
    
    # System resources
    if command -v mpstat &> /dev/null && command -v free &> /dev/null; then
        CPU=$(mpstat 1 1 | awk '/Average/ {print 100 - $NF}')
        MEMORY=$(free | awk '/Mem:/ {printf "%.2f", $3/$2 * 100}')
        DISK=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
        LOAD=$(uptime | awk -F'load average:' '{print $2}' | sed 's/,//g')
        
        echo "${TIMESTAMP},${CPU},${MEMORY},${DISK},${LOAD}" >> "$SYSTEM_CSV"
    fi
    
    # Docker container resources
    if command -v docker &> /dev/null; then
        docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}" | tail -n +2 | while read line; do
            CONTAINER=$(echo "$line" | awk '{print $1}')
            CPU_PERC=$(echo "$line" | awk '{print $2}' | sed 's/%//')
            MEM_USAGE=$(echo "$line" | awk '{print $3}' | sed 's/MiB//')
            MEM_LIMIT=$(echo "$line" | awk '{print $5}' | sed 's/GiB//' | awk '{print $1 * 1024}')
            MEM_PERC=$(echo "$line" | awk '{print $6}' | sed 's/%//')
            NET_RX=$(echo "$line" | awk '{print $7}' | sed 's/MB//')
            NET_TX=$(echo "$line" | awk '{print $9}' | sed 's/MB//')
            
            echo "${TIMESTAMP},${CONTAINER},${CPU_PERC},${MEM_USAGE},${MEM_LIMIT},${MEM_PERC},${NET_RX},${NET_TX}" >> "$DOCKER_CSV"
        done
    fi
    
    # Database metrics (if PostgreSQL is accessible)
    if command -v psql &> /dev/null; then
        DB_METRICS=$(psql -h localhost -U postgres -d slidespeaker -t -c "
            SELECT 
                (SELECT count(*) FROM pg_stat_activity WHERE state = 'active'),
                (SELECT count(*) FROM pg_stat_activity WHERE state = 'idle'),
                (SELECT count(*) FROM pg_stat_activity),
                (SELECT sum(xact_commit) FROM pg_stat_database),
                (SELECT sum(xact_rollback) FROM pg_stat_database)
        " 2>/dev/null)
        
        if [ -n "$DB_METRICS" ]; then
            echo "${TIMESTAMP},${DB_METRICS}" | tr -d ' ' | tr '|' ',' >> "$DB_CSV"
        fi
    fi
    
    sleep $INTERVAL
done
