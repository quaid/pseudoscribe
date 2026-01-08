"""Tests for Usage Tracking functionality.

Issue: ENT-001 - Usage Tracking

These tests verify:
- API call tracking by tenant
- Feature usage tracking
- Usage quotas and limits
- Usage summaries and reports
- Multi-tenant isolation
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock, patch
from typing import Dict, Any

from pseudoscribe.infrastructure.usage_tracker import (
    UsageTracker,
    UsageEvent,
    UsageQuota,
    QuotaExceededError
)


class TestUsageEventTracking:
    """Tests for basic usage event tracking."""

    @pytest.fixture
    def usage_tracker(self):
        """Create a UsageTracker instance for testing."""
        return UsageTracker()

    def test_track_api_call(self, usage_tracker):
        """Test tracking a single API call."""
        # Arrange
        tenant_id = "tenant-123"
        endpoint = "/api/v1/style/check"

        # Act
        usage_tracker.track_api_call(
            tenant_id=tenant_id,
            endpoint=endpoint,
            method="POST"
        )

        # Assert
        events = usage_tracker.get_events(tenant_id)
        assert len(events) == 1
        assert events[0].event_type == "api_call"
        assert events[0].tenant_id == tenant_id
        assert events[0].metadata["endpoint"] == endpoint

    def test_track_feature_usage(self, usage_tracker):
        """Test tracking feature usage."""
        # Arrange
        tenant_id = "tenant-123"
        feature = "style_check"

        # Act
        usage_tracker.track_feature_usage(
            tenant_id=tenant_id,
            feature=feature,
            metadata={"profile_id": "formal-style"}
        )

        # Assert
        events = usage_tracker.get_events(tenant_id, event_type="feature_usage")
        assert len(events) == 1
        assert events[0].metadata["feature"] == feature

    def test_track_multiple_events(self, usage_tracker):
        """Test tracking multiple events for a tenant."""
        # Arrange
        tenant_id = "tenant-123"

        # Act
        usage_tracker.track_api_call(tenant_id, "/api/v1/style/check", "POST")
        usage_tracker.track_api_call(tenant_id, "/api/v1/style/adapt", "POST")
        usage_tracker.track_feature_usage(tenant_id, "style_adaptation")

        # Assert
        all_events = usage_tracker.get_events(tenant_id)
        assert len(all_events) == 3

        api_events = usage_tracker.get_events(tenant_id, event_type="api_call")
        assert len(api_events) == 2

    def test_track_events_with_timestamp(self, usage_tracker):
        """Test that events are tracked with timestamps."""
        # Arrange
        tenant_id = "tenant-123"
        before = datetime.now()

        # Act
        usage_tracker.track_api_call(tenant_id, "/api/v1/test", "GET")

        # Assert
        events = usage_tracker.get_events(tenant_id)
        assert len(events) == 1
        assert events[0].timestamp >= before
        assert events[0].timestamp <= datetime.now()


class TestMultiTenantIsolation:
    """Tests for multi-tenant usage isolation."""

    @pytest.fixture
    def usage_tracker(self):
        return UsageTracker()

    def test_tenant_isolation(self, usage_tracker):
        """Test that usage is isolated between tenants."""
        # Arrange
        tenant_a = "tenant-A"
        tenant_b = "tenant-B"

        # Act
        usage_tracker.track_api_call(tenant_a, "/api/v1/a", "GET")
        usage_tracker.track_api_call(tenant_a, "/api/v1/a", "GET")
        usage_tracker.track_api_call(tenant_b, "/api/v1/b", "POST")

        # Assert
        events_a = usage_tracker.get_events(tenant_a)
        events_b = usage_tracker.get_events(tenant_b)

        assert len(events_a) == 2
        assert len(events_b) == 1
        assert all(e.tenant_id == tenant_a for e in events_a)
        assert all(e.tenant_id == tenant_b for e in events_b)

    def test_get_all_tenants(self, usage_tracker):
        """Test getting list of all tenants with usage."""
        # Arrange
        usage_tracker.track_api_call("tenant-1", "/api", "GET")
        usage_tracker.track_api_call("tenant-2", "/api", "GET")
        usage_tracker.track_api_call("tenant-3", "/api", "GET")

        # Act
        tenants = usage_tracker.get_active_tenants()

        # Assert
        assert len(tenants) == 3
        assert "tenant-1" in tenants
        assert "tenant-2" in tenants
        assert "tenant-3" in tenants


class TestUsageQuotas:
    """Tests for usage quota management."""

    @pytest.fixture
    def usage_tracker(self):
        return UsageTracker()

    def test_set_quota(self, usage_tracker):
        """Test setting a usage quota for a tenant."""
        # Arrange
        tenant_id = "tenant-123"

        # Act
        usage_tracker.set_quota(
            tenant_id=tenant_id,
            quota_type="api_calls",
            limit=1000,
            period="monthly"
        )

        # Assert
        quota = usage_tracker.get_quota(tenant_id, "api_calls")
        assert quota is not None
        assert quota.limit == 1000
        assert quota.period == "monthly"

    def test_check_quota_within_limit(self, usage_tracker):
        """Test quota check when within limit."""
        # Arrange
        tenant_id = "tenant-123"
        usage_tracker.set_quota(tenant_id, "api_calls", limit=100, period="daily")

        # Track some usage
        for _ in range(50):
            usage_tracker.track_api_call(tenant_id, "/api", "GET")

        # Act
        is_allowed = usage_tracker.check_quota(tenant_id, "api_calls")

        # Assert
        assert is_allowed is True

    def test_check_quota_exceeded(self, usage_tracker):
        """Test quota check when limit exceeded."""
        # Arrange
        tenant_id = "tenant-123"
        usage_tracker.set_quota(tenant_id, "api_calls", limit=10, period="daily")

        # Track usage up to limit
        for _ in range(10):
            usage_tracker.track_api_call(tenant_id, "/api", "GET")

        # Act
        is_allowed = usage_tracker.check_quota(tenant_id, "api_calls")

        # Assert
        assert is_allowed is False

    def test_track_with_quota_enforcement(self, usage_tracker):
        """Test tracking with quota enforcement enabled."""
        # Arrange
        tenant_id = "tenant-123"
        usage_tracker.set_quota(tenant_id, "api_calls", limit=5, period="daily")

        # Act & Assert - should work for first 5 calls
        for i in range(5):
            usage_tracker.track_api_call(
                tenant_id, "/api", "GET",
                enforce_quota=True
            )

        # 6th call should raise exception
        with pytest.raises(QuotaExceededError):
            usage_tracker.track_api_call(
                tenant_id, "/api", "GET",
                enforce_quota=True
            )

    def test_get_quota_usage(self, usage_tracker):
        """Test getting current quota usage."""
        # Arrange
        tenant_id = "tenant-123"
        usage_tracker.set_quota(tenant_id, "api_calls", limit=100, period="daily")

        for _ in range(25):
            usage_tracker.track_api_call(tenant_id, "/api", "GET")

        # Act
        usage = usage_tracker.get_quota_usage(tenant_id, "api_calls")

        # Assert
        assert usage["current"] == 25
        assert usage["limit"] == 100
        assert usage["remaining"] == 75
        assert usage["percentage"] == 25.0


class TestUsageSummaries:
    """Tests for usage summary and reporting."""

    @pytest.fixture
    def usage_tracker(self):
        return UsageTracker()

    def test_get_usage_summary(self, usage_tracker):
        """Test getting a usage summary for a tenant."""
        # Arrange
        tenant_id = "tenant-123"
        usage_tracker.track_api_call(tenant_id, "/api/v1/style/check", "POST")
        usage_tracker.track_api_call(tenant_id, "/api/v1/style/adapt", "POST")
        usage_tracker.track_feature_usage(tenant_id, "style_check")
        usage_tracker.track_feature_usage(tenant_id, "style_adaptation")
        usage_tracker.track_feature_usage(tenant_id, "style_check")

        # Act
        summary = usage_tracker.get_usage_summary(tenant_id)

        # Assert
        assert summary is not None
        assert summary["total_events"] == 5
        assert summary["api_calls"] == 2
        assert summary["feature_usage"] == 3
        assert "style_check" in summary["features"]
        assert summary["features"]["style_check"] == 2

    def test_get_usage_by_time_period(self, usage_tracker):
        """Test getting usage for a specific time period."""
        # Arrange
        tenant_id = "tenant-123"
        usage_tracker.track_api_call(tenant_id, "/api", "GET")

        # Act
        now = datetime.now()
        yesterday = now - timedelta(days=1)

        summary_today = usage_tracker.get_usage_summary(
            tenant_id,
            start_time=now - timedelta(hours=1)
        )
        summary_yesterday = usage_tracker.get_usage_summary(
            tenant_id,
            start_time=yesterday,
            end_time=yesterday + timedelta(hours=1)
        )

        # Assert
        assert summary_today["total_events"] == 1
        assert summary_yesterday["total_events"] == 0

    def test_get_top_features(self, usage_tracker):
        """Test getting most used features."""
        # Arrange
        tenant_id = "tenant-123"
        # Track various features with different counts
        for _ in range(10):
            usage_tracker.track_feature_usage(tenant_id, "style_check")
        for _ in range(5):
            usage_tracker.track_feature_usage(tenant_id, "style_adaptation")
        for _ in range(3):
            usage_tracker.track_feature_usage(tenant_id, "profile_creation")

        # Act
        top_features = usage_tracker.get_top_features(tenant_id, limit=2)

        # Assert
        assert len(top_features) == 2
        assert top_features[0]["feature"] == "style_check"
        assert top_features[0]["count"] == 10
        assert top_features[1]["feature"] == "style_adaptation"
        assert top_features[1]["count"] == 5

    def test_get_usage_trends(self, usage_tracker):
        """Test getting usage trends over time."""
        # Arrange
        tenant_id = "tenant-123"
        # Track some usage
        usage_tracker.track_api_call(tenant_id, "/api", "GET")
        usage_tracker.track_api_call(tenant_id, "/api", "POST")

        # Act
        trends = usage_tracker.get_usage_trends(
            tenant_id,
            period="hourly",
            num_periods=24
        )

        # Assert
        assert trends is not None
        assert "periods" in trends
        assert len(trends["periods"]) <= 24


class TestUsageExport:
    """Tests for usage data export."""

    @pytest.fixture
    def usage_tracker(self):
        return UsageTracker()

    def test_export_usage_json(self, usage_tracker):
        """Test exporting usage data as JSON."""
        # Arrange
        tenant_id = "tenant-123"
        usage_tracker.track_api_call(tenant_id, "/api/v1/test", "GET")
        usage_tracker.track_feature_usage(tenant_id, "style_check")

        # Act
        export_data = usage_tracker.export_usage(tenant_id, format="json")

        # Assert
        assert export_data is not None
        import json
        data = json.loads(export_data)
        assert "events" in data
        assert len(data["events"]) == 2

    def test_export_usage_csv(self, usage_tracker):
        """Test exporting usage data as CSV."""
        # Arrange
        tenant_id = "tenant-123"
        usage_tracker.track_api_call(tenant_id, "/api/v1/test", "GET")

        # Act
        export_data = usage_tracker.export_usage(tenant_id, format="csv")

        # Assert
        assert export_data is not None
        assert "tenant_id" in export_data
        assert "event_type" in export_data


class TestUsageTrackerIntegration:
    """Integration tests for usage tracking with other components."""

    @pytest.fixture
    def usage_tracker(self):
        return UsageTracker()

    def test_track_with_metrics_collector(self, usage_tracker):
        """Test that usage tracking integrates with metrics collector."""
        # Arrange
        tenant_id = "tenant-123"

        # Act
        usage_tracker.track_api_call(
            tenant_id, "/api/v1/style/check", "POST",
            response_time_ms=150
        )

        # Assert
        # Usage should be recorded
        events = usage_tracker.get_events(tenant_id)
        assert len(events) == 1
        assert events[0].metadata.get("response_time_ms") == 150

    def test_reset_usage_for_period(self, usage_tracker):
        """Test resetting usage counts for a new period."""
        # Arrange
        tenant_id = "tenant-123"
        usage_tracker.set_quota(tenant_id, "api_calls", limit=100, period="daily")

        for _ in range(50):
            usage_tracker.track_api_call(tenant_id, "/api", "GET")

        # Act
        usage_tracker.reset_quota_usage(tenant_id, "api_calls")

        # Assert
        usage = usage_tracker.get_quota_usage(tenant_id, "api_calls")
        assert usage["current"] == 0
