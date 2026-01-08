"""Analytics Dashboard for Enterprise Reporting.

Issue: ENT-003 - Analytics Dashboard

This module provides analytics dashboard functionality including:
- Dashboard data aggregation
- Tenant-specific analytics
- Time-series metrics for charting
- KPI calculations
- Period comparisons
- Export functionality
"""

import json
import csv
import io
import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union
from enum import Enum
from collections import defaultdict


class WidgetType(Enum):
    """Types of dashboard widgets."""
    LINE_CHART = "line_chart"
    BAR_CHART = "bar_chart"
    PIE_CHART = "pie_chart"
    KPI_CARD = "kpi_card"
    TABLE = "table"


class KPIMetric(Enum):
    """Available KPI metrics."""
    USAGE_GROWTH = "usage_growth"
    SUCCESS_RATE = "success_rate"
    AVG_RESPONSE_TIME = "avg_response_time"
    ACTIVE_USERS = "active_users"
    TOTAL_EVENTS = "total_events"


@dataclass
class DateRange:
    """Represents a date range for filtering."""
    start: datetime
    end: datetime


@dataclass
class DashboardWidget:
    """Represents a dashboard widget configuration."""
    widget_id: str
    tenant_id: str
    widget_type: WidgetType
    metric: str
    title: str = ""
    config: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class AnalyticsEvent:
    """Represents an analytics event."""
    event_id: str
    tenant_id: str
    event_type: str
    metadata: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


