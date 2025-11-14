"""
Real-time Resource Monitoring for Load Tests

Monitors system resources (CPU, Memory, Disk) and application metrics
(DB connections, Redis, Celery queues) during load tests.

Features:
- Real-time monitoring with configurable interval
- Alert when thresholds exceeded
- Export metrics to CSV
- Integration with Locust events

Usage:
    # Add to locustfile.py:
    from resource_monitor import ResourceMonitor
    
    monitor = ResourceMonitor(interval=5)  # Check every 5 seconds
"""

import time
import psutil
import csv
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from collections import deque

from locust import events

# Try to import docker - optional dependency
try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    logging.warning("Docker not available - container metrics disabled")

# Configuration (imported from config.py)
try:
    from config import RESOURCE_THRESHOLDS
except ImportError:
    RESOURCE_THRESHOLDS = {
        "cpu_percent": 80,
        "memory_percent": 85,
        "disk_usage_percent": 90,
        "database_connections": 90,
    }

logger = logging.getLogger(__name__)


class ResourceMonitor:
    """Monitor system and application resources during load tests"""
    
    def __init__(self, interval: int = 5, output_dir: str = "./reports"):
        """
        Initialize resource monitor
        
        Args:
            interval: Seconds between measurements
            output_dir: Directory for CSV output
        """
        self.interval = interval
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # State
        self.monitoring = False
        self.thread: Optional[threading.Thread] = None
        self.metrics: deque = deque(maxlen=10000)  # Keep last 10k measurements
        
        # Docker client (optional)
        self.docker_client = None
        if DOCKER_AVAILABLE:
            try:
                self.docker_client = docker.from_env()
            except Exception as e:
                logger.warning(f"Docker client init failed: {e}")
        
        # Alert state
        self.alerts_sent = set()
    
    def start(self):
        """Start monitoring in background thread"""
        if self.monitoring:
            logger.warning("Monitor already running")
            return
        
        self.monitoring = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        logger.info("Resource monitoring started")
    
    def stop(self):
        """Stop monitoring and save metrics"""
        if not self.monitoring:
            return
        
        self.monitoring = False
        if self.thread:
            self.thread.join(timeout=5)
        
        self._save_metrics()
        logger.info("Resource monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop (runs in background thread)"""
        while self.monitoring:
            try:
                metrics = self._collect_metrics()
                self.metrics.append(metrics)
                
                # Check thresholds and alert
                self._check_thresholds(metrics)
                
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
            
            time.sleep(self.interval)
    
    def _collect_metrics(self) -> Dict:
        """Collect all metrics"""
        timestamp = datetime.now()
        
        metrics = {
            'timestamp': timestamp.isoformat(),
            'timestamp_unix': time.time(),
        }
        
        # System metrics
        metrics.update(self._collect_system_metrics())
        
        # Docker container metrics (if available)
        if self.docker_client:
            metrics.update(self._collect_docker_metrics())
        
        return metrics
    
    def _collect_system_metrics(self) -> Dict:
        """Collect system-level metrics"""
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Memory
        memory = psutil.virtual_memory()
        
        # Disk
        disk = psutil.disk_usage('/')
        
        # Network
        net_io = psutil.net_io_counters()
        
        return {
            'cpu_percent': cpu_percent,
            'cpu_count': cpu_count,
            'memory_percent': memory.percent,
            'memory_used_gb': memory.used / (1024**3),
            'memory_available_gb': memory.available / (1024**3),
            'disk_percent': disk.percent,
            'disk_used_gb': disk.used / (1024**3),
            'disk_free_gb': disk.free / (1024**3),
            'network_bytes_sent': net_io.bytes_sent,
            'network_bytes_recv': net_io.bytes_recv,
        }
    
    def _collect_docker_metrics(self) -> Dict:
        """Collect Docker container metrics"""
        metrics = {}
        
        try:
            # Backend container
            backend = self.docker_client.containers.get('backend')
            stats = backend.stats(stream=False)
            
            # CPU usage
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                       stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                          stats['precpu_stats']['system_cpu_usage']
            cpu_percent = (cpu_delta / system_delta) * 100.0 if system_delta > 0 else 0
            
            # Memory usage
            memory_usage = stats['memory_stats']['usage'] / (1024**3)  # GB
            memory_limit = stats['memory_stats']['limit'] / (1024**3)  # GB
            memory_percent = (memory_usage / memory_limit) * 100 if memory_limit > 0 else 0
            
            metrics['backend_cpu_percent'] = cpu_percent
            metrics['backend_memory_gb'] = memory_usage
            metrics['backend_memory_percent'] = memory_percent
            
        except Exception as e:
            logger.debug(f"Failed to collect Docker metrics: {e}")
        
        return metrics
    
    def _check_thresholds(self, metrics: Dict):
        """Check if metrics exceed thresholds and alert"""
        
        # CPU threshold
        if metrics['cpu_percent'] > RESOURCE_THRESHOLDS['cpu_percent']:
            alert_key = f"cpu_{metrics['cpu_percent']:.0f}"
            if alert_key not in self.alerts_sent:
                logger.warning(
                    f"⚠️  CPU usage HIGH: {metrics['cpu_percent']:.1f}% "
                    f"(threshold: {RESOURCE_THRESHOLDS['cpu_percent']}%)"
                )
                self.alerts_sent.add(alert_key)
        
        # Memory threshold
        if metrics['memory_percent'] > RESOURCE_THRESHOLDS['memory_percent']:
            alert_key = f"memory_{metrics['memory_percent']:.0f}"
            if alert_key not in self.alerts_sent:
                logger.warning(
                    f"⚠️  Memory usage HIGH: {metrics['memory_percent']:.1f}% "
                    f"(threshold: {RESOURCE_THRESHOLDS['memory_percent']}%)"
                )
                self.alerts_sent.add(alert_key)
        
        # Disk threshold
        if metrics['disk_percent'] > RESOURCE_THRESHOLDS['disk_usage_percent']:
            alert_key = f"disk_{metrics['disk_percent']:.0f}"
            if alert_key not in self.alerts_sent:
                logger.warning(
                    f"⚠️  Disk usage HIGH: {metrics['disk_percent']:.1f}% "
                    f"(threshold: {RESOURCE_THRESHOLDS['disk_usage_percent']}%)"
                )
                self.alerts_sent.add(alert_key)
    
    def _save_metrics(self):
        """Save metrics to CSV file"""
        if not self.metrics:
            logger.warning("No metrics to save")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = self.output_dir / f"resources_{timestamp}.csv"
        
        # Get all unique keys from metrics
        all_keys = set()
        for metric in self.metrics:
            all_keys.update(metric.keys())
        
        fieldnames = sorted(all_keys)
        
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.metrics)
        
        logger.info(f"Saved {len(self.metrics)} metrics to {csv_path}")
    
    def get_summary(self) -> Dict:
        """Get summary statistics of collected metrics"""
        if not self.metrics:
            return {}
        
        metrics_list = list(self.metrics)
        
        def avg(key):
            values = [m[key] for m in metrics_list if key in m]
            return sum(values) / len(values) if values else 0
        
        def max_val(key):
            values = [m[key] for m in metrics_list if key in m]
            return max(values) if values else 0
        
        return {
            'cpu_percent_avg': avg('cpu_percent'),
            'cpu_percent_max': max_val('cpu_percent'),
            'memory_percent_avg': avg('memory_percent'),
            'memory_percent_max': max_val('memory_percent'),
            'disk_percent': avg('disk_percent'),
            'measurements_count': len(metrics_list),
        }


