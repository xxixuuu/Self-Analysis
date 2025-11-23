"""
Data analysis Celery tasks.
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy import select, and_

from app.core.celery_app import celery_app
from app.core.database import async_session_maker
from app.db.models import User, RawData, Insight
from app.ollama.analyzer import ai_analyzer

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.analysis.generate_daily_summaries")
def generate_daily_summaries():
    """
    Generate daily summaries for all users.

    Returns:
        dict: Generation results
    """
    import asyncio

    async def _generate():
        async with async_session_maker() as db:
            # Get all active users
            result = await db.execute(
                select(User).where(User.is_active == True)
            )
            users = result.scalars().all()

            results = []
            yesterday = datetime.utcnow() - timedelta(days=1)
            start_of_day = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)

            for user in users:
                try:
                    # Get activities for yesterday
                    activities_result = await db.execute(
                        select(RawData)
                        .where(
                            and_(
                                RawData.timestamp >= start_of_day,
                                RawData.timestamp < end_of_day,
                            )
                        )
                        .order_by(RawData.timestamp.asc())
                    )
                    activities = activities_result.scalars().all()

                    if not activities:
                        logger.info(f"No activities for user {user.id} on {yesterday.date()}")
                        continue

                    # Format activities
                    activities_data = [
                        {
                            "type": activity.data_type,
                            "content": str(activity.content),
                            "timestamp": activity.timestamp.isoformat(),
                        }
                        for activity in activities
                    ]

                    # Generate summary
                    summary = await ai_analyzer.generate_daily_summary(
                        activities=activities_data,
                        date=yesterday,
                    )

                    if summary:
                        # Save insight
                        insight = Insight(
                            user_id=user.id,
                            insight_type="daily_summary",
                            title=f"Daily Summary - {yesterday.strftime('%Y-%m-%d')}",
                            content=summary,
                            timestamp=datetime.utcnow(),
                            model_used="llama3.2",
                            confidence_score=0.85,
                        )
                        db.add(insight)
                        await db.commit()

                        results.append({
                            "user_id": user.id,
                            "success": True,
                            "activities_count": len(activities),
                        })
                        logger.info(f"Daily summary generated for user {user.id}")
                    else:
                        results.append({
                            "user_id": user.id,
                            "success": False,
                            "error": "Failed to generate summary",
                        })

                except Exception as e:
                    results.append({
                        "user_id": user.id,
                        "success": False,
                        "error": str(e),
                    })
                    logger.error(f"Error generating daily summary for user {user.id}: {e}")

            return {
                "total_users": len(users),
                "results": results,
                "timestamp": datetime.utcnow().isoformat(),
            }

    return asyncio.run(_generate())


@celery_app.task(name="app.tasks.analysis.analyze_weekly_productivity")
def analyze_weekly_productivity():
    """
    Analyze weekly productivity for all users.

    Returns:
        dict: Analysis results
    """
    import asyncio

    async def _analyze():
        async with async_session_maker() as db:
            # Get all active users
            result = await db.execute(
                select(User).where(User.is_active == True)
            )
            users = result.scalars().all()

            results = []

            for user in users:
                try:
                    # Get activities for last 7 days
                    start_date = datetime.utcnow() - timedelta(days=7)

                    activities_result = await db.execute(
                        select(RawData)
                        .where(RawData.timestamp >= start_date)
                        .order_by(RawData.timestamp.asc())
                    )
                    activities = activities_result.scalars().all()

                    if not activities:
                        continue

                    # Calculate basic metrics
                    metrics = {
                        "total_activities": len(activities),
                        "days_active": len(set(a.timestamp.date() for a in activities)),
                        "avg_activities_per_day": len(activities) / 7,
                    }

                    # Generate productivity advice
                    advice = await ai_analyzer.generate_productivity_advice(
                        metrics=metrics,
                    )

                    if advice:
                        # Save as insight
                        insight = Insight(
                            user_id=user.id,
                            insight_type="weekly_productivity",
                            title="Weekly Productivity Analysis",
                            content=advice,
                            timestamp=datetime.utcnow(),
                            model_used="llama3.2",
                            confidence_score=0.8,
                        )
                        db.add(insight)
                        await db.commit()

                        results.append({
                            "user_id": user.id,
                            "success": True,
                            "metrics": metrics,
                        })
                        logger.info(f"Weekly productivity analysis complete for user {user.id}")

                except Exception as e:
                    results.append({
                        "user_id": user.id,
                        "success": False,
                        "error": str(e),
                    })
                    logger.error(f"Error analyzing productivity for user {user.id}: {e}")

            return {
                "total_users": len(users),
                "results": results,
                "timestamp": datetime.utcnow().isoformat(),
            }

    return asyncio.run(_analyze())
