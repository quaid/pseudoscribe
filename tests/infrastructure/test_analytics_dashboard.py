"""Tests for Analytics Dashboard.

Issue: ENT-003 - Analytics Dashboard

These tests verify:
- Dashboard data aggregation
- Tenant-specific analytics
- Time-series metrics for charting
- KPI calculations
- Period comparisons
- Export functionality
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

from pseudoscribe.infrastructure.analytics_dashboard import (
    AnalyticsDashboard,
    DashboardWidget,
    WidgetType,
    DateRange,
    KPIMetric
)


class TestDashboardDataAggregation:
    """Tests for dashboard data aggregation."""

    @pytest.fixture
    def dashboard(self):
        """Create an AnalyticsDashboard instance."""
        return AnalyticsDashboard()

    def test_aggregate_tenant_metrics(self, dashboard):
        """Test aggregating metrics across a tenant."""
        # Arrange
        tenant_id = "tenant-123"
        dashboard.record_event(tenant_id, "api_call", {"endpoint": "/style/check"})
        dashboard.record_event(tenant_id, "api_call", {"endpoint": "/style/adapt"})
        dashboard.record_event(tenant_id, "feature_usage", {"feature": "style_check"})

        # Act
        metrics = dashboard.get_aggregated_metrics(tenant_id)

        # Assert
        assert metrics is not None
        assert metrics["total_events"] == 3
        assert metrics["api_calls"] == 2
        assert metrics["feature_usage"] == 1

    def test_aggregate_system_wide_metrics(self, dashboard):
        """Test aggregating metrics across all tenants (admin view)."""
        # Arrange
        dashboard.record_event("tenant-A", "api_call", {"endpoint": "/api"})
        dashboard.record_event("tenant-A", "api_call", {"endpoint": "/api"})
        dashboard.record_event("tenant-B", "api_call", {"endpoint": "/api"})
        dashboard.record_event("tenant-C", "feature_usage", {"feature": "adapt"})

        # Act
        system_metrics = dashboard.get_system_metrics()

        # Assert
        assert system_metrics["total_events"] == 4
        assert system_metrics["active_tenants"] == 3
        assert system_metrics["api_calls"] == 3
        assert system_metrics["feature_usage"] == 1

    def test_filter_by_date_range(self, dashboard):
        """Test filtering metrics by date range."""
        # Arrange
        tenant_id = "tenant-123"
        dashboard.record_event(tenant_id, "api_call", {})

        # Act
        now = datetime.now()
        date_range = DateRange(
            start=now - timedelta(hours=1),
            end=now + timedelta(hours=1)
        )
        metrics = dashboard.get_aggregated_metrics(tenant_id, date_range=date_range)

        # Assert
        assert metrics["total_events"] == 1

    def test_filter_excludes_out_of_range(self, dashboard):
        """Test that out-of-range events are excluded."""
        # Arrange
        tenant_id = "tenant-123"
        dashboard.record_event(tenant_id, "api_call", {})

        # Act - query for yesterday only
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        date_range = DateRange(
            start=yesterday - timedelta(hours=1),
            end=yesterday + timedelta(hours=1)
        )
        metrics = dashboard.get_aggregated_metrics(tenant_id, date_range=date_range)

        # Assert
        assert metrics["total_events"] == 0


class TestTimeSeriesData:
    """Tests for time-series data generation."""

    @pytest.fixture
    def dashboard(self):
        return AnalyticsDashboard()

    def test_get_time_series_hourly(self, dashboard):
        """Test getting hourly time-series data."""
        # Arrange
        tenant_id = "tenant-123"
        for _ in range(5):
            dashboard.record_event(tenant_id, "api_call", {})

        # Act
        series = dashboard.get_time_series(
            tenant_id,
            metric="api_calls",
            granularity="hourly",
            periods=24
        )

        # Assert
        assert series is not None
        assert "data_points" in series
        assert len(series["data_points"]) <= 24

    def test_get_time_series_daily(self, dashboard):
        """Test getting daily time-series data."""
        # Arrange
        tenant_id = "tenant-123"
        dashboard.record_event(tenant_id, "api_call", {})

        # Act
        series = dashboard.get_time_series(
            tenant_id,
            metric="api_calls",
            granularity="daily",
            periods=7
        )

        # Assert
        assert series is not None
        assert series["granularity"] == "daily"
        assert len(series["data_points"]) <= 7

    def test_time_series_includes_timestamps(self, dashboard):
        """Test that time-series data includes proper timestamps."""
        # Arrange
        tenant_id = "tenant-123"
        dashboard.record_event(tenant_id, "api_call", {})

        # Act
        series = dashboard.get_time_series(
            tenant_id,
            metric="api_calls",
            granularity="hourly",
            periods=2
        )

        # Assert
        for point in series["data_points"]:
            assert "timestamp" in point
            assert "value" in point


class TestKPICalculations:
    """Tests for KPI metric calculations."""

    @pytest.fixture
    def dashboard(self):
        return AnalyticsDashboard()

    def test_calculate_usage_growth(self, dashboard):
        """Test calculating usage growth KPI."""
        # Arrange
        tenant_id = "tenant-123"
        # Simulate historical data
        for i in range(20):
            dashboard.record_event(tenant_id, "api_call", {})

        # Act
        kpi = dashboard.calculate_kpi(tenant_id, KPIMetric.USAGE_GROWTH)

        # Assert
        assert kpi is not None
        assert "value" in kpi
        assert "trend" in kpi  # "up", "down", "stable"

    def test_calculate_success_rate(self, dashboard):
        """Test calculating success rate KPI."""
        # Arrange
        tenant_id = "tenant-123"
        for _ in range(8):
            dashboard.record_event(tenant_id, "api_call", {"success": True})
        for _ in range(2):
            dashboard.record_event(tenant_id, "api_call", {"success": False})

        # Act
        kpi = dashboard.calculate_kpi(tenant_id, KPIMetric.SUCCESS_RATE)

        # Assert
        assert kpi["value"] == 80.0  # 8/10 = 80%

    def test_calculate_avg_response_time(self, dashboard):
        """Test calculating average response time KPI."""
        # Arrange
        tenant_id = "tenant-123"
        dashboard.record_event(tenant_id, "api_call", {"response_time_ms": 100})
        dashboard.record_event(tenant_id, "api_call", {"response_time_ms": 200})
        dashboard.record_event(tenant_id, "api_call", {"response_time_ms": 150})

        # Act
        kpi = dashboard.calculate_kpi(tenant_id, KPIMetric.AVG_RESPONSE_TIME)

        # Assert
        assert kpi["value"] == 150.0  # (100+200+150)/3

    def test_calculate_active_users(self, dashboard):
        """Test calculating active users KPI."""
        # Arrange
        tenant_id = "tenant-123"
        dashboard.record_event(tenant_id, "api_call", {"user_id": "user-1"})
        dashboard.record_event(tenant_id, "api_call", {"user_id": "user-2"})
        dashboard.record_event(tenant_id, "api_call", {"user_id": "user-1"})  # duplicate

        # Act
        kpi = dashboard.calculate_kpi(tenant_id, KPIMetric.ACTIVE_USERS)

        # Assert
        assert kpi["value"] == 2  # 2 unique users


class TestPeriodComparison:
    """Tests for comparing metrics across periods."""

    @pytest.fixture
    def dashboard(self):
        return AnalyticsDashboard()

    def test_compare_to_previous_period(self, dashboard):
        """Test comparing current period to previous."""
        # Arrange
        tenant_id = "tenant-123"
        # Record some events
        for _ in range(10):
            dashboard.record_event(tenant_id, "api_call", {})

        # Act
        comparison = dashboard.compare_periods(
            tenant_id,
            current_period="this_week",
            previous_period="last_week"
        )

        # Assert
        assert comparison is not None
        assert "current" in comparison
        assert "previous" in comparison
        assert "change_percent" in comparison

    def test_compare_specific_date_ranges(self, dashboard):
        """Test comparing specific date ranges."""
        # Arrange
        tenant_id = "tenant-123"
        dashboard.record_event(tenant_id, "api_call", {})

        # Act
        now = datetime.now()
        current = DateRange(now - timedelta(days=7), now)
        previous = DateRange(now - timedelta(days=14), now - timedelta(days=7))

        comparison = dashboard.compare_periods(
            tenant_id,
            current_range=current,
            previous_range=previous
        )

        # Assert
        assert "current" in comparison
        assert "previous" in comparison


class TestDashboardWidgets:
    """Tests for dashboard widget configuration."""

    @pytest.fixture
    def dashboard(self):
        return AnalyticsDashboard()

    def test_create_widget(self, dashboard):
        """Test creating a dashboard widget."""
        # Arrange
        tenant_id = "tenant-123"

        # Act
        widget = dashboard.create_widget(
            tenant_id=tenant_id,
            widget_type=WidgetType.LINE_CHART,
            metric="api_calls",
            title="API Calls Over Time"
        )

        # Assert
        assert widget is not None
        assert widget.widget_type == WidgetType.LINE_CHART
        assert widget.title == "API Calls Over Time"

    def test_get_widget_data(self, dashboard):
        """Test getting data for a widget."""
        # Arrange
        tenant_id = "tenant-123"
        dashboard.record_event(tenant_id, "api_call", {})
        dashboard.record_event(tenant_id, "api_call", {})

        widget = dashboard.create_widget(
            tenant_id=tenant_id,
            widget_type=WidgetType.KPI_CARD,
            metric="total_events"
        )

        # Act
        data = dashboard.get_widget_data(widget.widget_id)

        # Assert
        assert data is not None
        assert data["value"] == 2

    def test_list_tenant_widgets(self, dashboard):
        """Test listing all widgets for a tenant."""
        # Arrange
        tenant_id = "tenant-123"
        dashboard.create_widget(tenant_id, WidgetType.LINE_CHART, "api_calls")
        dashboard.create_widget(tenant_id, WidgetType.PIE_CHART, "features")
        dashboard.create_widget(tenant_id, WidgetType.KPI_CARD, "success_rate")

        # Act
        widgets = dashboard.list_widgets(tenant_id)

        # Assert
        assert len(widgets) == 3

    def test_delete_widget(self, dashboard):
        """Test deleting a widget."""
        # Arrange
        tenant_id = "tenant-123"
        widget = dashboard.create_widget(tenant_id, WidgetType.LINE_CHART, "api_calls")

        # Act
        dashboard.delete_widget(widget.widget_id)

        # Assert
        widgets = dashboard.list_widgets(tenant_id)
        assert len(widgets) == 0


class TestTopFeatures:
    """Tests for top features analytics."""

    @pytest.fixture
    def dashboard(self):
        return AnalyticsDashboard()

    def test_get_top_features(self, dashboard):
        """Test getting top used features."""
        # Arrange
        tenant_id = "tenant-123"
        for _ in range(10):
            dashboard.record_event(tenant_id, "feature_usage", {"feature": "style_check"})
        for _ in range(5):
            dashboard.record_event(tenant_id, "feature_usage", {"feature": "style_adapt"})
        for _ in range(2):
            dashboard.record_event(tenant_id, "feature_usage", {"feature": "profile_create"})

        # Act
        top = dashboard.get_top_features(tenant_id, limit=2)

        # Assert
        assert len(top) == 2
        assert top[0]["feature"] == "style_check"
        assert top[0]["count"] == 10
        assert top[1]["feature"] == "style_adapt"

    def test_get_top_endpoints(self, dashboard):
        """Test getting top used API endpoints."""
        # Arrange
        tenant_id = "tenant-123"
        for _ in range(15):
            dashboard.record_event(tenant_id, "api_call", {"endpoint": "/api/style/check"})
        for _ in range(8):
            dashboard.record_event(tenant_id, "api_call", {"endpoint": "/api/style/adapt"})

        # Act
        top = dashboard.get_top_endpoints(tenant_id, limit=2)

        # Assert
        assert len(top) == 2
        assert top[0]["endpoint"] == "/api/style/check"
        assert top[0]["count"] == 15


class TestExportAnalytics:
    """Tests for exporting analytics data."""

    @pytest.fixture
    def dashboard(self):
        return AnalyticsDashboard()

    def test_export_dashboard_json(self, dashboard):
        """Test exporting dashboard data as JSON."""
        # Arrange
        tenant_id = "tenant-123"
        dashboard.record_event(tenant_id, "api_call", {})
        dashboard.record_event(tenant_id, "feature_usage", {"feature": "test"})

        # Act
        export = dashboard.export_dashboard(tenant_id, format="json")

        # Assert
        import json
        data = json.loads(export)
        assert "metrics" in data
        assert "generated_at" in data

    def test_export_dashboard_csv(self, dashboard):
        """Test exporting dashboard data as CSV."""
        # Arrange
        tenant_id = "tenant-123"
        dashboard.record_event(tenant_id, "api_call", {"endpoint": "/test"})

        # Act
        export = dashboard.export_dashboard(tenant_id, format="csv")

        # Assert
        assert "event_type" in export
        assert "timestamp" in export


class TestRealTimeUpdates:
    """Tests for real-time dashboard updates."""

    @pytest.fixture
    def dashboard(self):
        return AnalyticsDashboard()

    def test_get_live_metrics(self, dashboard):
        """Test getting live/real-time metrics."""
        # Arrange
        tenant_id = "tenant-123"
        for _ in range(5):
            dashboard.record_event(tenant_id, "api_call", {})

        # Act
        live = dashboard.get_live_metrics(tenant_id)

        # Assert
        assert live is not None
        assert "current_minute_events" in live
        assert "events_per_minute" in live

    def test_get_activity_feed(self, dashboard):
        """Test getting recent activity feed."""
        # Arrange
        tenant_id = "tenant-123"
        dashboard.record_event(tenant_id, "api_call", {"endpoint": "/api/test1"})
        dashboard.record_event(tenant_id, "api_call", {"endpoint": "/api/test2"})
        dashboard.record_event(tenant_id, "feature_usage", {"feature": "style_check"})

        # Act
        feed = dashboard.get_activity_feed(tenant_id, limit=10)

        # Assert
        assert len(feed) == 3
        # Most recent first
        assert feed[0]["event_type"] == "feature_usage"
