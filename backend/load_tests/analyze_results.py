"""
Analyze Locust load test results and generate summary report
"""

import sys
import json
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


def read_csv_results(csv_path: str) -> List[Dict]:
    """Read Locust CSV results"""
    results = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
    return results


def analyze_stats(stats_csv: str) -> Dict[str, Any]:
    """Analyze statistics CSV"""
    stats = read_csv_results(stats_csv)
    
    analysis = {
        'total_requests': 0,
        'failed_requests': 0,
        'endpoints': []
    }
    
    for stat in stats:
        if stat['Name'] == 'Aggregated':
            analysis['total_requests'] = int(stat.get('Request Count', 0))
            analysis['failed_requests'] = int(stat.get('Failure Count', 0))
            analysis['error_rate'] = float(stat.get('Failure Count', 0)) / max(1, int(stat.get('Request Count', 1))) * 100
            analysis['avg_response_time'] = float(stat.get('Average Response Time', 0))
            analysis['p50'] = float(stat.get('50%', 0))
            analysis['p95'] = float(stat.get('95%', 0))
            analysis['p99'] = float(stat.get('99%', 0))
            analysis['max_response_time'] = float(stat.get('Max Response Time', 0))
            analysis['rps'] = float(stat.get('Requests/s', 0))
        else:
            endpoint = {
                'name': stat['Name'],
                'method': stat['Type'],
                'requests': int(stat.get('Request Count', 0)),
                'failures': int(stat.get('Failure Count', 0)),
                'avg_response': float(stat.get('Average Response Time', 0)),
                'p95': float(stat.get('95%', 0)),
                'rps': float(stat.get('Requests/s', 0))
            }
            analysis['endpoints'].append(endpoint)
    
    return analysis


def analyze_failures(failures_csv: str) -> List[Dict]:
    """Analyze failures CSV"""
    try:
        failures = read_csv_results(failures_csv)
        return failures
    except FileNotFoundError:
        return []


def read_resource_metrics(resource_csv: str) -> Dict[str, Any]:
    """Read and analyze resource monitoring data"""
    try:
        data = read_csv_results(resource_csv)
        if not data:
            return {}
        
        cpu_values = [float(row.get('cpu_percent', 0)) for row in data if row.get('cpu_percent')]
        memory_values = [float(row.get('memory_percent', 0)) for row in data if row.get('memory_percent')]
        
        return {
            'cpu': {
                'avg': sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                'max': max(cpu_values) if cpu_values else 0,
                'min': min(cpu_values) if cpu_values else 0
            },
            'memory': {
                'avg': sum(memory_values) / len(memory_values) if memory_values else 0,
                'max': max(memory_values) if memory_values else 0,
                'min': min(memory_values) if memory_values else 0
            }
        }
    except FileNotFoundError:
        return {}


