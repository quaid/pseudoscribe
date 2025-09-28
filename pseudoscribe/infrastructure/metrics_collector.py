"""
Metrics Collector
Collects and aggregates performance metrics from various sources
"""

import time
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """Single metric data point"""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class MetricSeries:
    """Time series of metric points"""
    name: str
    points: deque = field(default_factory=lambda: deque(maxlen=1000))
    tags: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """
    Collects and aggregates performance metrics
    Provides time-series data storage and querying capabilities
    """
    
    def __init__(self, max_series_length: int = 1000):
        self._metrics: Dict[str, MetricSeries] = {}
        self._lock = threading.Lock()
        self._max_series_length = max_series_length
        self._collectors: Dict[str, Callable] = {}
        self._collection_interval = 1.0  # seconds
        self._collecting = False
        self._collection_thread: Optional[threading.Thread] = None
        
    def register_collector(self, name: str, collector_func: Callable[[], Dict[str, float]]) -> None:
        """Register a metric collector function"""
        with self._lock:
            self._collectors[name] = collector_func
        logger.info(f"Registered metric collector: {name}")
    
    def unregister_collector(self, name: str) -> None:
        """Unregister a metric collector function"""
        with self._lock:
            self._collectors.pop(name, None)
        logger.info(f"Unregistered metric collector: {name}")
    
    def start_collection(self, interval: float = 1.0) -> None:
        """Start automatic metric collection"""
        if self._collecting:
            logger.warning("Metrics collection already started")
            return
            
        self._collection_interval = interval
        self._collecting = True
        self._collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
        self._collection_thread.start()
        logger.info(f"Started metrics collection with {interval}s interval")
    
    def stop_collection(self) -> None:
        """Stop automatic metric collection"""
        if not self._collecting:
            logger.warning("Metrics collection not running")
            return
            
        self._collecting = False
        if self._collection_thread:
            self._collection_thread.join(timeout=2.0)
        logger.info("Stopped metrics collection")
    
    def _collection_loop(self) -> None:
        """Main collection loop"""
        while self._collecting:
            try:
                self._collect_all_metrics()
                time.sleep(self._collection_interval)
            except Exception as e:
                logger.error(f"Error in metrics collection loop: {e}")
                time.sleep(self._collection_interval)
    
    def _collect_all_metrics(self) -> None:
        """Collect metrics from all registered collectors"""
        timestamp = datetime.now()
        
        with self._lock:
            for collector_name, collector_func in self._collectors.items():
                try:
                    metrics = collector_func()
                    for metric_name, value in metrics.items():
                        full_name = f"{collector_name}.{metric_name}"
                        self._add_metric_point(full_name, value, timestamp)
                except Exception as e:
                    logger.error(f"Error collecting metrics from {collector_name}: {e}")
    
    def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record a single metric point"""
        timestamp = datetime.now()
        tags = tags or {}
        
        with self._lock:
            self._add_metric_point(name, value, timestamp, tags)
    
    def _add_metric_point(self, name: str, value: float, timestamp: datetime, tags: Optional[Dict[str, str]] = None) -> None:
        """Add a metric point to the time series"""
        tags = tags or {}
        
        if name not in self._metrics:
            self._metrics[name] = MetricSeries(
                name=name,
                points=deque(maxlen=self._max_series_length),
                tags=tags
            )
        
        point = MetricPoint(name=name, value=value, timestamp=timestamp, tags=tags)
        self._metrics[name].points.append(point)
    
    def get_metric_series(self, name: str, since: Optional[datetime] = None) -> List[MetricPoint]:
        """Get metric time series data"""
        with self._lock:
            if name not in self._metrics:
                return []
            
            points = list(self._metrics[name].points)
            
            if since:
                points = [p for p in points if p.timestamp >= since]
            
            return points
    
    def get_latest_metric(self, name: str) -> Optional[MetricPoint]:
        """Get the latest metric point"""
        with self._lock:
            if name not in self._metrics or not self._metrics[name].points:
                return None
            return self._metrics[name].points[-1]
    
    def get_metric_statistics(self, name: str, since: Optional[datetime] = None) -> Dict[str, float]:
        """Get statistical summary of a metric"""
        points = self.get_metric_series(name, since)
        
        if not points:
            return {}
        
        values = [p.value for p in points]
        sorted_values = sorted(values)
        count = len(values)
        
        return {
            'count': count,
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / count,
            'median': sorted_values[count // 2],
            'p95': sorted_values[int(count * 0.95)] if count > 0 else 0,
            'p99': sorted_values[int(count * 0.99)] if count > 0 else 0,
            'sum': sum(values),
            'latest': values[-1] if values else 0
        }
    
    def get_all_metrics(self, since: Optional[datetime] = None) -> Dict[str, List[MetricPoint]]:
        """Get all metric series data"""
        with self._lock:
            result = {}
            for name in self._metrics:
                result[name] = self.get_metric_series(name, since)
            return result
    
    def get_metric_names(self) -> List[str]:
        """Get list of all metric names"""
        with self._lock:
            return list(self._metrics.keys())
    
    def clear_metrics(self, name: Optional[str] = None) -> None:
        """Clear metrics data"""
        with self._lock:
            if name:
                if name in self._metrics:
                    self._metrics[name].points.clear()
                    logger.info(f"Cleared metrics for: {name}")
            else:
                self._metrics.clear()
                logger.info("Cleared all metrics")
    
    def get_metrics_summary(self, since: Optional[datetime] = None) -> Dict[str, Any]:
        """Get summary of all metrics"""
        summary = {}
        
        for name in self.get_metric_names():
            stats = self.get_metric_statistics(name, since)
            if stats:
                summary[name] = stats
        
        return {
            'metrics': summary,
            'total_series': len(self._metrics),
            'collection_active': self._collecting,
            'collection_interval': self._collection_interval,
            'timestamp': datetime.now().isoformat()
        }
    
    def export_metrics(self, format: str = 'json', since: Optional[datetime] = None) -> str:
        """Export metrics in specified format"""
        if format.lower() == 'json':
            import json
            data = self.get_all_metrics(since)
            # Convert MetricPoint objects to dictionaries for JSON serialization
            json_data = {}
            for name, points in data.items():
                json_data[name] = [
                    {
                        'name': p.name,
                        'value': p.value,
                        'timestamp': p.timestamp.isoformat(),
                        'tags': p.tags
                    }
                    for p in points
                ]
            return json.dumps(json_data, indent=2)
        
        elif format.lower() == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['metric_name', 'value', 'timestamp', 'tags'])
            
            for name, points in self.get_all_metrics(since).items():
                for point in points:
                    tags_str = ','.join(f"{k}={v}" for k, v in point.tags.items())
                    writer.writerow([point.name, point.value, point.timestamp.isoformat(), tags_str])
            
            return output.getvalue()
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def create_alert_rule(self, metric_name: str, threshold: float, condition: str = 'greater') -> str:
        """Create an alert rule for a metric (placeholder for future implementation)"""
        # This is a placeholder for alert functionality
        rule_id = f"{metric_name}_{condition}_{threshold}"
        logger.info(f"Created alert rule: {rule_id}")
        return rule_id


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector instance"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def record_metric(name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
    """Convenience function to record a metric"""
    collector = get_metrics_collector()
    collector.record_metric(name, value, tags)
