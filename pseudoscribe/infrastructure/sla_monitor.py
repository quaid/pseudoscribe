"""
SLA Monitor
Monitors Service Level Agreement compliance and performance thresholds
"""

import time
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SLAStatus(Enum):
    """SLA compliance status"""
    COMPLIANT = "compliant"
    WARNING = "warning"
    VIOLATION = "violation"
    UNKNOWN = "unknown"


@dataclass
class SLAThreshold:
    """SLA threshold configuration"""
    name: str
    max_value: float
    warning_threshold: float
    unit: str = "seconds"
    description: str = ""


@dataclass
class SLAViolation:
    """SLA violation record"""
    sla_name: str
    actual_value: float
    threshold_value: float
    timestamp: datetime
    severity: str
    description: str = ""


@dataclass
class SLAMetrics:
    """SLA compliance metrics"""
    total_measurements: int = 0
    compliant_measurements: int = 0
    warning_measurements: int = 0
    violation_measurements: int = 0
    compliance_rate: float = 0.0
    average_value: float = 0.0
    last_measurement: Optional[float] = None
    last_measurement_time: Optional[datetime] = None


class SLAMonitor:
    """
    Service Level Agreement monitoring system
    Tracks compliance with performance thresholds and SLA requirements
    """
    
    def __init__(self):
        self._thresholds: Dict[str, SLAThreshold] = {}
        self._violations: List[SLAViolation] = []
        self._metrics: Dict[str, SLAMetrics] = {}
        self._measurements: Dict[str, List[float]] = {}
        self._lock = threading.Lock()
        self._alert_callbacks: Dict[str, List[Callable]] = {}
        
        # Initialize default SLA thresholds
        self._setup_default_thresholds()
    
    def _setup_default_thresholds(self) -> None:
        """Setup default SLA thresholds based on requirements"""
        default_thresholds = [
            SLAThreshold(
                name="ai_operations",
                max_value=2.0,
                warning_threshold=1.5,
                unit="seconds",
                description="AI operations should complete within 2 seconds"
            ),
            SLAThreshold(
                name="live_suggestions",
                max_value=0.5,
                warning_threshold=0.3,
                unit="seconds",
                description="Live suggestions should respond within 500ms"
            ),
            SLAThreshold(
                name="api_response",
                max_value=0.2,
                warning_threshold=0.15,
                unit="seconds",
                description="API endpoints should respond within 200ms"
            ),
            SLAThreshold(
                name="extension_load",
                max_value=1.0,
                warning_threshold=0.8,
                unit="seconds",
                description="Extension should load within 1 second"
            ),
            SLAThreshold(
                name="websocket_connect",
                max_value=1.0,
                warning_threshold=0.8,
                unit="seconds",
                description="WebSocket connections should establish within 1 second"
            )
        ]
        
        for threshold in default_thresholds:
            self._thresholds[threshold.name] = threshold
            self._metrics[threshold.name] = SLAMetrics()
            self._measurements[threshold.name] = []
    
    def add_sla_threshold(self, threshold: SLAThreshold) -> None:
        """Add or update an SLA threshold"""
        with self._lock:
            self._thresholds[threshold.name] = threshold
            if threshold.name not in self._metrics:
                self._metrics[threshold.name] = SLAMetrics()
                self._measurements[threshold.name] = []
        logger.info(f"Added SLA threshold: {threshold.name} <= {threshold.max_value}{threshold.unit}")
    
    def remove_sla_threshold(self, name: str) -> None:
        """Remove an SLA threshold"""
        with self._lock:
            self._thresholds.pop(name, None)
            self._metrics.pop(name, None)
            self._measurements.pop(name, None)
        logger.info(f"Removed SLA threshold: {name}")
    
    def check_sla_compliance(self, sla_name: str, value: float) -> bool:
        """Check if a measurement complies with SLA threshold"""
        with self._lock:
            if sla_name not in self._thresholds:
                logger.warning(f"Unknown SLA: {sla_name}")
                return True  # Unknown SLAs are considered compliant
            
            threshold = self._thresholds[sla_name]
            metrics = self._metrics[sla_name]
            
            # Record the measurement
            self._measurements[sla_name].append(value)
            # Keep only last 1000 measurements
            if len(self._measurements[sla_name]) > 1000:
                self._measurements[sla_name] = self._measurements[sla_name][-1000:]
            
            # Update metrics
            metrics.total_measurements += 1
            metrics.last_measurement = value
            metrics.last_measurement_time = datetime.now()
            
            # Calculate average
            measurements = self._measurements[sla_name]
            metrics.average_value = sum(measurements) / len(measurements)
            
            # Determine compliance status
            is_compliant = value <= threshold.max_value
            is_warning = threshold.warning_threshold < value <= threshold.max_value
            is_violation = value > threshold.max_value
            
            if is_compliant and not is_warning:
                metrics.compliant_measurements += 1
            elif is_warning:
                metrics.warning_measurements += 1
                self._trigger_warning(sla_name, value, threshold)
            elif is_violation:
                metrics.violation_measurements += 1
                self._record_violation(sla_name, value, threshold)
            
            # Update compliance rate
            metrics.compliance_rate = (metrics.compliant_measurements / metrics.total_measurements) * 100
            
            return is_compliant
    
    def _record_violation(self, sla_name: str, value: float, threshold: SLAThreshold) -> None:
        """Record an SLA violation"""
        violation = SLAViolation(
            sla_name=sla_name,
            actual_value=value,
            threshold_value=threshold.max_value,
            timestamp=datetime.now(),
            severity="high",
            description=f"{sla_name} exceeded threshold: {value:.3f}{threshold.unit} > {threshold.max_value}{threshold.unit}"
        )
        
        self._violations.append(violation)
        # Keep only last 100 violations
        if len(self._violations) > 100:
            self._violations = self._violations[-100:]
        
        logger.warning(f"SLA violation: {violation.description}")
        self._trigger_alerts(sla_name, violation)
    
    def _trigger_warning(self, sla_name: str, value: float, threshold: SLAThreshold) -> None:
        """Trigger warning for approaching SLA threshold"""
        logger.warning(f"SLA warning: {sla_name} approaching threshold: {value:.3f}{threshold.unit} (warning at {threshold.warning_threshold}{threshold.unit})")
    
    def _trigger_alerts(self, sla_name: str, violation: SLAViolation) -> None:
        """Trigger alert callbacks for SLA violations"""
        callbacks = self._alert_callbacks.get(sla_name, [])
        for callback in callbacks:
            try:
                callback(violation)
            except Exception as e:
                logger.error(f"Error in SLA alert callback: {e}")
    
    def register_alert_callback(self, sla_name: str, callback: Callable[[SLAViolation], None]) -> None:
        """Register callback for SLA violations"""
        with self._lock:
            if sla_name not in self._alert_callbacks:
                self._alert_callbacks[sla_name] = []
            self._alert_callbacks[sla_name].append(callback)
        logger.info(f"Registered alert callback for SLA: {sla_name}")
    
    def get_sla_status(self, sla_name: Optional[str] = None) -> Dict[str, Any]:
        """Get SLA compliance status"""
        with self._lock:
            if sla_name:
                if sla_name not in self._thresholds:
                    return {}
                
                threshold = self._thresholds[sla_name]
                metrics = self._metrics[sla_name]
                
                # Determine current status
                status = SLAStatus.COMPLIANT
                if metrics.last_measurement:
                    if metrics.last_measurement > threshold.max_value:
                        status = SLAStatus.VIOLATION
                    elif metrics.last_measurement > threshold.warning_threshold:
                        status = SLAStatus.WARNING
                
                return {
                    'sla_name': sla_name,
                    'status': status.value,
                    'threshold': threshold.max_value,
                    'warning_threshold': threshold.warning_threshold,
                    'unit': threshold.unit,
                    'description': threshold.description,
                    'metrics': {
                        'total_measurements': metrics.total_measurements,
                        'compliance_rate': metrics.compliance_rate,
                        'average_value': metrics.average_value,
                        'last_measurement': metrics.last_measurement,
                        'last_measurement_time': metrics.last_measurement_time.isoformat() if metrics.last_measurement_time else None
                    }
                }
            else:
                # Return status for all SLAs
                result = {}
                for name in self._thresholds:
                    result[name] = self.get_sla_status(name)
                
                # Calculate overall compliance
                total_measurements = sum(m.total_measurements for m in self._metrics.values())
                total_compliant = sum(m.compliant_measurements for m in self._metrics.values())
                overall_compliance = (total_compliant / total_measurements * 100) if total_measurements > 0 else 100
                
                result['overall_compliance'] = overall_compliance
                result['total_violations'] = len(self._violations)
                result['timestamp'] = datetime.now().isoformat()
                
                return result
    
    def get_violations(self, since: Optional[datetime] = None, sla_name: Optional[str] = None) -> List[SLAViolation]:
        """Get SLA violations"""
        with self._lock:
            violations = self._violations.copy()
            
            if since:
                violations = [v for v in violations if v.timestamp >= since]
            
            if sla_name:
                violations = [v for v in violations if v.sla_name == sla_name]
            
            return violations
    
    def get_sla_report(self, since: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate comprehensive SLA report"""
        since = since or datetime.now() - timedelta(hours=24)
        
        with self._lock:
            report = {
                'report_period': {
                    'start': since.isoformat(),
                    'end': datetime.now().isoformat()
                },
                'sla_status': self.get_sla_status(),
                'violations': [
                    {
                        'sla_name': v.sla_name,
                        'actual_value': v.actual_value,
                        'threshold_value': v.threshold_value,
                        'timestamp': v.timestamp.isoformat(),
                        'severity': v.severity,
                        'description': v.description
                    }
                    for v in self.get_violations(since)
                ],
                'summary': {
                    'total_slas': len(self._thresholds),
                    'total_violations': len(self.get_violations(since)),
                    'slas_with_violations': len(set(v.sla_name for v in self.get_violations(since))),
                    'overall_health': 'healthy' if len(self.get_violations(since)) == 0 else 'degraded'
                }
            }
            
            return report
    
    def reset_metrics(self, sla_name: Optional[str] = None) -> None:
        """Reset SLA metrics"""
        with self._lock:
            if sla_name:
                if sla_name in self._metrics:
                    self._metrics[sla_name] = SLAMetrics()
                    self._measurements[sla_name] = []
                    logger.info(f"Reset SLA metrics for: {sla_name}")
            else:
                for name in self._metrics:
                    self._metrics[name] = SLAMetrics()
                    self._measurements[name] = []
                self._violations.clear()
                logger.info("Reset all SLA metrics")
    
    def get_threshold_config(self) -> Dict[str, Dict[str, Any]]:
        """Get current SLA threshold configuration"""
        with self._lock:
            return {
                name: {
                    'max_value': threshold.max_value,
                    'warning_threshold': threshold.warning_threshold,
                    'unit': threshold.unit,
                    'description': threshold.description
                }
                for name, threshold in self._thresholds.items()
            }


# Global SLA monitor instance
_sla_monitor: Optional[SLAMonitor] = None


def get_sla_monitor() -> SLAMonitor:
    """Get global SLA monitor instance"""
    global _sla_monitor
    if _sla_monitor is None:
        _sla_monitor = SLAMonitor()
    return _sla_monitor


def check_sla_compliance(sla_name: str, value: float) -> bool:
    """Convenience function to check SLA compliance"""
    monitor = get_sla_monitor()
    return monitor.check_sla_compliance(sla_name, value)
