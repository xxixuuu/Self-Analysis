"""
Dashboard routes.
"""
from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.api.dependencies import get_db
from app.api.schemas import (
    DashboardData,
    DashboardStats,
    ProductivityScore,
    InsightResponse,
)
from app.db.models import DataSource, RawData, Metric, Insight
from app.core.redis import redis_client

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
):
    """
    Get dashboard statistics.

    Args:
        db: Database session

    Returns:
        DashboardStats: Dashboard statistics
    """
    # Check cache
    cache_key = "dashboard:stats"
    cached = await redis_client.get(cache_key)
    if cached:
        return cached

    # Count data sources
    data_sources_count = await db.scalar(
        select(func.count(DataSource.id)).where(DataSource.status == "active")
    )

    # Count total activities
    total_activities = await db.scalar(
        select(func.count(RawData.id))
    )

    # Count insights
    insights_count = await db.scalar(
        select(func.count(Insight.id))
    )

    # Calculate days tracked
    first_activity = await db.scalar(
        select(func.min(RawData.timestamp))
    )

    if first_activity:
        days_tracked = (datetime.utcnow() - first_activity).days
    else:
        days_tracked = 0

    stats = DashboardStats(
        data_sources_connected=data_sources_count or 0,
        total_activities=total_activities or 0,
        insights_generated=insights_count or 0,
        days_tracked=days_tracked,
    )

    # Cache for 1 hour
    await redis_client.set(cache_key, stats.model_dump(), expire=3600)

    return stats


@router.get("/data", response_model=DashboardData)
async def get_dashboard_data(
    period: str = Query("week", regex="^(day|week|month|year)$"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get complete dashboard data.

    Args:
        period: Time period (day, week, month, year)
        db: Database session

    Returns:
        DashboardData: Complete dashboard data
    """
    # Calculate date range
    now = datetime.utcnow()
    if period == "day":
        start_date = now - timedelta(days=1)
    elif period == "week":
        start_date = now - timedelta(weeks=1)
    elif period == "month":
        start_date = now - timedelta(days=30)
    else:  # year
        start_date = now - timedelta(days=365)

    # Get stats
    stats = await get_dashboard_stats(db)

    # Get recent activities
    recent_activities_result = await db.execute(
        select(RawData)
        .where(RawData.timestamp >= start_date)
        .order_by(RawData.timestamp.desc())
        .limit(20)
    )
    recent_activities_raw = recent_activities_result.scalars().all()

    recent_activities = [
        {
            "id": activity.id,
            "type": activity.data_type,
            "timestamp": activity.timestamp.isoformat(),
            "content": activity.content,
        }
        for activity in recent_activities_raw
    ]

    # Get recent insights
    recent_insights_result = await db.execute(
        select(Insight)
        .where(Insight.timestamp >= start_date)
        .order_by(Insight.timestamp.desc())
        .limit(10)
    )
    recent_insights = recent_insights_result.scalars().all()

    # Get productivity trend
    productivity_result = await db.execute(
        select(Metric)
        .where(
            and_(
                Metric.metric_type == "productivity",
                Metric.timestamp >= start_date,
            )
        )
        .order_by(Metric.timestamp.asc())
    )
    productivity_metrics = productivity_result.scalars().all()

    productivity_trend = [
        ProductivityScore(
            date=metric.timestamp.date().isoformat(),
            score=metric.value,
            category=metric.metric_name,
        )
        for metric in productivity_metrics
    ]

    return DashboardData(
        stats=stats,
        recent_activities=recent_activities,
        recent_insights=recent_insights,
        productivity_trend=productivity_trend,
    )


@router.get("/activities", response_model=List[dict])
async def get_activities(
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    activity_type: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Get paginated activities.

    Args:
        limit: Maximum number of activities to return
        offset: Number of activities to skip
        activity_type: Filter by activity type
        db: Database session

    Returns:
        List[dict]: List of activities
    """
    query = select(RawData).order_by(RawData.timestamp.desc())

    if activity_type:
        query = query.where(RawData.data_type == activity_type)

    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    activities = result.scalars().all()

    return [
        {
            "id": activity.id,
            "type": activity.data_type,
            "timestamp": activity.timestamp.isoformat(),
            "content": activity.content,
            "metadata": activity.metadata,
        }
        for activity in activities
    ]


@router.get("/productivity", response_model=List[ProductivityScore])
async def get_productivity_scores(
    days: int = Query(30, le=365),
    db: AsyncSession = Depends(get_db),
):
    """
    Get productivity scores for the last N days.

    Args:
        days: Number of days to retrieve
        db: Database session

    Returns:
        List[ProductivityScore]: Productivity scores
    """
    start_date = datetime.utcnow() - timedelta(days=days)

    result = await db.execute(
        select(Metric)
        .where(
            and_(
                Metric.metric_type == "productivity",
                Metric.timestamp >= start_date,
            )
        )
        .order_by(Metric.timestamp.asc())
    )
    metrics = result.scalars().all()

    return [
        ProductivityScore(
            date=metric.timestamp.date().isoformat(),
            score=metric.value,
            category=metric.metric_name,
        )
        for metric in metrics
    ]
