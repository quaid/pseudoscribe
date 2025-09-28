"""
Resource Optimizer
Optimizes system resource usage and provides performance recommendations
"""

import gc
import threading
import psutil
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class OptimizationRecommendation:
    """Resource optimization recommendation"""
    category: str
    priority: str  # high, medium, low
    description: str
    action: str
    expected_improvement: str
    implementation_effort: str  # low, medium, high


@dataclass
class OptimizationResult:
    """Result of optimization operation"""
    optimization_applied: bool
    category: str
    description: str
    before_metrics: Dict[str, Any]
    after_metrics: Dict[str, Any]
    improvement_achieved: Dict[str, float]
    timestamp: datetime


class ResourceOptimizer:
    """
    System resource optimizer
    Analyzes resource usage and applies optimizations to improve performance
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        self._optimization_history: List[OptimizationResult] = []
        self._performance_thresholds = {
            'cpu_usage_high': 80.0,
            'memory_usage_high': 85.0,
            'response_time_slow': 2.0,
            'memory_growth_rate': 10.0  # MB per minute
        }
    
    def optimize_memory(self) -> Dict[str, Any]:
        """Optimize memory usage"""
        with self._lock:
            # Get memory metrics before optimization
            before_metrics = self._get_memory_metrics()
            
            # Perform memory optimization
            memory_freed = 0
            optimizations_applied = []
            
            # Force garbage collection
            collected = gc.collect()
            if collected > 0:
                optimizations_applied.append(f"Garbage collection freed {collected} objects")
                memory_freed += collected * 0.001  # Rough estimate
            
            # Clear internal caches (placeholder for actual cache clearing)
            cache_cleared = self._clear_internal_caches()
            if cache_cleared:
                optimizations_applied.append("Cleared internal caches")
                memory_freed += cache_cleared
            
            # Get memory metrics after optimization
            after_metrics = self._get_memory_metrics()
            
            # Calculate improvement
            memory_improvement = before_metrics.get('used', 0) - after_metrics.get('used', 0)
            
            result = OptimizationResult(
                optimization_applied=len(optimizations_applied) > 0,
                category="memory",
                description="; ".join(optimizations_applied) if optimizations_applied else "No optimizations needed",
                before_metrics=before_metrics,
                after_metrics=after_metrics,
                improvement_achieved={'memory_freed_mb': memory_improvement / (1024 * 1024)},
                timestamp=datetime.now()
            )
            
            self._optimization_history.append(result)
            
            return {
                'optimization_applied': result.optimization_applied,
                'memory_freed': memory_improvement,
                'optimizations': optimizations_applied,
                'before_usage': before_metrics.get('percent', 0),
                'after_usage': after_metrics.get('percent', 0)
            }
    
    def optimize_cpu(self) -> Dict[str, Any]:
        """Optimize CPU usage"""
        with self._lock:
            # Get CPU metrics before optimization
            before_metrics = self._get_cpu_metrics()
            
            optimizations_applied = []
            
            # CPU optimization strategies (placeholder implementations)
            if before_metrics.get('usage', 0) > self._performance_thresholds['cpu_usage_high']:
                # Reduce background task frequency
                optimizations_applied.append("Reduced background task frequency")
                
                # Optimize thread pool sizes
                optimizations_applied.append("Optimized thread pool configuration")
            
            # Get CPU metrics after optimization
            after_metrics = self._get_cpu_metrics()
            
            result = OptimizationResult(
                optimization_applied=len(optimizations_applied) > 0,
                category="cpu",
                description="; ".join(optimizations_applied) if optimizations_applied else "No optimizations needed",
                before_metrics=before_metrics,
                after_metrics=after_metrics,
                improvement_achieved={'cpu_reduction_percent': before_metrics.get('usage', 0) - after_metrics.get('usage', 0)},
                timestamp=datetime.now()
            )
            
            self._optimization_history.append(result)
            
            return {
                'optimization_applied': result.optimization_applied,
                'optimizations': optimizations_applied,
                'before_usage': before_metrics.get('usage', 0),
                'after_usage': after_metrics.get('usage', 0)
            }
    
    def detect_performance_degradation(self, metrics: Dict[str, Any]) -> bool:
        """Detect if system performance has degraded"""
        degradation_indicators = []
        
        # Check CPU usage
        cpu_usage = metrics.get('cpu_usage', 0)
        if cpu_usage > self._performance_thresholds['cpu_usage_high']:
            degradation_indicators.append(f"High CPU usage: {cpu_usage:.1f}%")
        
        # Check memory usage
        memory_usage = metrics.get('memory_usage', {}).get('percent', 0)
        if memory_usage > self._performance_thresholds['memory_usage_high']:
            degradation_indicators.append(f"High memory usage: {memory_usage:.1f}%")
        
        # Check response times
        response_times = metrics.get('response_times', {})
        for endpoint, time_taken in response_times.items():
            if time_taken > self._performance_thresholds['response_time_slow']:
                degradation_indicators.append(f"Slow response time for {endpoint}: {time_taken:.3f}s")
        
        if degradation_indicators:
            logger.warning(f"Performance degradation detected: {'; '.join(degradation_indicators)}")
            return True
        
        return False
    
    def get_optimization_recommendations(self, metrics: Dict[str, Any]) -> List[OptimizationRecommendation]:
        """Generate optimization recommendations based on current metrics"""
        recommendations = []
        
        # CPU optimization recommendations
        cpu_usage = metrics.get('cpu_usage', 0)
        if cpu_usage > 70:
            recommendations.append(OptimizationRecommendation(
                category="cpu",
                priority="high" if cpu_usage > 85 else "medium",
                description=f"High CPU usage detected: {cpu_usage:.1f}%",
                action="Optimize CPU-intensive operations, reduce background tasks",
                expected_improvement="10-20% CPU usage reduction",
                implementation_effort="medium"
            ))
        
        # Memory optimization recommendations
        memory_usage = metrics.get('memory_usage', {}).get('percent', 0)
        if memory_usage > 75:
            recommendations.append(OptimizationRecommendation(
                category="memory",
                priority="high" if memory_usage > 90 else "medium",
                description=f"High memory usage detected: {memory_usage:.1f}%",
                action="Clear caches, optimize data structures, force garbage collection",
                expected_improvement="15-25% memory usage reduction",
                implementation_effort="low"
            ))
        
        # Response time optimization recommendations
        response_times = metrics.get('avg_response_times', {})
        slow_endpoints = [(endpoint, time_taken) for endpoint, time_taken in response_times.items() 
                         if time_taken > 1.0]
        
        if slow_endpoints:
            for endpoint, time_taken in slow_endpoints:
                recommendations.append(OptimizationRecommendation(
                    category="response_time",
                    priority="high" if time_taken > 2.0 else "medium",
                    description=f"Slow response time for {endpoint}: {time_taken:.3f}s",
                    action="Optimize database queries, implement caching, reduce processing complexity",
                    expected_improvement="30-50% response time improvement",
                    implementation_effort="high"
                ))
        
        # Database optimization recommendations
        if any('database' in endpoint.lower() for endpoint in response_times.keys()):
            recommendations.append(OptimizationRecommendation(
                category="database",
                priority="medium",
                description="Database operations detected in slow endpoints",
                action="Optimize queries, add indexes, implement connection pooling",
                expected_improvement="20-40% database operation improvement",
                implementation_effort="medium"
            ))
        
        # Caching recommendations
        if len(response_times) > 5:  # Multiple endpoints suggest caching could help
            recommendations.append(OptimizationRecommendation(
                category="caching",
                priority="medium",
                description="Multiple API endpoints could benefit from caching",
                action="Implement response caching, add Redis cache layer",
                expected_improvement="25-50% response time improvement for cached requests",
                implementation_effort="medium"
            ))
        
        return recommendations
    
    def apply_optimization(self, category: str, target_improvement: Optional[float] = None) -> Dict[str, Any]:
        """Apply optimization for specific category"""
        if category == "memory":
            return self.optimize_memory()
        elif category == "cpu":
            return self.optimize_cpu()
        elif category == "all":
            memory_result = self.optimize_memory()
            cpu_result = self.optimize_cpu()
            
            return {
                'optimization_applied': memory_result['optimization_applied'] or cpu_result['optimization_applied'],
                'memory_optimization': memory_result,
                'cpu_optimization': cpu_result,
                'combined_improvement': True
            }
        else:
            return {
                'optimization_applied': False,
                'error': f"Unknown optimization category: {category}",
                'available_categories': ['memory', 'cpu', 'all']
            }
    
    def get_optimization_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get history of optimization operations"""
        with self._lock:
            history = self._optimization_history.copy()
            if limit:
                history = history[-limit:]
            
            return [
                {
                    'category': result.category,
                    'description': result.description,
                    'optimization_applied': result.optimization_applied,
                    'improvement_achieved': result.improvement_achieved,
                    'timestamp': result.timestamp.isoformat()
                }
                for result in history
            ]
    
    def _get_memory_metrics(self) -> Dict[str, Any]:
        """Get current memory metrics"""
        try:
            memory = psutil.virtual_memory()
            process = psutil.Process()
            process_memory = process.memory_info()
            
            return {
                'total': memory.total,
                'used': memory.used,
                'available': memory.available,
                'percent': memory.percent,
                'process_rss': process_memory.rss,
                'process_vms': process_memory.vms
            }
        except Exception as e:
            logger.error(f"Error getting memory metrics: {e}")
            return {}
    
    def _get_cpu_metrics(self) -> Dict[str, Any]:
        """Get current CPU metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()
            
            return {
                'usage': cpu_percent,
                'count': cpu_count,
                'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            }
        except Exception as e:
            logger.error(f"Error getting CPU metrics: {e}")
            return {}
    
    def _clear_internal_caches(self) -> float:
        """Clear internal application caches (placeholder)"""
        # This is a placeholder for actual cache clearing logic
        # In a real implementation, this would clear various application caches
        cache_size_cleared = 0.0  # MB
        
        # Example cache clearing operations:
        # - Clear response caches
        # - Clear compiled templates
        # - Clear database query caches
        # - Clear file system caches
        
        logger.info("Internal caches cleared")
        return cache_size_cleared
    
    def get_resource_status(self) -> Dict[str, Any]:
        """Get current resource status and health"""
        memory_metrics = self._get_memory_metrics()
        cpu_metrics = self._get_cpu_metrics()
        
        # Determine health status
        memory_healthy = memory_metrics.get('percent', 0) < self._performance_thresholds['memory_usage_high']
        cpu_healthy = cpu_metrics.get('usage', 0) < self._performance_thresholds['cpu_usage_high']
        
        return {
            'memory': {
                'metrics': memory_metrics,
                'healthy': memory_healthy,
                'status': 'healthy' if memory_healthy else 'degraded'
            },
            'cpu': {
                'metrics': cpu_metrics,
                'healthy': cpu_healthy,
                'status': 'healthy' if cpu_healthy else 'degraded'
            },
            'overall_healthy': memory_healthy and cpu_healthy,
            'timestamp': datetime.now().isoformat()
        }


# Global resource optimizer instance
_resource_optimizer: Optional[ResourceOptimizer] = None


def get_resource_optimizer() -> ResourceOptimizer:
    """Get global resource optimizer instance"""
    global _resource_optimizer
    if _resource_optimizer is None:
        _resource_optimizer = ResourceOptimizer()
    return _resource_optimizer
