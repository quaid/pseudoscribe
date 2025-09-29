"""
Performance API
REST API endpoints for performance monitoring, SLA tracking, and optimization
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from pseudoscribe.api.dependencies import get_current_tenant
from pseudoscribe.infrastructure.performance_monitor import get_performance_monitor
from pseudoscribe.infrastructure.metrics_collector import get_metrics_collector
from pseudoscribe.infrastructure.sla_monitor import get_sla_monitor
from pseudoscribe.infrastructure.resource_optimizer import get_resource_optimizer

router = APIRouter(prefix="/api/v1/performance", tags=["performance"])


# Request/Response Models
class OptimizationRequest(BaseModel):
    """Request model for performance optimization"""
    optimization_type: str = Field(..., description="Type of optimization: memory, cpu, or all")
    target_improvement: Optional[float] = Field(None, description="Target improvement percentage")


class OptimizationResponse(BaseModel):
    """Response model for optimization results"""
    optimization_applied: bool
    improvement_achieved: Dict[str, float]
    recommendations: List[str]
    timestamp: str


class MetricsResponse(BaseModel):
    """Response model for performance metrics"""
    cpu_usage: float
    memory_usage: Dict[str, Any]
    response_times: Dict[str, float]
    timestamp: str
    uptime: float
    monitoring_active: bool


class SLAStatusResponse(BaseModel):
    """Response model for SLA status"""
    ai_operations: Dict[str, Any]
    live_suggestions: Dict[str, Any]
    api_response: Dict[str, Any]
    overall_compliance: float
    timestamp: str


class RecommendationsResponse(BaseModel):
    """Response model for optimization recommendations"""
    recommendations: List[Dict[str, Any]]
    system_health: str
    timestamp: str


@router.get("/metrics", response_model=MetricsResponse)
async def get_performance_metrics(tenant_id: str = Depends(get_current_tenant)):
    """
    Get current performance metrics
    
    Returns real-time system performance data including:
    - CPU usage
    - Memory usage
    - API response times
    - System uptime
    """
    try:
        monitor = get_performance_monitor()
        
        # Start monitoring if not already active
        if not monitor.is_monitoring():
            monitor.start_monitoring()
        
        metrics = monitor.get_metrics()
        
        return MetricsResponse(
            cpu_usage=metrics.get('cpu_usage', 0.0),
            memory_usage=metrics.get('memory_usage', {}),
            response_times=metrics.get('response_times', {}),
            timestamp=metrics.get('timestamp', datetime.now().isoformat()),
            uptime=metrics.get('uptime', 0.0),
            monitoring_active=metrics.get('monitoring_active', False)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving performance metrics: {str(e)}")


@router.get("/sla-status", response_model=SLAStatusResponse)
async def get_sla_status(tenant_id: str = Depends(get_current_tenant)):
    """
    Get SLA compliance status
    
    Returns compliance status for all monitored SLAs:
    - AI operations (< 2s)
    - Live suggestions (< 500ms)
    - API responses (< 200ms)
    """
    try:
        sla_monitor = get_sla_monitor()
        status = sla_monitor.get_sla_status()
        
        return SLAStatusResponse(
            ai_operations=status.get('ai_operations', {}),
            live_suggestions=status.get('live_suggestions', {}),
            api_response=status.get('api_response', {}),
            overall_compliance=status.get('overall_compliance', 100.0),
            timestamp=status.get('timestamp', datetime.now().isoformat())
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving SLA status: {str(e)}")


@router.get("/recommendations", response_model=RecommendationsResponse)
async def get_optimization_recommendations(tenant_id: str = Depends(get_current_tenant)):
    """
    Get performance optimization recommendations
    
    Returns actionable recommendations based on current system performance
    """
    try:
        monitor = get_performance_monitor()
        optimizer = get_resource_optimizer()
        
        # Get current metrics
        metrics = monitor.get_metrics()
        
        # Generate recommendations
        recommendations = optimizer.get_optimization_recommendations(metrics)
        
        # Get system health status
        health_status = monitor.get_system_health()
        
        return RecommendationsResponse(
            recommendations=[
                {
                    'category': rec.category,
                    'priority': rec.priority,
                    'description': rec.description,
                    'action': rec.action,
                    'expected_improvement': rec.expected_improvement,
                    'implementation_effort': rec.implementation_effort
                }
                for rec in recommendations
            ],
            system_health=health_status.get('status', 'unknown'),
            timestamp=datetime.now().isoformat()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")


@router.post("/optimize", response_model=OptimizationResponse)
async def optimize_performance(
    request: OptimizationRequest,
    background_tasks: BackgroundTasks,
    tenant_id: str = Depends(get_current_tenant)
):
    """
    Apply performance optimizations
    
    Applies the requested optimization type and returns results
    """
    try:
        optimizer = get_resource_optimizer()
        
        # Apply optimization
        result = optimizer.apply_optimization(
            category=request.optimization_type,
            target_improvement=request.target_improvement
        )
        
        # Generate new recommendations after optimization
        monitor = get_performance_monitor()
        metrics = monitor.get_metrics()
        recommendations = optimizer.get_optimization_recommendations(metrics)
        
        return OptimizationResponse(
            optimization_applied=result.get('optimization_applied', False),
            improvement_achieved=result.get('improvement_achieved', {}),
            recommendations=[rec.description for rec in recommendations],
            timestamp=datetime.now().isoformat()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error applying optimization: {str(e)}")


@router.get("/health")
async def get_system_health(tenant_id: str = Depends(get_current_tenant)):
    """
    Get overall system health status
    
    Returns comprehensive health assessment including:
    - Resource status
    - SLA compliance
    - Performance indicators
    """
    try:
        monitor = get_performance_monitor()
        optimizer = get_resource_optimizer()
        sla_monitor = get_sla_monitor()
        
        # Get health from all components
        system_health = monitor.get_system_health()
        resource_status = optimizer.get_resource_status()
        sla_status = sla_monitor.get_sla_status()
        
        return {
            'overall_status': system_health.get('status', 'unknown'),
            'components': {
                'performance_monitor': {
                    'status': 'healthy' if system_health.get('overall_healthy') else 'degraded',
                    'cpu_healthy': system_health.get('cpu_healthy'),
                    'memory_healthy': system_health.get('memory_healthy'),
                    'response_healthy': system_health.get('response_healthy')
                },
                'resource_optimizer': {
                    'status': 'healthy' if resource_status.get('overall_healthy') else 'degraded',
                    'memory_status': resource_status.get('memory', {}).get('status'),
                    'cpu_status': resource_status.get('cpu', {}).get('status')
                },
                'sla_monitor': {
                    'status': 'healthy' if sla_status.get('overall_compliance', 0) > 95 else 'degraded',
                    'compliance_rate': sla_status.get('overall_compliance', 0),
                    'total_violations': sla_status.get('total_violations', 0)
                }
            },
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving system health: {str(e)}")


@router.get("/history")
async def get_performance_history(
    hours: int = 24,
    tenant_id: str = Depends(get_current_tenant)
):
    """
    Get performance history
    
    Returns historical performance data for the specified time period
    """
    try:
        metrics_collector = get_metrics_collector()
        optimizer = get_resource_optimizer()
        sla_monitor = get_sla_monitor()
        
        since = datetime.now() - timedelta(hours=hours)
        
        # Get historical data
        metrics_summary = metrics_collector.get_metrics_summary(since)
        optimization_history = optimizer.get_optimization_history(limit=50)
        sla_report = sla_monitor.get_sla_report(since)
        
        return {
            'period': {
                'start': since.isoformat(),
                'end': datetime.now().isoformat(),
                'hours': hours
            },
            'metrics_summary': metrics_summary,
            'optimization_history': optimization_history,
            'sla_report': sla_report,
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving performance history: {str(e)}")


@router.post("/reset-metrics")
async def reset_performance_metrics(tenant_id: str = Depends(get_current_tenant)):
    """
    Reset performance metrics
    
    Clears all collected performance data and starts fresh monitoring
    """
    try:
        monitor = get_performance_monitor()
        metrics_collector = get_metrics_collector()
        sla_monitor = get_sla_monitor()
        
        # Reset all metrics
        monitor.reset_metrics()
        metrics_collector.clear_metrics()
        sla_monitor.reset_metrics()
        
        return {
            'message': 'Performance metrics reset successfully',
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting metrics: {str(e)}")


@router.get("/export")
async def export_performance_data(
    format: str = "json",
    hours: int = 24,
    tenant_id: str = Depends(get_current_tenant)
):
    """
    Export performance data
    
    Exports performance data in the specified format (json or csv)
    """
    try:
        if format not in ["json", "csv"]:
            raise HTTPException(status_code=400, detail="Format must be 'json' or 'csv'")
        
        metrics_collector = get_metrics_collector()
        since = datetime.now() - timedelta(hours=hours)
        
        # Export metrics data
        exported_data = metrics_collector.export_metrics(format=format, since=since)
        
        return {
            'format': format,
            'period_hours': hours,
            'data': exported_data,
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting performance data: {str(e)}")


# Background task to start monitoring when the module is imported
def initialize_performance_monitoring():
    """Initialize performance monitoring on startup"""
    try:
        monitor = get_performance_monitor()
        if not monitor.is_monitoring():
            monitor.start_monitoring()
        
        # Start metrics collection
        collector = get_metrics_collector()
        if not collector._collecting:
            collector.start_collection()
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error initializing performance monitoring: {e}")


# Initialize monitoring when module is imported
initialize_performance_monitoring()
