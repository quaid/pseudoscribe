"""
Performance Monitor
Provides real-time performance monitoring and metrics collection
"""

import time
import threading
import psutil
from typing import Dict, Any, Optional, ContextManager
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Data class for performance metrics"""
    cpu_usage: float = 0.0
    memory_usage: Dict[str, Any] = field(default_factory=dict)
    response_times: Dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    active_connections: int = 0
    request_count: int = 0


class PerformanceMonitor:
    """
    Real-time performance monitoring system
    Tracks CPU, memory, response times, and other performance metrics
    """
    
    def __init__(self):
        self._monitoring = False
        self._metrics = PerformanceMetrics()
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._response_times: Dict[str, list] = {}
        self._start_time = time.time()
        
    def start_monitoring(self) -> None:
        """Start performance monitoring in background thread"""
        if self._monitoring:
            logger.warning("Performance monitoring already started")
            return
            
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info("Performance monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop performance monitoring"""
        if not self._monitoring:
            logger.warning("Performance monitoring not running")
            return
            
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
        logger.info("Performance monitoring stopped")
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop running in background thread"""
        while self._monitoring:
            try:
                self._collect_system_metrics()
                time.sleep(1.0)  # Collect metrics every second
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(1.0)
    
    def _collect_system_metrics(self) -> None:
        """Collect system performance metrics"""
        with self._lock:
            # CPU usage
            self._metrics.cpu_usage = psutil.cpu_percent(interval=None)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self._metrics.memory_usage = {
                'used': memory.used,
                'available': memory.available,
                'percent': memory.percent,
                'total': memory.total
            }
            
            # Update timestamp
            self._metrics.timestamp = datetime.now()
            
            # Process-specific metrics
            try:
                process = psutil.Process()
                process_memory = process.memory_info()
                self._metrics.memory_usage.update({
                    'process_rss': process_memory.rss,
                    'process_vms': process_memory.vms
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    
    @contextmanager
    def measure_response_time(self, operation_name: str) -> ContextManager[None]:
        """Context manager to measure response time of operations"""
        start_time = time.time()
        try:
            yield
        finally:
            end_time = time.time()
            duration = end_time - start_time
            self._record_response_time(operation_name, duration)
    
    def _record_response_time(self, operation_name: str, duration: float) -> None:
        """Record response time for an operation"""
        with self._lock:
            if operation_name not in self._response_times:
                self._response_times[operation_name] = []
            
            # Keep only last 100 measurements to prevent memory growth
            self._response_times[operation_name].append(duration)
            if len(self._response_times[operation_name]) > 100:
                self._response_times[operation_name] = self._response_times[operation_name][-100:]
            
            # Update current metrics with latest response time
            self._metrics.response_times[operation_name] = duration
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        with self._lock:
            # Calculate average response times
            avg_response_times = {}
            for operation, times in self._response_times.items():
                if times:
                    avg_response_times[operation] = sum(times) / len(times)
            
            return {
                'cpu_usage': self._metrics.cpu_usage,
                'memory_usage': self._metrics.memory_usage.copy(),
                'response_times': self._metrics.response_times.copy(),
                'avg_response_times': avg_response_times,
                'timestamp': self._metrics.timestamp.isoformat(),
                'uptime': time.time() - self._start_time,
                'monitoring_active': self._monitoring
            }
    
    def get_response_time_stats(self, operation_name: str) -> Dict[str, float]:
        """Get detailed response time statistics for an operation"""
        with self._lock:
            times = self._response_times.get(operation_name, [])
            if not times:
                return {}
            
            sorted_times = sorted(times)
            count = len(sorted_times)
            
            return {
                'count': count,
                'min': min(sorted_times),
                'max': max(sorted_times),
                'avg': sum(sorted_times) / count,
                'median': sorted_times[count // 2],
                'p95': sorted_times[int(count * 0.95)] if count > 0 else 0,
                'p99': sorted_times[int(count * 0.99)] if count > 0 else 0
            }
    
    def reset_metrics(self) -> None:
        """Reset all collected metrics"""
        with self._lock:
            self._response_times.clear()
            self._metrics = PerformanceMetrics()
            self._start_time = time.time()
        logger.info("Performance metrics reset")
    
    def is_monitoring(self) -> bool:
        """Check if monitoring is currently active"""
        return self._monitoring
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        metrics = self.get_metrics()
        
        # Determine health status based on thresholds
        cpu_healthy = metrics['cpu_usage'] < 80.0
        memory_healthy = metrics['memory_usage'].get('percent', 0) < 85.0
        
        # Check response time health
        response_healthy = True
        for operation, avg_time in metrics.get('avg_response_times', {}).items():
            if avg_time > 2.0:  # 2 second threshold
                response_healthy = False
                break
        
        overall_healthy = cpu_healthy and memory_healthy and response_healthy
        
        return {
            'overall_healthy': overall_healthy,
            'cpu_healthy': cpu_healthy,
            'memory_healthy': memory_healthy,
            'response_healthy': response_healthy,
            'status': 'healthy' if overall_healthy else 'degraded',
            'timestamp': datetime.now().isoformat()
        }


# Global performance monitor instance
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def start_global_monitoring() -> None:
    """Start global performance monitoring"""
    monitor = get_performance_monitor()
    monitor.start_monitoring()


def stop_global_monitoring() -> None:
    """Stop global performance monitoring"""
    monitor = get_performance_monitor()
    monitor.stop_monitoring()
