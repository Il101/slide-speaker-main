"""
Check if performance metrics meet defined thresholds
"""

import sys
import csv
from pathlib import Path
from config import PERFORMANCE_THRESHOLDS


def read_stats_csv(csv_path: str):
    """Read statistics from Locust CSV"""
    stats = {}
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['Name'] == 'Aggregated':
                stats = {
                    'p50': float(row.get('50%', 0)),
                    'p95': float(row.get('95%', 0)),
                    'p99': float(row.get('99%', 0)),
                    'error_rate': (float(row.get('Failure Count', 0)) / max(1, float(row.get('Request Count', 1)))) * 100,
                    'rps': float(row.get('Requests/s', 0))
                }
    return stats


def categorize_endpoint(name: str) -> str:
    """Categorize endpoint by operation type"""
    if 'health' in name.lower():
        return 'health_check'
    elif 'upload' in name.lower():
        return 'file_upload'
    elif 'export' in name.lower():
        return 'video_export'
    elif any(method in name for method in ['GET', 'List', 'Browse']):
        return 'api_read'
    else:
        return 'api_write'


def check_thresholds(stats_csv_path: str) -> bool:
    """Check if metrics meet thresholds"""
    stats = read_stats_csv(stats_csv_path)
    
    all_passed = True
    
    print("\n" + "=" * 80)
    print("PERFORMANCE THRESHOLD VALIDATION")
    print("=" * 80 + "\n")
    
    # Check error rate
    print(f"Error Rate: {stats['error_rate']:.2f}%")
    if stats['error_rate'] > PERFORMANCE_THRESHOLDS['max_error_rate']:
        print(f"  ✗ FAILED: Exceeds threshold of {PERFORMANCE_THRESHOLDS['max_error_rate']}%")
        all_passed = False
    else:
        print(f"  ✓ PASSED: Below threshold of {PERFORMANCE_THRESHOLDS['max_error_rate']}%")
    print()
    
    # Check response times (using API write as general category)
    category = 'api_write'
    thresholds = PERFORMANCE_THRESHOLDS[category]
    
    print("Response Times:")
    
    # P50
    print(f"  50th percentile: {stats['p50']:.2f}ms")
    if stats['p50'] > thresholds['p50']:
        print(f"    ⚠ WARNING: Exceeds threshold of {thresholds['p50']}ms")
        # Warning, not a failure
    else:
        print(f"    ✓ PASSED: Below threshold of {thresholds['p50']}ms")
    
    # P95
    print(f"  95th percentile: {stats['p95']:.2f}ms")
    if stats['p95'] > thresholds['p95']:
        print(f"    ✗ FAILED: Exceeds threshold of {thresholds['p95']}ms")
        all_passed = False
    else:
        print(f"    ✓ PASSED: Below threshold of {thresholds['p95']}ms")
    
    # P99
    print(f"  99th percentile: {stats['p99']:.2f}ms")
    if stats['p99'] > thresholds['p99']:
        print(f"    ✗ FAILED: Exceeds threshold of {thresholds['p99']}ms")
        all_passed = False
    else:
        print(f"    ✓ PASSED: Below threshold of {thresholds['p99']}ms")
    
    print()
    
    # Overall result
    print("=" * 80)
    if all_passed:
        print("RESULT: ✓ ALL THRESHOLDS PASSED")
    else:
        print("RESULT: ✗ SOME THRESHOLDS FAILED")
    print("=" * 80 + "\n")
    
    return all_passed


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_thresholds.py <stats_csv_path>")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    
    if not Path(csv_path).exists():
        print(f"Error: File not found: {csv_path}")
        sys.exit(1)
    
    passed = check_thresholds(csv_path)
    sys.exit(0 if passed else 1)
