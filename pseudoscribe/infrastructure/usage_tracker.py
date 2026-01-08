"""Usage Tracking for Multi-Tenant API.

Issue: ENT-001 - Usage Tracking

This module provides comprehensive usage tracking including:
- API call tracking by tenant
- Feature usage tracking
- Usage quotas and limits
- Usage summaries and reports
- Multi-tenant isolation
"""

import json
import csv
import io
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional
from collections import defaultdict


@dataclass
class UsageEvent:
    """Represents a single usage event."""

    event_type: str
    tenant_id: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_type": self.event_type,
            "tenant_id": self.tenant_id,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class UsageQuota:
    """Represents a usage quota configuration."""

    quota_type: str
    limit: int
    period: str  # "daily", "monthly", "hourly"
    tenant_id: str
    created_at: datetime = field(default_factory=datetime.now)


class QuotaExceededError(Exception):
    """Raised when a usage quota is exceeded."""

    def __init__(self, tenant_id: str, quota_type: str, limit: int, current: int):
        self.tenant_id = tenant_id
        self.quota_type = quota_type
        self.limit = limit
        self.current = current
        super().__init__(
            f"Quota exceeded for tenant {tenant_id}: {quota_type} "
            f"(limit: {limit}, current: {current})"
        )


class UsageTracker:
    """Tracks API and feature usage across tenants."""

    def __init__(self):
        """Initialize the usage tracker."""
        self._events: Dict[str, List[UsageEvent]] = defaultdict(list)
        self._quotas: Dict[str, Dict[str, UsageQuota]] = defaultdict(dict)
        self._quota_usage: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    def track_api_call(
        self,
        tenant_id: str,
        endpoint: str,
        method: str,
        enforce_quota: bool = False,
        response_time_ms: Optional[int] = None
    ) -> UsageEvent:
        """Track an API call for a tenant.

        Args:
            tenant_id: The tenant making the call
            endpoint: The API endpoint called
            method: HTTP method (GET, POST, etc.)
            enforce_quota: Whether to enforce quota limits
            response_time_ms: Optional response time in milliseconds

        Returns:
            The created UsageEvent

        Raises:
            QuotaExceededError: If enforce_quota is True and quota is exceeded
        """
        if enforce_quota and not self.check_quota(tenant_id, "api_calls"):
            quota = self._quotas[tenant_id].get("api_calls")
            current = self._count_events_for_quota(tenant_id, "api_calls")
            raise QuotaExceededError(
                tenant_id=tenant_id,
                quota_type="api_calls",
                limit=quota.limit if quota else 0,
                current=current
            )

        metadata = {
            "endpoint": endpoint,
            "method": method
        }
        if response_time_ms is not None:
            metadata["response_time_ms"] = response_time_ms

        event = UsageEvent(
            event_type="api_call",
            tenant_id=tenant_id,
            timestamp=datetime.now(),
            metadata=metadata
        )
        self._events[tenant_id].append(event)
        return event

    def track_feature_usage(
        self,
        tenant_id: str,
        feature: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UsageEvent:
        """Track feature usage for a tenant.

        Args:
            tenant_id: The tenant using the feature
            feature: The feature name
            metadata: Optional additional metadata

        Returns:
            The created UsageEvent
        """
        event_metadata = {"feature": feature}
        if metadata:
            event_metadata.update(metadata)

        event = UsageEvent(
            event_type="feature_usage",
            tenant_id=tenant_id,
            timestamp=datetime.now(),
            metadata=event_metadata
        )
        self._events[tenant_id].append(event)
        return event

    def get_events(
        self,
        tenant_id: str,
        event_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[UsageEvent]:
        """Get usage events for a tenant.

        Args:
            tenant_id: The tenant to get events for
            event_type: Optional filter by event type
            start_time: Optional start time filter
            end_time: Optional end time filter

        Returns:
            List of matching UsageEvents
        """
        events = self._events.get(tenant_id, [])

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if start_time:
            events = [e for e in events if e.timestamp >= start_time]

        if end_time:
            events = [e for e in events if e.timestamp <= end_time]

        return events

    def get_active_tenants(self) -> List[str]:
        """Get list of all tenants with usage data.

        Returns:
            List of tenant IDs
        """
        return list(self._events.keys())

    def set_quota(
        self,
        tenant_id: str,
        quota_type: str,
        limit: int,
        period: str
    ) -> UsageQuota:
        """Set a usage quota for a tenant.

        Args:
            tenant_id: The tenant to set quota for
            quota_type: Type of quota (e.g., "api_calls")
            limit: Maximum allowed usage
            period: Time period ("daily", "monthly", "hourly")

        Returns:
            The created UsageQuota
        """
        quota = UsageQuota(
            quota_type=quota_type,
            limit=limit,
            period=period,
            tenant_id=tenant_id
        )
        self._quotas[tenant_id][quota_type] = quota
        return quota

    def get_quota(self, tenant_id: str, quota_type: str) -> Optional[UsageQuota]:
        """Get a quota configuration for a tenant.

        Args:
            tenant_id: The tenant to get quota for
            quota_type: Type of quota

        Returns:
            UsageQuota if found, None otherwise
        """
        return self._quotas.get(tenant_id, {}).get(quota_type)

    def _get_period_start(self, period: str) -> datetime:
        """Get the start time for a quota period.

        Args:
            period: The period type ("hourly", "daily", "monthly")

        Returns:
            The start datetime for the period
        """
        now = datetime.now()
        if period == "hourly":
            return now.replace(minute=0, second=0, microsecond=0)
        elif period == "daily":
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "monthly":
            return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return now

    def _count_events_for_quota(self, tenant_id: str, quota_type: str) -> int:
        """Count events relevant to a quota type within the current period.

        Args:
            tenant_id: The tenant to count for
            quota_type: Type of quota

        Returns:
            Number of events in the current period
        """
        quota = self.get_quota(tenant_id, quota_type)
        if not quota:
            return 0

        period_start = self._get_period_start(quota.period)

        # Map quota types to event types
        if quota_type == "api_calls":
            events = self.get_events(tenant_id, event_type="api_call", start_time=period_start)
        else:
            events = self.get_events(tenant_id, start_time=period_start)

        return len(events)

    def check_quota(self, tenant_id: str, quota_type: str) -> bool:
        """Check if a tenant is within their quota.

        Args:
            tenant_id: The tenant to check
            quota_type: Type of quota to check

        Returns:
            True if within quota, False if exceeded
        """
        quota = self.get_quota(tenant_id, quota_type)
        if not quota:
            return True  # No quota means unlimited

        current = self._count_events_for_quota(tenant_id, quota_type)
        return current < quota.limit

    def get_quota_usage(self, tenant_id: str, quota_type: str) -> Dict[str, Any]:
        """Get current quota usage for a tenant.

        Args:
            tenant_id: The tenant to get usage for
            quota_type: Type of quota

        Returns:
            Dictionary with current, limit, remaining, and percentage
        """
        quota = self.get_quota(tenant_id, quota_type)
        if not quota:
            return {"current": 0, "limit": 0, "remaining": 0, "percentage": 0.0}

        current = self._count_events_for_quota(tenant_id, quota_type)
        remaining = max(0, quota.limit - current)
        percentage = (current / quota.limit * 100) if quota.limit > 0 else 0.0

        return {
            "current": current,
            "limit": quota.limit,
            "remaining": remaining,
            "percentage": percentage
        }

    def reset_quota_usage(self, tenant_id: str, quota_type: str) -> None:
        """Reset quota usage for a tenant (clear events for current period).

        Args:
            tenant_id: The tenant to reset
            quota_type: Type of quota to reset
        """
        quota = self.get_quota(tenant_id, quota_type)
        if not quota:
            return

        period_start = self._get_period_start(quota.period)

        # Filter out events from current period for this quota type
        if quota_type == "api_calls":
            self._events[tenant_id] = [
                e for e in self._events.get(tenant_id, [])
                if not (e.event_type == "api_call" and e.timestamp >= period_start)
            ]

    def get_usage_summary(
        self,
        tenant_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get a usage summary for a tenant.

        Args:
            tenant_id: The tenant to summarize
            start_time: Optional start time filter
            end_time: Optional end time filter

        Returns:
            Dictionary with usage summary statistics
        """
        events = self.get_events(tenant_id, start_time=start_time, end_time=end_time)

        api_calls = [e for e in events if e.event_type == "api_call"]
        feature_events = [e for e in events if e.event_type == "feature_usage"]

        # Count features
        features: Dict[str, int] = defaultdict(int)
        for event in feature_events:
            feature_name = event.metadata.get("feature", "unknown")
            features[feature_name] += 1

        return {
            "total_events": len(events),
            "api_calls": len(api_calls),
            "feature_usage": len(feature_events),
            "features": dict(features)
        }

    def get_top_features(
        self,
        tenant_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get the most used features for a tenant.

        Args:
            tenant_id: The tenant to analyze
            limit: Maximum number of features to return

        Returns:
            List of features with counts, sorted by usage
        """
        events = self.get_events(tenant_id, event_type="feature_usage")

        feature_counts: Dict[str, int] = defaultdict(int)
        for event in events:
            feature_name = event.metadata.get("feature", "unknown")
            feature_counts[feature_name] += 1

        sorted_features = sorted(
            feature_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]

        return [
            {"feature": name, "count": count}
            for name, count in sorted_features
        ]

    def get_usage_trends(
        self,
        tenant_id: str,
        period: str = "hourly",
        num_periods: int = 24
    ) -> Dict[str, Any]:
        """Get usage trends over time.

        Args:
            tenant_id: The tenant to analyze
            period: Time period granularity ("hourly", "daily")
            num_periods: Number of periods to include

        Returns:
            Dictionary with trend data
        """
        now = datetime.now()

        if period == "hourly":
            delta = timedelta(hours=1)
        elif period == "daily":
            delta = timedelta(days=1)
        else:
            delta = timedelta(hours=1)

        periods = []
        for i in range(num_periods):
            period_start = now - (delta * (num_periods - i))
            period_end = period_start + delta

            events = self.get_events(
                tenant_id,
                start_time=period_start,
                end_time=period_end
            )

            periods.append({
                "start": period_start.isoformat(),
                "end": period_end.isoformat(),
                "count": len(events)
            })

        # Filter out empty periods at the start
        periods = [p for p in periods if p["count"] > 0] or periods[-1:]

        return {"periods": periods}

    def export_usage(
        self,
        tenant_id: str,
        format: str = "json",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> str:
        """Export usage data in the specified format.

        Args:
            tenant_id: The tenant to export
            format: Output format ("json" or "csv")
            start_time: Optional start time filter
            end_time: Optional end time filter

        Returns:
            Exported data as a string
        """
        events = self.get_events(tenant_id, start_time=start_time, end_time=end_time)

        if format == "json":
            return json.dumps({
                "events": [e.to_dict() for e in events],
                "tenant_id": tenant_id,
                "export_time": datetime.now().isoformat()
            }, indent=2)

        elif format == "csv":
            output = io.StringIO()
            writer = csv.writer(output)

            # Header
            writer.writerow(["tenant_id", "event_type", "timestamp", "metadata"])

            # Data rows
            for event in events:
                writer.writerow([
                    event.tenant_id,
                    event.event_type,
                    event.timestamp.isoformat(),
                    json.dumps(event.metadata)
                ])

            return output.getvalue()

        raise ValueError(f"Unsupported export format: {format}")
