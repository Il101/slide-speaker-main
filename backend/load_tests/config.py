"""
Load Testing Configuration for Different Scenarios
"""

# Light Load - Normal operation
LIGHT_LOAD = {
    "users": 10,
    "spawn_rate": 2,
    "run_time": "5m",
    "description": "Simulates normal daily traffic with 10 concurrent users"
}

# Medium Load - Peak hours
MEDIUM_LOAD = {
    "users": 50,
    "spawn_rate": 5,
    "run_time": "10m",
    "description": "Simulates peak hours with 50 concurrent users"
}

# Heavy Load - High traffic
HEAVY_LOAD = {
    "users": 100,
    "spawn_rate": 10,
    "run_time": "15m",
    "description": "Simulates heavy traffic with 100 concurrent users"
}

# Stress Test - Breaking point
STRESS_TEST = {
    "users": 500,
    "spawn_rate": 50,
    "run_time": "20m",
    "description": "Stress test to find breaking point with 500 concurrent users"
}

# Spike Test - Sudden traffic increase
SPIKE_TEST = {
    "users": 200,
    "spawn_rate": 100,  # Spawn all users quickly
    "run_time": "5m",
    "description": "Spike test with sudden increase to 200 users"
}

# Endurance Test - Long-running
ENDURANCE_TEST = {
    "users": 30,
    "spawn_rate": 3,
    "run_time": "2h",
    "description": "Endurance test with 30 users over 2 hours"
}

# API-only test (no file uploads)
API_ONLY_TEST = {
    "users": 100,
    "spawn_rate": 20,
    "run_time": "10m",
    "description": "API-focused test without heavy file operations",
    "exclude_classes": ["ContentCreatorUser", "VideoExportUser"]
}

# Resource-intensive test (file uploads and processing)
RESOURCE_INTENSIVE_TEST = {
    "users": 20,
    "spawn_rate": 2,
    "run_time": "15m",
    "description": "Resource-intensive operations (uploads, processing, exports)",
    "user_classes": ["ContentCreatorUser", "VideoExportUser"]
}

# Performance thresholds
PERFORMANCE_THRESHOLDS = {
    # Response time thresholds (in milliseconds)
    "health_check": {
        "p50": 50,
        "p95": 200,
        "p99": 500
    },
    "api_read": {  # GET requests
        "p50": 100,
        "p95": 500,
        "p99": 1000
    },
    "api_write": {  # POST/PUT/PATCH requests
        "p50": 200,
        "p95": 1000,
        "p99": 3000
    },
    "file_upload": {
        "p50": 2000,
        "p95": 5000,
        "p99": 10000
    },
    "video_export": {
        "p50": 30000,  # 30 seconds
        "p95": 120000,  # 2 minutes
        "p99": 300000   # 5 minutes
    },
    # Error rate thresholds (percentage)
    "max_error_rate": 1.0,  # 1% maximum error rate
    
    # Throughput thresholds (requests per second)
    "min_throughput": {
        "health_check": 100,
        "api_read": 50,
        "api_write": 20
    }
}

# Resource monitoring thresholds
RESOURCE_THRESHOLDS = {
    "cpu_percent": 80,  # Maximum CPU usage
    "memory_percent": 85,  # Maximum memory usage
    "disk_usage_percent": 90,  # Maximum disk usage
    "database_connections": 90,  # Maximum percentage of DB pool
    "redis_memory_usage_percent": 80,  # Maximum Redis memory
    "celery_queue_length": 100  # Maximum queue length
}

# Test data configuration
TEST_DATA = {
    "test_users_count": 100,  # Number of test users to create
    "test_presentations": [
        {
            "name": "small_presentation.pptx",
            "slides": 5,
            "size_kb": 100
        },
        {
            "name": "medium_presentation.pptx",
            "slides": 20,
            "size_kb": 500
        },
        {
            "name": "large_presentation.pptx",
            "slides": 50,
            "size_kb": 2000
        }
    ]
}

# Locust command templates
LOCUST_COMMANDS = {
    "light": "locust -f locustfile.py --headless -u {users} -r {spawn_rate} -t {run_time} --host {host}",
    "web_ui": "locust -f locustfile.py --host {host}",
    "distributed_master": "locust -f locustfile.py --master --host {host}",
    "distributed_worker": "locust -f locustfile.py --worker --master-host {master_host}"
}