class AnalyticsDashboard:
    """Analytics dashboard for enterprise reporting."""

    def __init__(self):
        """Initialize the analytics dashboard."""
        self._events: Dict[str, List[AnalyticsEvent]] = defaultdict(list)
        self._widgets: Dict[str, DashboardWidget] = {}
        self._tenant_widgets: Dict[str, List[str]] = defaultdict(list)

    def record_event(
        self,
        tenant_id: str,
        event_type: str,
        metadata: Dict[str, Any]
    ) -> AnalyticsEvent:
        """Record an analytics event.

        Args:
            tenant_id: The tenant generating the event
            event_type: Type of event (api_call, feature_usage, etc.)
            metadata: Additional event metadata

        Returns:
            The created AnalyticsEvent
        """
        event = AnalyticsEvent(
            event_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            event_type=event_type,
            metadata=metadata
        )
        self._events[tenant_id].append(event)
        return event

    def get_aggregated_metrics(
        self,
        tenant_id: str,
        date_range: Optional[DateRange] = None
    ) -> Dict[str, Any]:
        """Get aggregated metrics for a tenant.

        Args:
            tenant_id: The tenant to get metrics for
            date_range: Optional date range filter

        Returns:
            Aggregated metrics dictionary
        """
        events = self._filter_events(tenant_id, date_range)

        api_calls = sum(1 for e in events if e.event_type == "api_call")
        feature_usage = sum(1 for e in events if e.event_type == "feature_usage")

        return {
            "total_events": len(events),
            "api_calls": api_calls,
            "feature_usage": feature_usage
        }

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system-wide metrics across all tenants.

        Returns:
            System-wide metrics dictionary
        """
        all_events = []
        for events in self._events.values():
            all_events.extend(events)

        active_tenants = len(self._events)
        api_calls = sum(1 for e in all_events if e.event_type == "api_call")
        feature_usage = sum(1 for e in all_events if e.event_type == "feature_usage")

        return {
            "total_events": len(all_events),
            "active_tenants": active_tenants,
            "api_calls": api_calls,
            "feature_usage": feature_usage
        }

    def _filter_events(
        self,
        tenant_id: str,
        date_range: Optional[DateRange] = None
    ) -> List[AnalyticsEvent]:
        """Filter events by date range.

        Args:
            tenant_id: The tenant to filter events for
            date_range: Optional date range filter

        Returns:
            Filtered list of events
        """
        events = self._events.get(tenant_id, [])

        if date_range:
            events = [
                e for e in events
                if date_range.start <= e.timestamp <= date_range.end
            ]

        return events

    def get_time_series(
        self,
        tenant_id: str,
        metric: str,
        granularity: str = "hourly",
        periods: int = 24
    ) -> Dict[str, Any]:
        """Get time-series data for charting.

        Args:
            tenant_id: The tenant to get data for
            metric: The metric to chart
            granularity: Time granularity ("hourly", "daily")
            periods: Number of periods to include

        Returns:
            Time-series data dictionary
        """
        events = self._events.get(tenant_id, [])
        now = datetime.now()

        if granularity == "hourly":
            delta = timedelta(hours=1)
        else:  # daily
            delta = timedelta(days=1)

        data_points = []
        for i in range(periods):
            period_end = now - (delta * i)
            period_start = period_end - delta

            period_events = [
                e for e in events
                if period_start <= e.timestamp <= period_end
            ]

            # Calculate metric value
            if metric == "api_calls":
                value = sum(1 for e in period_events if e.event_type == "api_call")
            elif metric == "feature_usage":
                value = sum(1 for e in period_events if e.event_type == "feature_usage")
            else:
                value = len(period_events)

            data_points.append({
                "timestamp": period_start.isoformat(),
                "value": value
            })

        # Reverse to get chronological order
        data_points.reverse()

        return {
            "metric": metric,
            "granularity": granularity,
            "data_points": data_points
        }

    def calculate_kpi(
        self,
        tenant_id: str,
        kpi: KPIMetric
    ) -> Dict[str, Any]:
        """Calculate a KPI metric.

        Args:
            tenant_id: The tenant to calculate KPI for
            kpi: The KPI metric to calculate

        Returns:
            KPI value and metadata
        """
        events = self._events.get(tenant_id, [])

        if kpi == KPIMetric.USAGE_GROWTH:
            return self._calculate_usage_growth(events)
        elif kpi == KPIMetric.SUCCESS_RATE:
            return self._calculate_success_rate(events)
        elif kpi == KPIMetric.AVG_RESPONSE_TIME:
            return self._calculate_avg_response_time(events)
        elif kpi == KPIMetric.ACTIVE_USERS:
            return self._calculate_active_users(events)
        elif kpi == KPIMetric.TOTAL_EVENTS:
            return {"value": len(events), "trend": "stable"}

        return {"value": 0, "trend": "stable"}

    def _calculate_usage_growth(self, events: List[AnalyticsEvent]) -> Dict[str, Any]:
        """Calculate usage growth KPI."""
        if not events:
            return {"value": 0, "trend": "stable"}

        now = datetime.now()
        current_week = [e for e in events if e.timestamp >= now - timedelta(days=7)]
        previous_week = [
            e for e in events
            if now - timedelta(days=14) <= e.timestamp < now - timedelta(days=7)
        ]

        current_count = len(current_week)
        previous_count = len(previous_week)

        if previous_count == 0:
            growth = 100.0 if current_count > 0 else 0.0
        else:
            growth = ((current_count - previous_count) / previous_count) * 100

        trend = "up" if growth > 0 else "down" if growth < 0 else "stable"

        return {"value": growth, "trend": trend}

    def _calculate_success_rate(self, events: List[AnalyticsEvent]) -> Dict[str, Any]:
        """Calculate success rate KPI."""
        api_events = [e for e in events if e.event_type == "api_call"]
        if not api_events:
            return {"value": 100.0, "trend": "stable"}

        successes = sum(1 for e in api_events if e.metadata.get("success", True))
        rate = (successes / len(api_events)) * 100

        return {"value": rate, "trend": "stable"}

    def _calculate_avg_response_time(self, events: List[AnalyticsEvent]) -> Dict[str, Any]:
        """Calculate average response time KPI."""
        times = [
            e.metadata.get("response_time_ms")
            for e in events
            if e.metadata.get("response_time_ms") is not None
        ]

        if not times:
            return {"value": 0, "trend": "stable"}

        avg = sum(times) / len(times)
        return {"value": avg, "trend": "stable"}

    def _calculate_active_users(self, events: List[AnalyticsEvent]) -> Dict[str, Any]:
        """Calculate active users KPI."""
        users = set()
        for event in events:
            user_id = event.metadata.get("user_id")
            if user_id:
                users.add(user_id)

        return {"value": len(users), "trend": "stable"}

    def compare_periods(
        self,
        tenant_id: str,
        current_period: Optional[str] = None,
        previous_period: Optional[str] = None,
        current_range: Optional[DateRange] = None,
        previous_range: Optional[DateRange] = None
    ) -> Dict[str, Any]:
        """Compare metrics between two periods.

        Args:
            tenant_id: The tenant to compare
            current_period: Current period name (e.g., "this_week")
            previous_period: Previous period name (e.g., "last_week")
            current_range: Optional specific current date range
            previous_range: Optional specific previous date range

        Returns:
            Comparison results
        """
        now = datetime.now()

        # Use named periods or specific ranges
        if current_range is None:
            if current_period == "this_week":
                current_range = DateRange(now - timedelta(days=7), now)
            else:
                current_range = DateRange(now - timedelta(days=7), now)

        if previous_range is None:
            if previous_period == "last_week":
                previous_range = DateRange(
                    now - timedelta(days=14),
                    now - timedelta(days=7)
                )
            else:
                previous_range = DateRange(
                    now - timedelta(days=14),
                    now - timedelta(days=7)
                )

        current_events = self._filter_events(tenant_id, current_range)
        previous_events = self._filter_events(tenant_id, previous_range)

        current_count = len(current_events)
        previous_count = len(previous_events)

        if previous_count == 0:
            change_percent = 100.0 if current_count > 0 else 0.0
        else:
            change_percent = ((current_count - previous_count) / previous_count) * 100

        return {
            "current": {"event_count": current_count},
            "previous": {"event_count": previous_count},
            "change_percent": change_percent
        }

    def create_widget(
        self,
        tenant_id: str,
        widget_type: WidgetType,
        metric: str,
        title: str = ""
    ) -> DashboardWidget:
        """Create a dashboard widget.

        Args:
            tenant_id: The tenant creating the widget
            widget_type: Type of widget
            metric: Metric to display
            title: Widget title

        Returns:
            Created DashboardWidget
        """
        widget = DashboardWidget(
            widget_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            widget_type=widget_type,
            metric=metric,
            title=title or f"{metric} Widget"
        )
        self._widgets[widget.widget_id] = widget
        self._tenant_widgets[tenant_id].append(widget.widget_id)
        return widget

    def get_widget_data(self, widget_id: str) -> Optional[Dict[str, Any]]:
        """Get data for a widget.

        Args:
            widget_id: The widget to get data for

        Returns:
            Widget data dictionary
        """
        widget = self._widgets.get(widget_id)
        if not widget:
            return None

        events = self._events.get(widget.tenant_id, [])

        # Calculate value based on metric
        if widget.metric == "total_events":
            value = len(events)
        elif widget.metric == "api_calls":
            value = sum(1 for e in events if e.event_type == "api_call")
        elif widget.metric == "feature_usage":
            value = sum(1 for e in events if e.event_type == "feature_usage")
        elif widget.metric == "success_rate":
            kpi = self.calculate_kpi(widget.tenant_id, KPIMetric.SUCCESS_RATE)
            value = kpi["value"]
        else:
            value = len(events)

        return {
            "widget_id": widget_id,
            "value": value,
            "updated_at": datetime.now().isoformat()
        }

    def list_widgets(self, tenant_id: str) -> List[DashboardWidget]:
        """List all widgets for a tenant.

        Args:
            tenant_id: The tenant to list widgets for

        Returns:
            List of DashboardWidgets
        """
        widget_ids = self._tenant_widgets.get(tenant_id, [])
        return [self._widgets[wid] for wid in widget_ids if wid in self._widgets]

    def delete_widget(self, widget_id: str) -> bool:
        """Delete a widget.

        Args:
            widget_id: The widget to delete

        Returns:
            True if deleted, False if not found
        """
        widget = self._widgets.get(widget_id)
        if not widget:
            return False

        del self._widgets[widget_id]
        self._tenant_widgets[widget.tenant_id].remove(widget_id)
        return True

    def get_top_features(
        self,
        tenant_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top used features.

        Args:
            tenant_id: The tenant to analyze
            limit: Maximum features to return

        Returns:
            List of features with counts
        """
        events = self._events.get(tenant_id, [])
        feature_events = [e for e in events if e.event_type == "feature_usage"]

        counts: Dict[str, int] = defaultdict(int)
        for event in feature_events:
            feature = event.metadata.get("feature", "unknown")
            counts[feature] += 1

        sorted_features = sorted(counts.items(), key=lambda x: x[1], reverse=True)

        return [
            {"feature": name, "count": count}
            for name, count in sorted_features[:limit]
        ]

    def get_top_endpoints(
        self,
        tenant_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top used API endpoints.

        Args:
            tenant_id: The tenant to analyze
            limit: Maximum endpoints to return

        Returns:
            List of endpoints with counts
        """
        events = self._events.get(tenant_id, [])
        api_events = [e for e in events if e.event_type == "api_call"]

        counts: Dict[str, int] = defaultdict(int)
        for event in api_events:
            endpoint = event.metadata.get("endpoint", "unknown")
            counts[endpoint] += 1

        sorted_endpoints = sorted(counts.items(), key=lambda x: x[1], reverse=True)

        return [
            {"endpoint": name, "count": count}
            for name, count in sorted_endpoints[:limit]
        ]

    def export_dashboard(
        self,
        tenant_id: str,
        format: str = "json"
    ) -> str:
        """Export dashboard data.

        Args:
            tenant_id: The tenant to export
            format: Export format ("json" or "csv")

        Returns:
            Exported data as string
        """
        events = self._events.get(tenant_id, [])
        metrics = self.get_aggregated_metrics(tenant_id)

        if format == "json":
            return json.dumps({
                "metrics": metrics,
                "events": [
                    {
                        "event_id": e.event_id,
                        "event_type": e.event_type,
                        "timestamp": e.timestamp.isoformat(),
                        "metadata": e.metadata
                    }
                    for e in events
                ],
                "generated_at": datetime.now().isoformat()
            }, indent=2)

        elif format == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["event_id", "event_type", "timestamp", "metadata"])
            for event in events:
                writer.writerow([
                    event.event_id,
                    event.event_type,
                    event.timestamp.isoformat(),
                    json.dumps(event.metadata)
                ])
            return output.getvalue()

        raise ValueError(f"Unsupported format: {format}")

    def get_live_metrics(self, tenant_id: str) -> Dict[str, Any]:
        """Get live/real-time metrics.

        Args:
            tenant_id: The tenant to get metrics for

        Returns:
            Live metrics dictionary
        """
        events = self._events.get(tenant_id, [])
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)

        current_minute_events = sum(
            1 for e in events if e.timestamp >= one_minute_ago
        )

        # Calculate average events per minute over last hour
        one_hour_ago = now - timedelta(hours=1)
        last_hour_events = sum(1 for e in events if e.timestamp >= one_hour_ago)
        events_per_minute = last_hour_events / 60 if last_hour_events > 0 else 0

        return {
            "current_minute_events": current_minute_events,
            "events_per_minute": events_per_minute,
            "total_today": len([
                e for e in events
                if e.timestamp.date() == now.date()
            ])
        }

    def get_activity_feed(
        self,
        tenant_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get recent activity feed.

        Args:
            tenant_id: The tenant to get activity for
            limit: Maximum activities to return

        Returns:
            List of recent activities (most recent first)
        """
        events = self._events.get(tenant_id, [])

        # Sort by timestamp descending
        sorted_events = sorted(events, key=lambda e: e.timestamp, reverse=True)

        return [
            {
                "event_id": e.event_id,
                "event_type": e.event_type,
                "timestamp": e.timestamp.isoformat(),
                "metadata": e.metadata
            }
            for e in sorted_events[:limit]
        ]
