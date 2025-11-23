"""
Data collection Celery tasks.
"""
import logging
from datetime import datetime
from sqlalchemy import select

from app.core.celery_app import celery_app
from app.core.database import async_session_maker
from app.db.models import DataSource, DataSourceType, DataSourceStatus
from app.collectors.github_collector import collect_github_data
from app.collectors.twitter_collector import collect_twitter_data
from app.collectors.gmail_collector import collect_gmail_data
from app.collectors.calendar_collector import collect_calendar_data

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.collection.collect_github_data_for_source")
def collect_github_data_for_source(data_source_id: int):
    """
    Collect GitHub data for a specific data source.

    Args:
        data_source_id: Data source ID

    Returns:
        dict: Collection results
    """
    import asyncio

    async def _collect():
        async with async_session_maker() as db:
            try:
                stats = await collect_github_data(data_source_id, db)
                logger.info(f"GitHub collection complete for source {data_source_id}: {stats}")
                return {"success": True, "stats": stats}
            except Exception as e:
                logger.error(f"Error collecting GitHub data: {e}")
                return {"success": False, "error": str(e)}

    return asyncio.run(_collect())


@celery_app.task(name="app.tasks.collection.collect_all_github_data")
def collect_all_github_data():
    """
    Collect GitHub data for all active GitHub data sources.

    Returns:
        dict: Collection results for all sources
    """
    import asyncio

    async def _collect_all():
        async with async_session_maker() as db:
            # Get all active GitHub data sources
            result = await db.execute(
                select(DataSource).where(
                    DataSource.source_type == DataSourceType.GITHUB,
                    DataSource.status == DataSourceStatus.ACTIVE,
                )
            )
            data_sources = result.scalars().all()

            results = []
            for ds in data_sources:
                try:
                    stats = await collect_github_data(ds.id, db)
                    results.append({
                        "data_source_id": ds.id,
                        "success": True,
                        "stats": stats,
                    })
                    logger.info(f"GitHub collection complete for source {ds.id}: {stats}")
                except Exception as e:
                    results.append({
                        "data_source_id": ds.id,
                        "success": False,
                        "error": str(e),
                    })
                    logger.error(f"Error collecting GitHub data for source {ds.id}: {e}")

            return {
                "total_sources": len(data_sources),
                "results": results,
                "timestamp": datetime.utcnow().isoformat(),
            }

    return asyncio.run(_collect_all())


@celery_app.task(name="app.tasks.collection.trigger_collection")
def trigger_collection(data_source_id: int, force: bool = False):
    """
    Trigger data collection for a specific data source.

    Args:
        data_source_id: Data source ID
        force: Force collection even if recently collected

    Returns:
        dict: Collection results
    """
    import asyncio

    async def _trigger():
        async with async_session_maker() as db:
            # Get data source
            result = await db.execute(
                select(DataSource).where(DataSource.id == data_source_id)
            )
            data_source = result.scalar_one_or_none()

            if not data_source:
                return {"success": False, "error": "Data source not found"}

            # Dispatch to appropriate collector
            try:
                if data_source.source_type == DataSourceType.GITHUB:
                    stats = await collect_github_data(data_source_id, db)
                elif data_source.source_type == DataSourceType.TWITTER:
                    stats = await collect_twitter_data(data_source_id, db)
                elif data_source.source_type == DataSourceType.GMAIL:
                    stats = await collect_gmail_data(data_source_id, db)
                elif data_source.source_type == DataSourceType.CALENDAR:
                    stats = await collect_calendar_data(data_source_id, db)
                else:
                    return {
                        "success": False,
                        "error": f"Collector not implemented for {data_source.source_type}",
                    }

                return {"success": True, "stats": stats}
            except Exception as e:
                return {"success": False, "error": str(e)}

    return asyncio.run(_trigger())


@celery_app.task(name="app.tasks.collection.collect_all_data")
def collect_all_data():
    """
    Collect data from all active data sources.

    Returns:
        dict: Collection results for all sources
    """
    import asyncio

    async def _collect_all():
        async with async_session_maker() as db:
            # Get all active data sources
            result = await db.execute(
                select(DataSource).where(DataSource.status == DataSourceStatus.ACTIVE)
            )
            data_sources = result.scalars().all()

            results = []
            for ds in data_sources:
                try:
                    if ds.source_type == DataSourceType.GITHUB:
                        stats = await collect_github_data(ds.id, db)
                    elif ds.source_type == DataSourceType.TWITTER:
                        stats = await collect_twitter_data(ds.id, db)
                    elif ds.source_type == DataSourceType.GMAIL:
                        stats = await collect_gmail_data(ds.id, db)
                    elif ds.source_type == DataSourceType.CALENDAR:
                        stats = await collect_calendar_data(ds.id, db)
                    else:
                        logger.warning(f"No collector for {ds.source_type}")
                        continue

                    results.append({
                        "data_source_id": ds.id,
                        "source_type": ds.source_type.value,
                        "success": True,
                        "stats": stats,
                    })
                    logger.info(f"{ds.source_type.value} collection complete for source {ds.id}: {stats}")

                except Exception as e:
                    results.append({
                        "data_source_id": ds.id,
                        "source_type": ds.source_type.value,
                        "success": False,
                        "error": str(e),
                    })
                    logger.error(f"Error collecting {ds.source_type.value} data for source {ds.id}: {e}")

            return {
                "total_sources": len(data_sources),
                "results": results,
                "timestamp": datetime.utcnow().isoformat(),
            }

    return asyncio.run(_collect_all())
