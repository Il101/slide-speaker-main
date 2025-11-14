#!/bin/bash
set -e

# Create Prometheus multiprocess directory if it doesn't exist
# Use -m to set permissions during creation to avoid permission issues
mkdir -p /tmp/prometheus_multiproc_dir || true
chmod 777 /tmp/prometheus_multiproc_dir 2>/dev/null || true

# Execute the main command
exec "$@"

