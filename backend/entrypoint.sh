#!/bin/bash
set -e

# Create Prometheus multiprocess directory if it doesn't exist
mkdir -p /tmp/prometheus_multiproc_dir
chmod 777 /tmp/prometheus_multiproc_dir

# Execute the main command
exec "$@"

