# Load Testing Examples and Use Cases

This document provides practical examples for different load testing scenarios.

## 📚 Table of Contents
- [Basic Examples](#basic-examples)
- [Advanced Scenarios](#advanced-scenarios)
- [Custom Test Creation](#custom-test-creation)
- [Result Analysis](#result-analysis)
- [Production Testing](#production-testing)

## Basic Examples

### Example 1: First Time Setup and Test

```bash
# 1. Navigate to load tests directory
cd backend/load_tests

# 2. Run validation
python3 validate_setup.py

# 3. Install dependencies if needed
pip3 install -r requirements.txt

# 4. Start the application
cd ../..
docker-compose up -d

# 5. Wait for services to be ready
sleep 15

# 6. Run quick test
cd backend/load_tests
./quickstart.sh
```

### Example 2: Testing Specific Features

```bash
# Test only authentication endpoints
locust -f locustfile.py \
    --headless \
    -u 20 \
    -r 5 \
    -t 3m \
    --host http://localhost:8000 \
    --tags auth

# Test only file operations (exclude video export)
locust -f locustfile.py \
    --headless \
    -u 10 \
    -r 2 \
    -t 5m \
    --host http://localhost:8000 \
    --tags upload \
    --exclude-tags export
```

### Example 3: Progressive Load Testing

```bash
# Step 1: Establish baseline with light load
./run_load_tests.sh light http://localhost:8000

# Step 2: Increase to medium load
./run_load_tests.sh medium http://localhost:8000

# Step 3: Test with heavy load
./run_load_tests.sh heavy http://localhost:8000

# Compare results
python3 << EOF
import pandas as pd
import glob

reports = sorted(glob.glob('reports/*/results_stats.csv'))[-3:]
for report in reports:
    df = pd.read_csv(report)
    agg = df[df['Name'] == 'Aggregated'].iloc[0]
    print(f"{report}:")
    print(f"  RPS: {agg['Requests/s']:.2f}")
    print(f"  P95: {agg['95%']:.2f}ms")
    print(f"  Error Rate: {float(agg['Failure Count'])/float(agg['Request Count'])*100:.2f}%")
    print()
EOF
```

## Advanced Scenarios

### Example 4: Stress Testing with Monitoring

```bash
# Terminal 1: Start application with resource limits
docker-compose up -d

# Terminal 2: Start monitoring
cd backend/load_tests
./monitor_resources.sh ./reports/stress_test &
MONITOR_PID=$!

# Terminal 3: Run stress test
./run_load_tests.sh stress http://localhost:8000

# Stop monitoring
kill $MONITOR_PID

# Analyze resource usage
python3 << EOF
import pandas as pd
df = pd.read_csv('reports/stress_test/system_resources.csv')
print("CPU Usage:")
print(f"  Average: {df['cpu_percent'].mean():.2f}%")
print(f"  Maximum: {df['cpu_percent'].max():.2f}%")
print("\nMemory Usage:")
print(f"  Average: {df['memory_percent'].mean():.2f}%")
print(f"  Maximum: {df['memory_percent'].max():.2f}%")
EOF
```

### Example 5: Distributed Load Testing

```bash
# Using Docker Compose for distributed testing
cd backend/load_tests

# Start with 8 workers
TARGET_HOST=http://host.docker.internal:8000 \
docker-compose -f docker-compose.loadtest.yml up -d --scale worker=8

# Open web UI
open http://localhost:8089

# Configure in UI:
# - Number of users: 500
# - Spawn rate: 50
# - Host: http://host.docker.internal:8000

# Stop when done
docker-compose -f docker-compose.loadtest.yml down
```

### Example 6: Endurance Testing with Continuous Monitoring

```bash
# Run 2-hour endurance test with monitoring
./run_load_tests.sh endurance http://localhost:8000 &
TEST_PID=$!

# Monitor every 5 minutes
while kill -0 $TEST_PID 2>/dev/null; do
    echo "$(date): Test running..."
    curl -s http://localhost:8000/metrics | grep -E "http_requests_total|http_request_duration"
    sleep 300
done

echo "Test completed"
```

## Custom Test Creation

### Example 7: Creating a Custom User Behavior

```python
# Add to locustfile.py

class CustomWorkflowUser(AuthenticatedUser, HttpUser):
    """Custom user workflow for specific feature testing"""
    
    weight = 3
    wait_time = between(5, 10)
    
    @task(1)
    def complete_workflow(self):
        """Test complete workflow: upload -> process -> export"""
        
        # Step 1: Upload
        files = {
            'file': ('test.pptx', b'content', 'application/vnd.openxmlformats-officedocument.presentationml.presentation')
        }
        
        response = self.client.post(
            "/upload",
            files=files,
            headers=self.headers,
            name="[Custom] Upload"
        )
        
        if response.status_code != 200:
            return
        
        lesson_id = response.json().get("lesson_id")
        
        # Step 2: Wait for processing
        for _ in range(10):
            time.sleep(2)
            status_resp = self.client.get(
                f"/lessons/{lesson_id}/status",
                headers=self.headers,
                name="[Custom] Check Status"
            )
            if status_resp.json().get("status") == "ready":
                break
        
        # Step 3: Export
        self.client.post(
            f"/lessons/{lesson_id}/export",
            json={"format": "mp4"},
            headers=self.headers,
            name="[Custom] Export"
        )
```

### Example 8: Custom Load Pattern

```python
# Create custom_load.py

from locust import HttpUser, task, LoadTestShape

class CustomLoadShape(LoadTestShape):
    """
    Custom load shape that gradually increases load, plateaus, then decreases
    """
    
    stages = [
        {"duration": 60, "users": 10, "spawn_rate": 2},   # Ramp up
        {"duration": 180, "users": 50, "spawn_rate": 5},  # Plateau
        {"duration": 240, "users": 100, "spawn_rate": 10}, # Peak
        {"duration": 300, "users": 50, "spawn_rate": 10}, # Decrease
        {"duration": 360, "users": 10, "spawn_rate": 5},  # Cool down
    ]
    
    def tick(self):
        run_time = self.get_run_time()
        
        for stage in self.stages:
            if run_time < stage["duration"]:
                return (stage["users"], stage["spawn_rate"])
        
        return None
```

## Result Analysis

### Example 9: Comparing Multiple Test Runs

```python
# compare_results.py

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

def compare_test_runs(report_dirs):
    """Compare metrics across multiple test runs"""
    
    results = []
    
    for report_dir in report_dirs:
        csv_path = Path(report_dir) / "results_stats.csv"
        df = pd.read_csv(csv_path)
        agg = df[df['Name'] == 'Aggregated'].iloc[0]
        
        results.append({
            'test': report_dir.split('/')[-1],
            'rps': float(agg['Requests/s']),
            'p50': float(agg['50%']),
            'p95': float(agg['95%']),
            'p99': float(agg['99%']),
            'error_rate': float(agg['Failure Count']) / float(agg['Request Count']) * 100
        })
    
    df_results = pd.DataFrame(results)
    
    # Plot comparison
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # RPS comparison
    axes[0, 0].bar(df_results['test'], df_results['rps'])
    axes[0, 0].set_title('Requests Per Second')
    axes[0, 0].set_ylabel('RPS')
    
    # Response times
    axes[0, 1].plot(df_results['test'], df_results['p50'], label='P50', marker='o')
    axes[0, 1].plot(df_results['test'], df_results['p95'], label='P95', marker='s')
    axes[0, 1].plot(df_results['test'], df_results['p99'], label='P99', marker='^')
    axes[0, 1].set_title('Response Times')
    axes[0, 1].set_ylabel('Time (ms)')
    axes[0, 1].legend()
    
    # Error rates
    axes[1, 0].bar(df_results['test'], df_results['error_rate'])
    axes[1, 0].set_title('Error Rate')
    axes[1, 0].set_ylabel('Error Rate (%)')
    axes[1, 0].axhline(y=1, color='r', linestyle='--', label='Threshold')
    axes[1, 0].legend()
    
    plt.tight_layout()
    plt.savefig('comparison.png')
    print("Comparison chart saved to comparison.png")
    
    return df_results

# Usage
report_dirs = [
    'reports/20250131_100000_light',
    'reports/20250131_110000_medium',
    'reports/20250131_120000_heavy',
]

results = compare_test_runs(report_dirs)
print(results)
```

### Example 10: Identifying Bottlenecks

```bash
# Run test and analyze bottlenecks
./run_load_tests.sh heavy http://localhost:8000

# Extract slowest endpoints
python3 << EOF
import pandas as pd
import glob

latest_report = sorted(glob.glob('reports/*/results_stats.csv'))[-1]
df = pd.read_csv(latest_report)

# Filter out aggregated row
df = df[df['Name'] != 'Aggregated']

# Find slowest endpoints by P95
slowest = df.nlargest(10, '95%')

print("Top 10 Slowest Endpoints (P95):")
print("=" * 80)
for idx, row in slowest.iterrows():
    print(f"{row['Name']}")
    print(f"  P95: {row['95%']:.2f}ms")
    print(f"  Average: {row['Average Response Time']:.2f}ms")
    print(f"  Requests: {row['Request Count']}")
    print(f"  Failures: {row['Failure Count']}")
    print()
EOF
```

## Production Testing

### Example 11: Safe Production Load Testing

```bash
# NEVER run heavy tests in production!
# Use gradual approach with monitoring

# 1. Test with minimal load
locust -f locustfile.py \
    --headless \
    -u 5 \
    -r 1 \
    -t 2m \
    --host https://production.example.com \
    --html prod_test_5users.html

# 2. Monitor for issues
# Check application metrics, errors, database

# 3. Gradually increase if no issues
locust -f locustfile.py \
    --headless \
    -u 10 \
    -r 2 \
    -t 5m \
    --host https://production.example.com \
    --html prod_test_10users.html

# 4. Always have rollback plan ready
```

### Example 12: A/B Performance Testing

```bash
# Test two different configurations

# Configuration A (current)
./run_load_tests.sh medium http://config-a:8000

# Configuration B (new)
./run_load_tests.sh medium http://config-b:8000

# Compare results
python3 << EOF
import pandas as pd

config_a = pd.read_csv('reports/config_a/results_stats.csv')
config_b = pd.read_csv('reports/config_b/results_stats.csv')

agg_a = config_a[config_a['Name'] == 'Aggregated'].iloc[0]
agg_b = config_b[config_b['Name'] == 'Aggregated'].iloc[0]

print("Configuration Comparison:")
print(f"Metric          | Config A    | Config B    | Change")
print("-" * 60)

rps_a = float(agg_a['Requests/s'])
rps_b = float(agg_b['Requests/s'])
print(f"RPS             | {rps_a:10.2f} | {rps_b:10.2f} | {(rps_b-rps_a)/rps_a*100:+.1f}%")

p95_a = float(agg_a['95%'])
p95_b = float(agg_b['95%'])
print(f"P95 (ms)        | {p95_a:10.2f} | {p95_b:10.2f} | {(p95_b-p95_a)/p95_a*100:+.1f}%")

err_a = float(agg_a['Failure Count']) / float(agg_a['Request Count']) * 100
err_b = float(agg_b['Failure Count']) / float(agg_b['Request Count']) * 100
print(f"Error Rate (%)  | {err_a:10.2f} | {err_b:10.2f} | {(err_b-err_a):+.2f}pp")
EOF
```

## Tips and Best Practices

### 1. Always Start Small
```bash
# Don't jump to stress testing immediately
./run_load_tests.sh light    # Start here
./run_load_tests.sh medium   # Then this
./run_load_tests.sh heavy    # Finally this
```

### 2. Monitor During Tests
```bash
# Watch metrics in real-time
watch -n 5 'curl -s http://localhost:8000/metrics | grep -E "http_requests_total|memory_usage"'
```

### 3. Test Against Staging First
```bash
# Never test production without testing staging
./run_load_tests.sh heavy https://staging.example.com
# Review results carefully
# Then cautiously test production with minimal load
```

### 4. Document Baselines
```bash
# Save baseline results
./run_load_tests.sh medium http://localhost:8000
cp -r reports/latest reports/baseline_v1.0
git add reports/baseline_v1.0
git commit -m "Add performance baseline for v1.0"
```

### 5. Automate Regular Testing
```bash
# Add to cron for weekly testing
0 2 * * 0 cd /path/to/project/backend/load_tests && ./run_load_tests.sh medium http://localhost:8000
```

---

**Remember:** Load testing is about learning, not just numbers. Always analyze results and use insights to improve your application!