def generate_summary_report(report_dir: str):
    """Generate comprehensive summary report"""
    report_path = Path(report_dir)
    
    print("=" * 80)
    print("LOAD TEST SUMMARY REPORT")
    print("=" * 80)
    print(f"Report Directory: {report_dir}")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Analyze statistics
    stats_file = report_path / "results_stats.csv"
    if stats_file.exists():
        print("PERFORMANCE METRICS")
        print("-" * 80)
        
        analysis = analyze_stats(str(stats_file))
        
        print(f"Total Requests: {analysis['total_requests']:,}")
        print(f"Failed Requests: {analysis['failed_requests']:,}")
        print(f"Error Rate: {analysis['error_rate']:.2f}%")
        print(f"Requests/Second: {analysis['rps']:.2f}")
        print()
        
        print("RESPONSE TIMES (ms)")
        print(f"  Average: {analysis['avg_response_time']:.2f}")
        print(f"  50th percentile (median): {analysis['p50']:.2f}")
        print(f"  95th percentile: {analysis['p95']:.2f}")
        print(f"  99th percentile: {analysis['p99']:.2f}")
        print(f"  Maximum: {analysis['max_response_time']:.2f}")
        print()
        
        # Top endpoints by request count
        print("TOP 10 ENDPOINTS BY REQUEST COUNT")
        print("-" * 80)
        sorted_endpoints = sorted(analysis['endpoints'], key=lambda x: x['requests'], reverse=True)[:10]
        for i, ep in enumerate(sorted_endpoints, 1):
            error_rate = (ep['failures'] / max(1, ep['requests'])) * 100
            print(f"{i}. {ep['name']}")
            print(f"   Requests: {ep['requests']:,} | Failures: {ep['failures']} ({error_rate:.2f}%)")
            print(f"   Avg Response: {ep['avg_response']:.2f}ms | P95: {ep['p95']:.2f}ms | RPS: {ep['rps']:.2f}")
        print()
        
        # Slowest endpoints
        print("TOP 5 SLOWEST ENDPOINTS (by P95)")
        print("-" * 80)
        slowest = sorted(analysis['endpoints'], key=lambda x: x['p95'], reverse=True)[:5]
        for i, ep in enumerate(slowest, 1):
            print(f"{i}. {ep['name']}: {ep['p95']:.2f}ms (avg: {ep['avg_response']:.2f}ms)")
        print()
    
    # Analyze failures
    failures_file = report_path / "results_failures.csv"
    if failures_file.exists():
        failures = analyze_failures(str(failures_file))
        if failures:
            print("FAILURES")
            print("-" * 80)
            print(f"Total Failure Types: {len(failures)}")
            for failure in failures[:10]:  # Top 10 failures
                print(f"  {failure.get('Name', 'Unknown')}: {failure.get('Occurrences', 0)} occurrences")
                print(f"    Error: {failure.get('Error', 'N/A')}")
            print()
    
    # Resource metrics
    resource_file = report_path / "system_resources.csv"
    if resource_file.exists():
        print("RESOURCE USAGE")
        print("-" * 80)
        resources = read_resource_metrics(str(resource_file))
        
        if resources:
            print("CPU Usage:")
            print(f"  Average: {resources['cpu']['avg']:.2f}%")
            print(f"  Maximum: {resources['cpu']['max']:.2f}%")
            print(f"  Minimum: {resources['cpu']['min']:.2f}%")
            print()
            
            print("Memory Usage:")
            print(f"  Average: {resources['memory']['avg']:.2f}%")
            print(f"  Maximum: {resources['memory']['max']:.2f}%")
            print(f"  Minimum: {resources['memory']['min']:.2f}%")
            print()
    
    # Recommendations
    print("RECOMMENDATIONS")
    print("-" * 80)
    
    if stats_file.exists():
        analysis = analyze_stats(str(stats_file))
        
        if analysis['error_rate'] > 5:
            print("⚠ HIGH ERROR RATE detected!")
            print("  - Review application logs for error patterns")
            print("  - Check database connection pool settings")
            print("  - Verify external API availability and rate limits")
            print()
        
        if analysis['p95'] > 1000:
            print("⚠ HIGH RESPONSE TIMES detected!")
            print("  - Review slow database queries")
            print("  - Implement caching for frequently accessed data")
            print("  - Consider scaling horizontally")
            print()
        
        if resources and resources['cpu']['max'] > 80:
            print("⚠ HIGH CPU USAGE detected!")
            print("  - Profile CPU-intensive operations")
            print("  - Optimize algorithmic complexity")
            print("  - Consider adding more CPU resources or horizontal scaling")
            print()
        
        if resources and resources['memory']['max'] > 85:
            print("⚠ HIGH MEMORY USAGE detected!")
            print("  - Check for memory leaks")
            print("  - Review caching strategies")
            print("  - Increase available memory or add memory limits")
            print()
        
        if analysis['error_rate'] < 1 and analysis['p95'] < 500:
            print("✓ Performance looks good!")
            print("  - Error rate is within acceptable limits")
            print("  - Response times are healthy")
            print("  - Continue monitoring in production")
    
    print()
    print("=" * 80)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_results.py <report_directory>")
        sys.exit(1)
    
    report_dir = sys.argv[1]
    generate_summary_report(report_dir)
