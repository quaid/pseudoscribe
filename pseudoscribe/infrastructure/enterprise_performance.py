"""Enterprise Performance Monitoring.

Issue: ENT-002 - Performance Monitoring

This module provides enterprise-grade performance monitoring including:
- Multi-tenant performance isolation
- Configurable alerting thresholds
- Historical data retention
- Performance baselines and comparison
- Anomaly detection
- Performance reporting
"""

import json
import statistics
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum
from collections import defaultdict


class AlertLevel(Enum):
    """Severity levels for performance alerts."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class PerformanceAlert:
    """Represents a performance alert."""
    level: AlertLevel
    message: str
    tenant_id: str
    operation: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metric_value: Optional[float] = None
    threshold: Optional[float] = None


@dataclass
class PerformanceBaseline:
    """Represents a performance baseline for an operation."""
    operation: str
    tenant_id: str
    avg_duration_ms: float
    min_duration_ms: float
    max_duration_ms: float
    std_dev_ms: float
    p95_duration_ms: float
    p99_duration_ms: float
    sample_size: int
    established_at: datetime = field(default_factory=datetime.now)


@dataclass
class TenantPerformanceConfig:
    """Configuration for tenant performance monitoring."""
    response_time_warning_ms: float = 500
    response_time_critical_ms: float = 2000
    error_rate_warning: float = 0.05  # 5%
    error_rate_critical: float = 0.10  # 10%
    baseline_sample_size: int = 10
    anomaly_threshold_std_dev: float = 2.0


@dataclass
class OperationRecord:
    """Record of a single operation."""
    operation: str
    duration_ms: float
    success: bool
    timestamp: datetime = field(default_factory=datetime.now)


class EnterprisePerformanceMonitor:
    """Enterprise-grade performance monitoring with multi-tenant support."""

    def __init__(self):
        """Initialize the enterprise performance monitor."""
        self._tenant_configs: Dict[str, TenantPerformanceConfig] = {}
        self._tenant_metrics: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"operations": defaultdict(lambda: self._default_op_metrics())}
        )
        self._operation_history: Dict[str, Dict[str, List[OperationRecord]]] = defaultdict(
            lambda: defaultdict(list)
        )
        self._baselines: Dict[str, Dict[str, PerformanceBaseline]] = defaultdict(dict)
        self._alerts: Dict[str, List[PerformanceAlert]] = defaultdict(list)

    def _default_op_metrics(self) -> Dict[str, Any]:
        """Return default operation metrics structure."""
        return {
            "count": 0,
            "success_count": 0,
            "failure_count": 0,
            "total_duration_ms": 0,
            "avg_duration_ms": 0,
            "min_duration_ms": float('inf'),
            "max_duration_ms": 0,
            "success_rate": 100.0,
            "durations": []
        }

    def configure_tenant(
        self,
        tenant_id: str,
        config: TenantPerformanceConfig
    ) -> None:
        """Configure performance monitoring for a tenant.

        Args:
            tenant_id: The tenant to configure
            config: Performance configuration
        """
        self._tenant_configs[tenant_id] = config

    def get_tenant_config(self, tenant_id: str) -> TenantPerformanceConfig:
        """Get performance configuration for a tenant.

        Args:
            tenant_id: The tenant to get config for

        Returns:
            TenantPerformanceConfig, defaults if not configured
        """
        return self._tenant_configs.get(tenant_id, TenantPerformanceConfig())

    def track_operation(
        self,
        tenant_id: str,
        operation: str,
        duration_ms: float,
        success: bool
    ) -> None:
        """Track a performance metric for an operation.

        Args:
            tenant_id: The tenant performing the operation
            operation: Name of the operation
            duration_ms: Duration in milliseconds
            success: Whether the operation succeeded
        """
        # Create operation record
        record = OperationRecord(
            operation=operation,
            duration_ms=duration_ms,
            success=success
        )
        self._operation_history[tenant_id][operation].append(record)

        # Update metrics
        metrics = self._tenant_metrics[tenant_id]["operations"][operation]
        metrics["count"] += 1
        metrics["total_duration_ms"] += duration_ms
        metrics["avg_duration_ms"] = metrics["total_duration_ms"] / metrics["count"]
        metrics["min_duration_ms"] = min(metrics["min_duration_ms"], duration_ms)
        metrics["max_duration_ms"] = max(metrics["max_duration_ms"], duration_ms)
        metrics["durations"].append(duration_ms)

        if success:
            metrics["success_count"] += 1
        else:
            metrics["failure_count"] += 1

        metrics["success_rate"] = (metrics["success_count"] / metrics["count"]) * 100

        # Check for alerts
        self._check_alerts(tenant_id, operation, duration_ms, success)

    def _check_alerts(
        self,
        tenant_id: str,
        operation: str,
        duration_ms: float,
        success: bool
    ) -> None:
        """Check and generate alerts based on thresholds.

        Args:
            tenant_id: The tenant to check
            operation: The operation that was tracked
            duration_ms: Duration of the operation
            success: Whether it succeeded
        """
        config = self.get_tenant_config(tenant_id)
        metrics = self._tenant_metrics[tenant_id]["operations"][operation]

        # Check response time thresholds
        if duration_ms >= config.response_time_critical_ms:
            self._alerts[tenant_id].append(PerformanceAlert(
                level=AlertLevel.CRITICAL,
                message=f"Critical response time for {operation}: {duration_ms}ms exceeds {config.response_time_critical_ms}ms",
                tenant_id=tenant_id,
                operation=operation,
                metric_value=duration_ms,
                threshold=config.response_time_critical_ms
            ))
        elif duration_ms >= config.response_time_warning_ms:
            self._alerts[tenant_id].append(PerformanceAlert(
                level=AlertLevel.WARNING,
                message=f"Warning: Response time for {operation}: {duration_ms}ms exceeds {config.response_time_warning_ms}ms",
                tenant_id=tenant_id,
                operation=operation,
                metric_value=duration_ms,
                threshold=config.response_time_warning_ms
            ))

        # Check error rate thresholds (only if enough samples)
        if metrics["count"] >= 10:
            error_rate = metrics["failure_count"] / metrics["count"]
            if error_rate >= config.error_rate_critical:
                # Only add if not already alerted at this level
                if not any(a.level == AlertLevel.CRITICAL and "error rate" in a.message.lower()
                          for a in self._alerts[tenant_id][-5:]):
                    self._alerts[tenant_id].append(PerformanceAlert(
                        level=AlertLevel.CRITICAL,
                        message=f"Critical error rate for {operation}: {error_rate*100:.1f}% exceeds {config.error_rate_critical*100}%",
                        tenant_id=tenant_id,
                        operation=operation,
                        metric_value=error_rate,
                        threshold=config.error_rate_critical
                    ))
            elif error_rate >= config.error_rate_warning:
                if not any(a.level == AlertLevel.WARNING and "error rate" in a.message.lower()
                          for a in self._alerts[tenant_id][-5:]):
                    self._alerts[tenant_id].append(PerformanceAlert(
                        level=AlertLevel.WARNING,
                        message=f"Warning: Error rate for {operation}: {error_rate*100:.1f}% exceeds {config.error_rate_warning*100}%",
                        tenant_id=tenant_id,
                        operation=operation,
                        metric_value=error_rate,
                        threshold=config.error_rate_warning
                    ))

    def get_tenant_metrics(self, tenant_id: str) -> Dict[str, Any]:
        """Get performance metrics for a tenant.

        Args:
            tenant_id: The tenant to get metrics for

        Returns:
            Dictionary containing operation metrics
        """
        metrics = self._tenant_metrics.get(tenant_id)
        if not metrics:
            return {"operations": {}}

        # Convert defaultdict to regular dict for output
        return {
            "operations": dict(metrics["operations"])
        }

    def get_alerts(self, tenant_id: str) -> List[PerformanceAlert]:
        """Get alerts for a tenant.

        Args:
            tenant_id: The tenant to get alerts for

        Returns:
            List of PerformanceAlerts
        """
        return self._alerts.get(tenant_id, [])

    def clear_alerts(self, tenant_id: str) -> None:
        """Clear alerts for a tenant.

        Args:
            tenant_id: The tenant to clear alerts for
        """
        self._alerts[tenant_id] = []

    def establish_baseline(
        self,
        tenant_id: str,
        operation: str
    ) -> Optional[PerformanceBaseline]:
        """Establish a performance baseline for an operation.

        Args:
            tenant_id: The tenant to establish baseline for
            operation: The operation to baseline

        Returns:
            PerformanceBaseline if enough data, None otherwise
        """
        config = self.get_tenant_config(tenant_id)
        history = self._operation_history.get(tenant_id, {}).get(operation, [])

        if len(history) < config.baseline_sample_size:
            return None

        durations = [r.duration_ms for r in history]
        sorted_durations = sorted(durations)
        count = len(sorted_durations)

        baseline = PerformanceBaseline(
            operation=operation,
            tenant_id=tenant_id,
            avg_duration_ms=statistics.mean(durations),
            min_duration_ms=min(durations),
            max_duration_ms=max(durations),
            std_dev_ms=statistics.stdev(durations) if len(durations) > 1 else 0,
            p95_duration_ms=sorted_durations[int(count * 0.95)] if count > 0 else 0,
            p99_duration_ms=sorted_durations[int(count * 0.99)] if count > 0 else 0,
            sample_size=count
        )

        self._baselines[tenant_id][operation] = baseline
        return baseline

    def compare_to_baseline(
        self,
        tenant_id: str,
        operation: str
    ) -> Optional[Dict[str, Any]]:
        """Compare current performance to baseline.

        Args:
            tenant_id: The tenant to compare
            operation: The operation to compare

        Returns:
            Comparison results or None if no baseline
        """
        baseline = self._baselines.get(tenant_id, {}).get(operation)
        if not baseline:
            return None

        metrics = self._tenant_metrics[tenant_id]["operations"].get(operation)
        if not metrics:
            return None

        current_avg = metrics["avg_duration_ms"]
        baseline_avg = baseline.avg_duration_ms

        deviation_percent = ((current_avg - baseline_avg) / baseline_avg) * 100 if baseline_avg > 0 else 0
        is_degraded = current_avg > baseline_avg + (2 * baseline.std_dev_ms)

        return {
            "baseline_avg_ms": baseline_avg,
            "current_avg_ms": current_avg,
            "deviation_percent": deviation_percent,
            "is_degraded": is_degraded,
            "baseline_established_at": baseline.established_at.isoformat()
        }

    def reset_tenant_metrics(self, tenant_id: str) -> None:
        """Reset metrics for a tenant (keeps baselines).

        Args:
            tenant_id: The tenant to reset
        """
        self._tenant_metrics[tenant_id] = {
            "operations": defaultdict(lambda: self._default_op_metrics())
        }
        self._operation_history[tenant_id] = defaultdict(list)

    def detect_anomalies(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Detect performance anomalies for a tenant.

        Args:
            tenant_id: The tenant to analyze

        Returns:
            List of detected anomalies
        """
        anomalies = []
        config = self.get_tenant_config(tenant_id)

        for operation, baseline in self._baselines.get(tenant_id, {}).items():
            metrics = self._tenant_metrics[tenant_id]["operations"].get(operation)
            if not metrics or metrics["count"] == 0:
                continue

            # Check for response time spike
            if metrics["durations"]:
                latest_duration = metrics["durations"][-1]
                # Use std_dev if available, otherwise use 50% of avg as threshold
                if baseline.std_dev_ms > 0:
                    threshold = baseline.avg_duration_ms + (config.anomaly_threshold_std_dev * baseline.std_dev_ms)
                else:
                    threshold = baseline.avg_duration_ms * 1.5  # 50% above average

                if latest_duration > threshold:
                    anomalies.append({
                        "type": "response_time_spike",
                        "operation": operation,
                        "value": latest_duration,
                        "expected_max": threshold,
                        "message": f"Response time spike detected: {latest_duration}ms vs expected max {threshold:.1f}ms"
                    })

            # Check for error rate spike
            if metrics["count"] >= 5:
                current_error_rate = metrics["failure_count"] / metrics["count"]
                # Baseline should have low error rate, spike is significant increase
                if current_error_rate > 0.20:  # More than 20% errors is an anomaly
                    anomalies.append({
                        "type": "error_rate_spike",
                        "operation": operation,
                        "value": current_error_rate,
                        "message": f"Error rate spike detected: {current_error_rate*100:.1f}%"
                    })

        return anomalies

    def generate_report(
        self,
        tenant_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Generate a performance report for a tenant.

        Args:
            tenant_id: The tenant to report on
            start_time: Optional start time filter
            end_time: Optional end time filter

        Returns:
            Performance report dictionary
        """
        # Filter history by time if specified
        all_records = []
        for op_records in self._operation_history.get(tenant_id, {}).values():
            for record in op_records:
                if start_time and record.timestamp < start_time:
                    continue
                if end_time and record.timestamp > end_time:
                    continue
                all_records.append(record)

        total_ops = len(all_records)
        total_failures = sum(1 for r in all_records if not r.success)
        success_rate = ((total_ops - total_failures) / total_ops * 100) if total_ops > 0 else 0

        # Group by operation
        operations = {}
        for record in all_records:
            if record.operation not in operations:
                operations[record.operation] = {
                    "count": 0,
                    "failures": 0,
                    "durations": []
                }
            operations[record.operation]["count"] += 1
            if not record.success:
                operations[record.operation]["failures"] += 1
            operations[record.operation]["durations"].append(record.duration_ms)

        # Calculate per-operation stats
        for op, data in operations.items():
            if data["durations"]:
                data["avg_duration_ms"] = statistics.mean(data["durations"])
                data["min_duration_ms"] = min(data["durations"])
                data["max_duration_ms"] = max(data["durations"])
            del data["durations"]  # Remove raw data from report

        return {
            "summary": {
                "total_operations": total_ops,
                "total_failures": total_failures,
                "overall_success_rate": success_rate,
                "report_generated_at": datetime.now().isoformat()
            },
            "operations": operations,
            "alerts": [
                {
                    "level": a.level.value,
                    "message": a.message,
                    "timestamp": a.timestamp.isoformat()
                }
                for a in self._alerts.get(tenant_id, [])
            ]
        }

    def export_report(
        self,
        tenant_id: str,
        format: str = "json"
    ) -> str:
        """Export performance report in specified format.

        Args:
            tenant_id: The tenant to export
            format: Output format ("json")

        Returns:
            Exported report as string
        """
        report = self.generate_report(tenant_id)

        if format == "json":
            return json.dumps(report, indent=2)

        raise ValueError(f"Unsupported format: {format}")

    def get_trending_metrics(
        self,
        tenant_id: str,
        operation: str
    ) -> Optional[Dict[str, Any]]:
        """Get trending performance metrics for an operation.

        Args:
            tenant_id: The tenant to analyze
            operation: The operation to analyze

        Returns:
            Trending metrics dictionary
        """
        history = self._operation_history.get(tenant_id, {}).get(operation, [])
        if len(history) < 2:
            return None

        durations = [r.duration_ms for r in history]

        # Calculate trend direction using simple linear comparison
        first_half_avg = statistics.mean(durations[:len(durations)//2])
        second_half_avg = statistics.mean(durations[len(durations)//2:])

        if second_half_avg > first_half_avg * 1.1:
            trend_direction = "increasing"
        elif second_half_avg < first_half_avg * 0.9:
            trend_direction = "decreasing"
        else:
            trend_direction = "stable"

        return {
            "trend_direction": trend_direction,
            "first_half_avg_ms": first_half_avg,
            "second_half_avg_ms": second_half_avg,
            "total_samples": len(durations)
        }

    def get_operation_history(
        self,
        tenant_id: str,
        operation: str
    ) -> List[OperationRecord]:
        """Get operation history for a tenant.

        Args:
            tenant_id: The tenant to get history for
            operation: The operation to get history for

        Returns:
            List of OperationRecords
        """
        return self._operation_history.get(tenant_id, {}).get(operation, [])

    def get_aggregated_metrics(
        self,
        tenant_id: str,
        operation: str,
        period: str = "hourly"
    ) -> Dict[str, Any]:
        """Get aggregated metrics by time period.

        Args:
            tenant_id: The tenant to aggregate
            operation: The operation to aggregate
            period: Aggregation period ("hourly", "daily")

        Returns:
            Aggregated metrics dictionary
        """
        history = self._operation_history.get(tenant_id, {}).get(operation, [])
        if not history:
            return {"periods": []}

        # Group by period
        periods = defaultdict(list)
        for record in history:
            if period == "hourly":
                key = record.timestamp.replace(minute=0, second=0, microsecond=0)
            else:  # daily
                key = record.timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
            periods[key].append(record)

        aggregated = []
        for period_start, records in sorted(periods.items()):
            durations = [r.duration_ms for r in records]
            aggregated.append({
                "period_start": period_start.isoformat(),
                "count": len(records),
                "avg_duration_ms": statistics.mean(durations),
                "success_count": sum(1 for r in records if r.success)
            })

        return {"periods": aggregated}

    def get_peak_usage_times(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Identify peak usage times for a tenant.

        Args:
            tenant_id: The tenant to analyze

        Returns:
            List of peak usage periods
        """
        all_records = []
        for op_records in self._operation_history.get(tenant_id, {}).values():
            all_records.extend(op_records)

        if not all_records:
            return []

        # Group by hour
        hourly_counts = defaultdict(int)
        for record in all_records:
            hour = record.timestamp.hour
            hourly_counts[hour] += 1

        # Sort by count descending
        sorted_hours = sorted(hourly_counts.items(), key=lambda x: x[1], reverse=True)

        return [
            {"hour": hour, "count": count}
            for hour, count in sorted_hours[:5]  # Top 5 peak hours
        ]