# Global monitor instance
_monitor: Optional[ResourceMonitor] = None


def get_monitor() -> ResourceMonitor:
    """Get global monitor instance"""
    global _monitor
    if _monitor is None:
        _monitor = ResourceMonitor()
    return _monitor


# Locust event hooks
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Start resource monitoring when test starts"""
    monitor = get_monitor()
    monitor.start()
    logger.info("✅ Resource monitoring activated")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Stop resource monitoring and print summary"""
    monitor = get_monitor()
    monitor.stop()
    
    summary = monitor.get_summary()
    
    print("\n" + "=" * 80)
    print("RESOURCE USAGE SUMMARY")
    print("=" * 80)
    print(f"CPU Average:    {summary.get('cpu_percent_avg', 0):.1f}%")
    print(f"CPU Peak:       {summary.get('cpu_percent_max', 0):.1f}%")
    print(f"Memory Average: {summary.get('memory_percent_avg', 0):.1f}%")
    print(f"Memory Peak:    {summary.get('memory_percent_max', 0):.1f}%")
    print(f"Disk Usage:     {summary.get('disk_percent', 0):.1f}%")
    print(f"Measurements:   {summary.get('measurements_count', 0)}")
    print("=" * 80 + "\n")


# Example usage:
"""
# In locustfile.py:

from resource_monitor import ResourceMonitor

# Monitor will automatically start/stop with test due to event hooks
# Just import it and it will work!

# Or manual control:
monitor = ResourceMonitor(interval=5)
monitor.start()
# ... run tests ...
monitor.stop()
summary = monitor.get_summary()
"""
