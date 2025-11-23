"""
Insights routes.
"""
from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.api.dependencies import get_db
from app.api.schemas import InsightResponse, NaturalLanguageQuery, QueryResponse
from app.db.models import Insight, RawData, Metric, User
from app.ollama.analyzer import ai_analyzer
from app.core.redis import redis_client

router = APIRouter(prefix="/insights", tags=["Insights"])


@router.get("", response_model=List[InsightResponse])
async def get_insights(
    limit: int = Query(20, le=100),
    insight_type: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Get insights.

    Args:
        limit: Maximum number of insights to return
        insight_type: Filter by insight type
        db: Database session

    Returns:
        List[InsightResponse]: List of insights
    """
    query = select(Insight).order_by(Insight.timestamp.desc()).limit(limit)

    if insight_type:
        query = query.where(Insight.insight_type == insight_type)

    result = await db.execute(query)
    insights = result.scalars().all()

    return insights


@router.post("/generate-daily-summary", response_model=InsightResponse)
async def generate_daily_summary(
    date: str = Query(None, description="Date in YYYY-MM-DD format"),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate daily summary using AI.

    Args:
        date: Date to generate summary for (default: today)
        db: Database session

    Returns:
        InsightResponse: Generated insight
    """
    # Parse date
    if date:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD",
            )
    else:
        target_date = datetime.utcnow()

    # Get activities for the day
    start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)

    result = await db.execute(
        select(RawData)
        .where(
            and_(
                RawData.timestamp >= start_of_day,
                RawData.timestamp < end_of_day,
            )
        )
        .order_by(RawData.timestamp.asc())
    )
    activities = result.scalars().all()

    # Format activities for AI
    activities_data = [
        {
            "type": activity.data_type,
            "content": str(activity.content),
            "timestamp": activity.timestamp.isoformat(),
        }
        for activity in activities
    ]

    # Generate summary using AI
    summary = await ai_analyzer.generate_daily_summary(
        activities=activities_data,
        date=target_date,
    )

    if not summary:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate summary. Is Ollama running?",
        )

    # Save insight
    # Get first user (for demo purposes)
    user_result = await db.execute(select(User).limit(1))
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No users found",
        )

    insight = Insight(
        user_id=user.id,
        insight_type="daily_summary",
        title=f"Daily Summary - {target_date.strftime('%Y-%m-%d')}",
        content=summary,
        timestamp=datetime.utcnow(),
        model_used="llama3.2",
        confidence_score=0.85,
    )

    db.add(insight)
    await db.commit()
    await db.refresh(insight)

    return insight


@router.post("/query", response_model=QueryResponse)
async def natural_language_query(
    query_data: NaturalLanguageQuery,
    db: AsyncSession = Depends(get_db),
):
    """
    Answer natural language query about user data.

    Args:
        query_data: Natural language query
        db: Database session

    Returns:
        QueryResponse: AI-generated answer
    """
    # Get recent data for context (last 30 days)
    start_date = datetime.utcnow() - timedelta(days=30)

    # Get activities
    activities_result = await db.execute(
        select(RawData)
        .where(RawData.timestamp >= start_date)
        .order_by(RawData.timestamp.desc())
        .limit(100)
    )
    activities = activities_result.scalars().all()

    # Get metrics
    metrics_result = await db.execute(
        select(Metric)
        .where(Metric.timestamp >= start_date)
        .order_by(Metric.timestamp.desc())
        .limit(100)
    )
    metrics = metrics_result.scalars().all()

    # Build context
    context = {
        "activities": [
            {
                "type": a.data_type,
                "timestamp": a.timestamp.isoformat(),
                "content": a.content,
            }
            for a in activities
        ],
        "metrics": [
            {
                "type": m.metric_type,
                "name": m.metric_name,
                "value": m.value,
                "timestamp": m.timestamp.isoformat(),
            }
            for m in metrics
        ],
    }

    # Get answer from AI
    answer = await ai_analyzer.answer_natural_language_query(
        query=query_data.query,
        context=context,
    )

    if not answer:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate answer. Is Ollama running?",
        )

    return QueryResponse(
        query=query_data.query,
        answer=answer,
        model_used="llama3.2",
        confidence=0.8,
    )


@router.post("/analyze-productivity")
async def analyze_productivity(
    days: int = Query(7, le=90),
    db: AsyncSession = Depends(get_db),
):
    """
    Analyze productivity and generate advice.

    Args:
        days: Number of days to analyze
        db: Database session

    Returns:
        dict: Productivity analysis and advice
    """
    start_date = datetime.utcnow() - timedelta(days=days)

    # Get productivity metrics
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

    if not metrics:
        return {
            "advice": "No productivity data available yet. Start tracking your activities!",
            "metrics": {},
        }

    # Calculate statistics
    values = [m.value for m in metrics]
    avg_score = sum(values) / len(values)
    max_score = max(values)
    min_score = min(values)

    metrics_summary = {
        "average_score": round(avg_score, 2),
        "max_score": round(max_score, 2),
        "min_score": round(min_score, 2),
        "days_tracked": len(metrics),
        "trend": "improving" if values[-1] > values[0] else "declining",
    }

    # Generate AI advice
    advice = await ai_analyzer.generate_productivity_advice(
        metrics=metrics_summary,
    )

    return {
        "advice": advice or "Keep up the good work!",
        "metrics": metrics_summary,
    }
