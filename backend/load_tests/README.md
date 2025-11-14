# 📊 Load Testing Guide for Slide Speaker

Comprehensive guide for conducting performance and load testing to ensure scalability and reliability.

## 📋 Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Test Scenarios](#test-scenarios)
- [Running Tests](#running-tests)
- [Interpreting Results](#interpreting-results)
- [Performance Optimization](#performance-optimization)
- [Distributed Testing](#distributed-testing)
- [CI/CD Integration](#cicd-integration)

## 🎯 Overview

This load testing suite uses [Locust](https://locust.io/) to simulate realistic user behavior and measure application performance under various load conditions. The tests cover:

- ✅ API endpoint performance
- ✅ Authentication flows
- ✅ File upload and processing
- ✅ Video generation and export
- ✅ Database performance
- ✅ Resource utilization
- ✅ Scalability limits

## 📦 Prerequisites

### Required Software

```bash
# Python 3.10+
python --version

# Install Locust and dependencies
pip install locust requests

# For monitoring (optional)
pip install psutil docker
```

### Application Setup

Ensure the application is running:

```bash
# Start all services
docker-compose up -d

# Verify health
curl http://localhost:8000/health
```

## 🚀 Quick Start

### 1. Run a Basic Test

```bash
cd backend/load_tests

# Run light load test (10 users for 5 minutes)
./run_load_tests.sh light http://localhost:8000
```

### 2. View Results

Results are saved in `backend/load_tests/reports/YYYYMMDD_HHMMSS_<scenario>/`:
- `report.html` - Interactive HTML report
- `results_stats.csv` - Detailed statistics
- `summary.txt` - Summary and recommendations

### 3. Open HTML Report

```bash
# macOS
open reports/latest/report.html

# Linux
xdg-open reports/latest/report.html
```

## 🎪 Test Scenarios

### Light Load (Baseline)
**Use case:** Normal daily operation
```bash
./run_load_tests.sh light
```
- **Users:** 10 concurrent
- **Duration:** 5 minutes
- **Purpose:** Establish baseline performance

### Medium Load (Peak Hours)
**Use case:** Typical peak traffic
```bash
./run_load_tests.sh medium
```
- **Users:** 50 concurrent
- **Duration:** 10 minutes
- **Purpose:** Validate peak hour performance

### Heavy Load (High Traffic)
**Use case:** Marketing campaign or viral growth
```bash
./run_load_tests.sh heavy
```
- **Users:** 100 concurrent
- **Duration:** 15 minutes
- **Purpose:** Test system limits

### Stress Test (Breaking Point)
**Use case:** Find maximum capacity
```bash
./run_load_tests.sh stress
```
- **Users:** 500 concurrent
- **Duration:** 20 minutes
- **Purpose:** Identify breaking points and bottlenecks

### Spike Test (Traffic Surge)
**Use case:** Sudden viral event
```bash
./run_load_tests.sh spike
```
- **Users:** 200 (spawned rapidly)
- **Duration:** 5 minutes
- **Purpose:** Test rapid scaling capability

### Endurance Test (Stability)
**Use case:** Long-running production stability
```bash
./run_load_tests.sh endurance
```
- **Users:** 30 concurrent
- **Duration:** 2 hours
- **Purpose:** Detect memory leaks and gradual degradation

### API-Only Test
**Use case:** Test API performance without heavy operations
```bash
./run_load_tests.sh api-only
```
- **Users:** 100 concurrent
- **Duration:** 10 minutes
- **Purpose:** Isolate API performance from file processing

### Resource-Intensive Test
**Use case:** Test file processing pipeline
```bash
./run_load_tests.sh resource-intensive
```
- **Users:** 20 concurrent
- **Duration:** 15 minutes
- **Purpose:** Test upload, processing, and export operations

## 🏃 Running Tests

### Basic Command Line

```bash
# Syntax
./run_load_tests.sh <scenario> <host>

# Examples
./run_load_tests.sh light http://localhost:8000
./run_load_tests.sh heavy https://staging.example.com
```

### Using Locust Web UI (Interactive)

```bash
# Start Locust web interface
cd backend/load_tests
locust -f locustfile.py --host http://localhost:8000

# Open browser to http://localhost:8089
# Configure users and spawn rate in the UI
```

### Custom Parameters

```bash
# Custom user count and duration
locust -f locustfile.py \
    --headless \
    -u 75 \                    # 75 concurrent users
    -r 10 \                    # spawn 10 users per second
    -t 15m \                   # run for 15 minutes
    --host http://localhost:8000 \
    --html report.html
```

### Filtering Tests

```bash
# Run only specific user types
locust -f locustfile.py --tags browse --host http://localhost:8000

# Exclude heavy operations
locust -f locustfile.py --exclude-tags upload,export --host http://localhost:8000
```

## 📈 Interpreting Results

### Key Metrics

#### Response Times
- **P50 (Median):** 50% of requests complete within this time
  - Target: < 100ms for reads, < 200ms for writes
- **P95:** 95% of requests complete within this time
  - Target: < 500ms for reads, < 1000ms for writes
- **P99:** 99% of requests complete within this time
  - Target: < 1000ms for reads, < 3000ms for writes

#### Error Rate
- **Target:** < 1%
- **Warning:** 1-5%
- **Critical:** > 5%

#### Throughput
- **RPS (Requests Per Second):** Measure of system capacity
- Compare against baseline to track improvements

### Reading the HTML Report

The HTML report (`report.html`) includes:

1. **Statistics Tab:**
   - Request counts and failure rates
   - Response time percentiles
   - Requests per second

2. **Charts Tab:**
   - Response time over time
   - RPS over time
   - Number of users over time

3. **Failures Tab:**
   - Error messages and counts
   - Help identify issues

4. **Exceptions Tab:**
   - Unhandled exceptions
   - Stack traces for debugging

### CSV Data Analysis

```python
import pandas as pd

# Load statistics
stats = pd.read_csv('reports/latest/results_stats.csv')

# Find slowest endpoints
slowest = stats.nlargest(10, '95%')
print(slowest[['Name', 'Request Count', '95%', 'Requests/s']])

# Calculate overall health
error_rate = stats['Failure Count'].sum() / stats['Request Count'].sum() * 100
print(f"Overall error rate: {error_rate:.2f}%")
```

## ⚡ Performance Optimization

### Common Issues and Solutions

#### High Response Times

**Symptoms:**
- P95 > 1000ms
- Gradual slowdown over time

**Solutions:**
```python
# 1. Add database indexes
# backend/alembic/versions/xxx_add_indexes.py
op.create_index('ix_lessons_user_id', 'lessons', ['user_id'])
op.create_index('ix_lessons_created_at', 'lessons', ['created_at'])

# 2. Enable query result caching
from cachetools import TTLCache
cache = TTLCache(maxsize=1000, ttl=300)

# 3. Use database connection pooling
# backend/app/core/database.py
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,          # Increase pool
    max_overflow=10,
    pool_pre_ping=True
)
```

#### High Error Rate

**Symptoms:**
- Error rate > 1%
- Timeout errors

**Solutions:**
```python
# 1. Increase timeouts
# backend/app/core/config.py
API_TIMEOUT = 60  # seconds

# 2. Add retry logic
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def call_external_api():
    # API call here
    pass

# 3. Implement circuit breaker
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
async def external_service_call():
    # Service call here
    pass
```

#### High CPU Usage

**Symptoms:**
- CPU > 80%
- Slow processing

**Solutions:**
```bash
# 1. Scale Celery workers
docker-compose up -d --scale celery=4

# 2. Optimize CPU-intensive operations
# Use multiprocessing for parallel tasks

# 3. Profile code
pip install py-spy
py-spy top --pid <backend_pid>
```

#### High Memory Usage

**Symptoms:**
- Memory > 85%
- OOM errors

**Solutions:**
```python
# 1. Implement streaming for large files
from fastapi.responses import StreamingResponse

async def stream_file():
    async with aiofiles.open(file_path, 'rb') as f:
        while chunk := await f.read(8192):
            yield chunk

# 2. Add memory limits to Docker
# docker-compose.yml
services:
  backend:
    mem_limit: 4g
    mem_reservation: 2g

# 3. Implement pagination
@app.get("/lessons")
async def list_lessons(skip: int = 0, limit: int = 50):
    return await get_lessons(skip=skip, limit=limit)
```

#### Database Connection Issues

**Symptoms:**
- "Too many connections" errors
- Connection timeouts

**Solutions:**
```python
# 1. Increase PostgreSQL max connections
# docker-compose.yml
postgres:
  command: postgres -c max_connections=200

# 2. Implement connection pooling properly
# backend/app/core/database.py
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_timeout=30,
    pool_recycle=3600
)

# 3. Close connections properly
async with get_db() as db:
    # Use async context manager
    result = await db.execute(query)
```

### Caching Strategy

```python
# backend/app/services/cache.py
import redis.asyncio as redis
from functools import wraps

redis_client = redis.from_url("redis://localhost:6379")

def cache_result(ttl: int = 300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{args}:{kwargs}"
            
            # Try cache first
            cached = await redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Compute and cache
            result = await func(*args, **kwargs)
            await redis_client.setex(
                cache_key,
                ttl,
                json.dumps(result)
            )
            return result
        return wrapper
    return decorator

# Usage
@cache_result(ttl=600)
async def get_user_lessons(user_id: str):
    # Expensive database query
    return await db.execute(query)
```

## 🌐 Distributed Testing

### Master-Worker Setup

For testing with higher load, use distributed testing:

```bash
# Terminal 1: Start master
locust -f locustfile.py --master --host http://localhost:8000

# Terminal 2-N: Start workers
locust -f locustfile.py --worker --master-host localhost
locust -f locustfile.py --worker --master-host localhost
locust -f locustfile.py --worker --master-host localhost
```

### Docker-based Distributed Testing

```bash
# Use the provided docker-compose setup
cd backend/load_tests
docker-compose -f docker-compose.loadtest.yml up --scale worker=4
```

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/load-test.yml
name: Load Testing

on:
  push:
    branches: [main, staging]
  schedule:
    - cron: '0 2 * * 0'  # Weekly on Sunday at 2 AM

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install locust
      
      - name: Start application
        run: |
          docker-compose up -d
          sleep 30  # Wait for services
      
      - name: Run load tests
        run: |
          cd backend/load_tests
          ./run_load_tests.sh medium http://localhost:8000
      
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: load-test-results
          path: backend/load_tests/reports/
      
      - name: Check thresholds
        run: |
          cd backend/load_tests
          python check_thresholds.py reports/latest/results_stats.csv
```

## 📊 Monitoring Integration

### Prometheus Metrics

The application exposes metrics at `/metrics`:

```bash
# View current metrics
curl http://localhost:8000/metrics

# Key metrics to monitor:
# - http_requests_total
# - http_request_duration_seconds
# - celery_tasks_total
# - database_connections_total
```

### Grafana Dashboards

Import the provided dashboard:

```bash
# Access Grafana
open http://localhost:3001

# Import dashboard
# Dashboard → Import → Upload JSON
# File: monitoring/grafana/dashboards/load-testing.json
```

## 🎯 Performance Targets

### Response Time Targets

| Operation | P50 | P95 | P99 |
|-----------|-----|-----|-----|
| Health Check | < 50ms | < 200ms | < 500ms |
| API Read (GET) | < 100ms | < 500ms | < 1000ms |
| API Write (POST/PUT) | < 200ms | < 1000ms | < 3000ms |
| File Upload | < 2s | < 5s | < 10s |
| Video Export | < 30s | < 2m | < 5m |

### Scalability Targets

- **Concurrent Users:** Support 100+ concurrent users
- **Throughput:** Handle 50+ requests/second
- **Error Rate:** Maintain < 1% error rate
- **Availability:** 99.9% uptime (< 43 minutes downtime/month)

## 📚 Additional Resources

- [Locust Documentation](https://docs.locust.io/)
- [FastAPI Performance Tips](https://fastapi.tiangolo.com/deployment/concepts/)
- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [Redis Best Practices](https://redis.io/topics/optimization)

## 🆘 Troubleshooting

### Locust Won't Start

```bash
# Check Python version
python --version  # Should be 3.10+

# Reinstall Locust
pip uninstall locust
pip install locust

# Check for port conflicts
lsof -i :8089  # Locust web UI port
```

### Backend Not Responding

```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs backend

# Restart services
docker-compose restart backend
```

### Out of Memory During Tests

```bash
# Reduce concurrent users
./run_load_tests.sh light  # Start with light load

# Increase Docker memory
# Docker Desktop → Settings → Resources → Memory: 8GB

# Monitor resources
docker stats
```

## 📝 Best Practices

1. **Start Small:** Begin with light load and gradually increase
2. **Monitor Resources:** Watch CPU, memory, and disk during tests
3. **Test Incrementally:** Test individual components before full system
4. **Use Realistic Data:** Create test data that matches production
5. **Regular Testing:** Run load tests weekly or before major releases
6. **Document Baselines:** Keep records of baseline performance
7. **Test in Staging:** Never run heavy load tests in production
8. **Analyze Failures:** Investigate all errors, even if < 1%

---

**Created:** 2025-10-31  
**Version:** 1.0  
**Maintainer:** DevOps Team
