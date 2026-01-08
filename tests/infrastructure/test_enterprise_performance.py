"""Tests for Enterprise Performance Monitoring.

Issue: ENT-002 - Performance Monitoring

These tests verify:
- Multi-tenant performance isolation
- Performance alerting with configurable thresholds
- Historical performance data retention
- Performance baseline comparison
- Anomaly detection
- Performance reporting per tenant
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from typing import Dict, Any

from pseudoscribe.infrastructure.enterprise_performance import (
    EnterprisePerformanceMonitor,
    PerformanceAlert,
    PerformanceBaseline,
    AlertLevel,
    TenantPerformanceConfig
)


class TestMultiTenantPerformance:
    """Tests for multi-tenant performance isolation."""

    @pytest.fixture
    def monitor(self):
        """Create an EnterprisePerformanceMonitor instance."""
        return EnterprisePerformanceMonitor()

    def test_track_tenant_performance(self, monitor):
        """Test tracking performance metrics per tenant."""
        # Arrange
        tenant_id = "tenant-123"
        operation = "style_check"

        # Act
        monitor.track_operation(
            tenant_id=tenant_id,
            operation=operation,
            duration_ms=150,
            success=True
        )

        # Assert
        metrics = monitor.get_tenant_metrics(tenant_id)
        assert metrics is not None
        assert operation in metrics["operations"]
        assert metrics["operations"][operation]["count"] == 1
        assert metrics["operations"][operation]["avg_duration_ms"] == 150

    def test_tenant_isolation(self, monitor):
        """Test that performance data is isolated between tenants."""
        # Arrange
        tenant_a = "tenant-A"
        tenant_b = "tenant-B"

        # Act
        monitor.track_operation(tenant_a, "op1", 100, True)
        monitor.track_operation(tenant_a, "op1", 200, True)
        monitor.track_operation(tenant_b, "op1", 50, True)

        # Assert
        metrics_a = monitor.get_tenant_metrics(tenant_a)
        metrics_b = monitor.get_tenant_metrics(tenant_b)

        assert metrics_a["operations"]["op1"]["count"] == 2
        assert metrics_b["operations"]["op1"]["count"] == 1
        assert metrics_a["operations"]["op1"]["avg_duration_ms"] == 150  # (100+200)/2
        assert metrics_b["operations"]["op1"]["avg_duration_ms"] == 50

    def test_track_multiple_operations(self, monitor):
        """Test tracking multiple operation types."""
        # Arrange
        tenant_id = "tenant-123"

        # Act
        monitor.track_operation(tenant_id, "style_check", 100, True)
        monitor.track_operation(tenant_id, "style_adapt", 200, True)
        monitor.track_operation(tenant_id, "profile_create", 50, True)

        # Assert
        metrics = monitor.get_tenant_metrics(tenant_id)
        assert len(metrics["operations"]) == 3
        assert "style_check" in metrics["operations"]
        assert "style_adapt" in metrics["operations"]
        assert "profile_create" in metrics["operations"]

    def test_track_operation_failures(self, monitor):
        """Test tracking operation failures."""
        # Arrange
        tenant_id = "tenant-123"

        # Act
        monitor.track_operation(tenant_id, "style_check", 100, True)
        monitor.track_operation(tenant_id, "style_check", 50, False)
        monitor.track_operation(tenant_id, "style_check", 150, True)

        # Assert
        metrics = monitor.get_tenant_metrics(tenant_id)
        op_metrics = metrics["operations"]["style_check"]
        assert op_metrics["count"] == 3
        assert op_metrics["success_count"] == 2
        assert op_metrics["failure_count"] == 1
        assert op_metrics["success_rate"] == pytest.approx(66.67, rel=0.01)


class TestPerformanceAlerting:
    """Tests for performance alerting."""

    @pytest.fixture
    def monitor(self):
        return EnterprisePerformanceMonitor()

    def test_configure_alert_threshold(self, monitor):
        """Test configuring alert thresholds."""
        # Arrange
        tenant_id = "tenant-123"
        config = TenantPerformanceConfig(
            response_time_warning_ms=500,
            response_time_critical_ms=1000,
            error_rate_warning=0.05,
            error_rate_critical=0.10
        )

        # Act
        monitor.configure_tenant(tenant_id, config)

        # Assert
        stored_config = monitor.get_tenant_config(tenant_id)
        assert stored_config.response_time_warning_ms == 500
        assert stored_config.response_time_critical_ms == 1000

    def test_generate_warning_alert(self, monitor):
        """Test generating a warning alert when threshold is exceeded."""
        # Arrange
        tenant_id = "tenant-123"
        config = TenantPerformanceConfig(
            response_time_warning_ms=100,
            response_time_critical_ms=500
        )
        monitor.configure_tenant(tenant_id, config)

        # Act - track an operation that exceeds warning threshold
        monitor.track_operation(tenant_id, "slow_op", 250, True)

        # Assert
        alerts = monitor.get_alerts(tenant_id)
        assert len(alerts) >= 1
        assert any(a.level == AlertLevel.WARNING for a in alerts)
        assert any("response time" in a.message.lower() for a in alerts)

    def test_generate_critical_alert(self, monitor):
        """Test generating a critical alert when threshold is exceeded."""
        # Arrange
        tenant_id = "tenant-123"
        config = TenantPerformanceConfig(
            response_time_warning_ms=100,
            response_time_critical_ms=500
        )
        monitor.configure_tenant(tenant_id, config)

        # Act - track an operation that exceeds critical threshold
        monitor.track_operation(tenant_id, "very_slow_op", 750, True)

        # Assert
        alerts = monitor.get_alerts(tenant_id)
        assert len(alerts) >= 1
        assert any(a.level == AlertLevel.CRITICAL for a in alerts)

    def test_error_rate_alert(self, monitor):
        """Test generating alert for high error rate."""
        # Arrange
        tenant_id = "tenant-123"
        config = TenantPerformanceConfig(
            error_rate_warning=0.10,
            error_rate_critical=0.25
        )
        monitor.configure_tenant(tenant_id, config)

        # Act - track operations with 15% failure rate (between warning and critical)
        for _ in range(17):
            monitor.track_operation(tenant_id, "failing_op", 100, True)
        for _ in range(3):
            monitor.track_operation(tenant_id, "failing_op", 100, False)

        # Assert - 15% error rate should trigger warning (>10%, <25%)
        alerts = monitor.get_alerts(tenant_id)
        assert any(a.level == AlertLevel.WARNING and "error rate" in a.message.lower() for a in alerts)

    def test_clear_alerts(self, monitor):
        """Test clearing alerts for a tenant."""
        # Arrange
        tenant_id = "tenant-123"
        config = TenantPerformanceConfig(response_time_critical_ms=100)
        monitor.configure_tenant(tenant_id, config)
        monitor.track_operation(tenant_id, "slow_op", 500, True)

        # Verify alert exists
        assert len(monitor.get_alerts(tenant_id)) > 0

        # Act
        monitor.clear_alerts(tenant_id)

        # Assert
        assert len(monitor.get_alerts(tenant_id)) == 0


class TestPerformanceBaselines:
    """Tests for performance baseline management."""

    @pytest.fixture
    def monitor(self):
        return EnterprisePerformanceMonitor()

    def test_establish_baseline(self, monitor):
        """Test establishing a performance baseline."""
        # Arrange
        tenant_id = "tenant-123"
        operation = "style_check"

        # Track enough operations to establish baseline
        for duration in [100, 110, 105, 95, 108, 102, 98, 112, 106, 104]:
            monitor.track_operation(tenant_id, operation, duration, True)

        # Act
        baseline = monitor.establish_baseline(tenant_id, operation)

        # Assert
        assert baseline is not None
        assert baseline.operation == operation
        assert baseline.avg_duration_ms == pytest.approx(104.0, rel=0.01)
        assert baseline.min_duration_ms == 95
        assert baseline.max_duration_ms == 112

    def test_compare_to_baseline(self, monitor):
        """Test comparing current performance to baseline."""
        # Arrange
        tenant_id = "tenant-123"
        operation = "style_check"

        # Establish baseline with ~100ms operations
        for _ in range(10):
            monitor.track_operation(tenant_id, operation, 100, True)
        monitor.establish_baseline(tenant_id, operation)

        # Clear metrics and track slower operations
        monitor.reset_tenant_metrics(tenant_id)
        for _ in range(5):
            monitor.track_operation(tenant_id, operation, 200, True)  # 2x slower

        # Act
        comparison = monitor.compare_to_baseline(tenant_id, operation)

        # Assert
        assert comparison is not None
        assert comparison["deviation_percent"] > 50  # Significant deviation
        assert comparison["is_degraded"] is True

    def test_baseline_not_enough_data(self, monitor):
        """Test baseline establishment with insufficient data."""
        # Arrange
        tenant_id = "tenant-123"
        monitor.track_operation(tenant_id, "op", 100, True)
        monitor.track_operation(tenant_id, "op", 100, True)

        # Act
        baseline = monitor.establish_baseline(tenant_id, "op")

        # Assert - should return None with insufficient data
        assert baseline is None


class TestAnomalyDetection:
    """Tests for performance anomaly detection."""

    @pytest.fixture
    def monitor(self):
        return EnterprisePerformanceMonitor()

    def test_detect_response_time_anomaly(self, monitor):
        """Test detection of response time anomalies."""
        # Arrange
        tenant_id = "tenant-123"
        operation = "style_check"

        # Establish baseline
        for _ in range(10):
            monitor.track_operation(tenant_id, operation, 100, True)
        monitor.establish_baseline(tenant_id, operation)

        # Act - introduce anomaly
        monitor.track_operation(tenant_id, operation, 500, True)  # 5x slower

        # Assert
        anomalies = monitor.detect_anomalies(tenant_id)
        assert len(anomalies) >= 1
        assert any(a["type"] == "response_time_spike" for a in anomalies)

    def test_detect_error_rate_anomaly(self, monitor):
        """Test detection of error rate anomalies."""
        # Arrange
        tenant_id = "tenant-123"
        operation = "style_check"

        # Establish baseline with low error rate
        for _ in range(20):
            monitor.track_operation(tenant_id, operation, 100, True)
        monitor.establish_baseline(tenant_id, operation)

        # Clear and introduce failures
        monitor.reset_tenant_metrics(tenant_id)
        for _ in range(5):
            monitor.track_operation(tenant_id, operation, 100, False)

        # Act
        anomalies = monitor.detect_anomalies(tenant_id)

        # Assert
        assert any(a["type"] == "error_rate_spike" for a in anomalies)

    def test_no_anomalies_normal_operation(self, monitor):
        """Test that no anomalies are detected during normal operation."""
        # Arrange
        tenant_id = "tenant-123"
        operation = "style_check"

        # Track consistent operations
        for _ in range(10):
            monitor.track_operation(tenant_id, operation, 100, True)
        monitor.establish_baseline(tenant_id, operation)

        # Track more consistent operations
        for _ in range(5):
            monitor.track_operation(tenant_id, operation, 105, True)

        # Act
        anomalies = monitor.detect_anomalies(tenant_id)

        # Assert
        assert len(anomalies) == 0


class TestPerformanceReporting:
    """Tests for performance reporting."""

    @pytest.fixture
    def monitor(self):
        return EnterprisePerformanceMonitor()

    def test_generate_performance_report(self, monitor):
        """Test generating a comprehensive performance report."""
        # Arrange
        tenant_id = "tenant-123"
        monitor.track_operation(tenant_id, "style_check", 100, True)
        monitor.track_operation(tenant_id, "style_check", 150, True)
        monitor.track_operation(tenant_id, "style_adapt", 200, True)
        monitor.track_operation(tenant_id, "profile_create", 50, False)

        # Act
        report = monitor.generate_report(tenant_id)

        # Assert
        assert report is not None
        assert "summary" in report
        assert "operations" in report
        assert report["summary"]["total_operations"] == 4
        assert report["summary"]["total_failures"] == 1
        assert report["summary"]["overall_success_rate"] == 75.0

    def test_report_time_filtering(self, monitor):
        """Test filtering report by time period."""
        # Arrange
        tenant_id = "tenant-123"
        monitor.track_operation(tenant_id, "op", 100, True)

        # Act
        now = datetime.now()
        yesterday = now - timedelta(days=1)

        report_today = monitor.generate_report(
            tenant_id,
            start_time=now - timedelta(hours=1)
        )
        report_yesterday = monitor.generate_report(
            tenant_id,
            start_time=yesterday,
            end_time=yesterday + timedelta(hours=1)
        )

        # Assert
        assert report_today["summary"]["total_operations"] == 1
        assert report_yesterday["summary"]["total_operations"] == 0

    def test_export_report_json(self, monitor):
        """Test exporting performance report as JSON."""
        # Arrange
        tenant_id = "tenant-123"
        monitor.track_operation(tenant_id, "style_check", 100, True)

        # Act
        export_data = monitor.export_report(tenant_id, format="json")

        # Assert
        import json
        data = json.loads(export_data)
        assert "summary" in data
        assert "operations" in data

    def test_get_trending_metrics(self, monitor):
        """Test getting trending performance metrics."""
        # Arrange
        tenant_id = "tenant-123"
        operation = "style_check"

        # Track operations
        for i in range(10):
            monitor.track_operation(tenant_id, operation, 100 + i * 10, True)

        # Act
        trends = monitor.get_trending_metrics(tenant_id, operation)

        # Assert
        assert trends is not None
        assert "trend_direction" in trends
        assert trends["trend_direction"] == "increasing"  # Response times increasing


class TestHistoricalDataRetention:
    """Tests for historical data retention."""

    @pytest.fixture
    def monitor(self):
        return EnterprisePerformanceMonitor()

    def test_retain_historical_data(self, monitor):
        """Test that historical data is retained."""
        # Arrange
        tenant_id = "tenant-123"

        # Track operations
        for i in range(100):
            monitor.track_operation(tenant_id, "op", 100 + i, True)

        # Act
        history = monitor.get_operation_history(tenant_id, "op")

        # Assert
        assert history is not None
        assert len(history) == 100

    def test_data_aggregation(self, monitor):
        """Test aggregation of historical data."""
        # Arrange
        tenant_id = "tenant-123"

        # Track many operations
        for i in range(50):
            monitor.track_operation(tenant_id, "op", 100, True)

        # Act
        aggregated = monitor.get_aggregated_metrics(
            tenant_id, "op",
            period="hourly"
        )

        # Assert
        assert aggregated is not None
        assert "periods" in aggregated

    def test_get_peak_usage_times(self, monitor):
        """Test identifying peak usage times."""
        # Arrange
        tenant_id = "tenant-123"

        # Track operations at different "times"
        for _ in range(20):
            monitor.track_operation(tenant_id, "op", 100, True)

        # Act
        peak_times = monitor.get_peak_usage_times(tenant_id)

        # Assert
        assert peak_times is not None
        assert isinstance(peak_times, list)
