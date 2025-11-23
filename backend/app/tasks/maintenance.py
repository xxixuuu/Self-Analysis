"""
Maintenance Celery tasks.
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy import select, delete

from app.core.celery_app import celery_app
from app.core.database import async_session_maker
from app.db.models import User, RawData, AuditLog
from app.core.config import settings

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.maintenance.clean_old_data")
def clean_old_data():
    """
    Clean old data based on retention policy.

    Returns:
        dict: Cleanup results
    """
    import asyncio

    async def _clean():
        async with async_session_maker() as db:
            results = {}

            # Get all users with retention settings
            users_result = await db.execute(
                select(User).where(User.is_active == True)
            )
            users = users_result.scalars().all()

            for user in users:
                try:
                    retention_days = user.data_retention_days or settings.data_retention_days
                    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

                    # Delete old raw data
                    if not user.anonymize_old_data:
                        # Hard delete
                        result = await db.execute(
                            delete(RawData).where(
                                RawData.timestamp < cutoff_date
                            )
                        )
                        deleted_count = result.rowcount
                        results[f"user_{user.id}_deleted"] = deleted_count
                        logger.info(f"Deleted {deleted_count} old records for user {user.id}")
                    else:
                        # Anonymize instead of delete
                        # TODO: Implement anonymization logic
                        results[f"user_{user.id}_anonymized"] = 0

                except Exception as e:
                    logger.error(f"Error cleaning data for user {user.id}: {e}")
                    results[f"user_{user.id}_error"] = str(e)

            await db.commit()

            return {
                "results": results,
                "timestamp": datetime.utcnow().isoformat(),
            }

    return asyncio.run(_clean())


@celery_app.task(name="app.tasks.maintenance.clean_audit_logs")
def clean_audit_logs(days: int = 90):
    """
    Clean old audit logs.

    Args:
        days: Number of days to retain audit logs

    Returns:
        dict: Cleanup results
    """
    import asyncio

    async def _clean():
        async with async_session_maker() as db:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            result = await db.execute(
                delete(AuditLog).where(AuditLog.created_at < cutoff_date)
            )
            deleted_count = result.rowcount

            await db.commit()

            logger.info(f"Deleted {deleted_count} old audit logs")

            return {
                "deleted_count": deleted_count,
                "cutoff_date": cutoff_date.isoformat(),
                "timestamp": datetime.utcnow().isoformat(),
            }

    return asyncio.run(_clean())


@celery_app.task(name="app.tasks.maintenance.vacuum_database")
def vacuum_database():
    """
    Perform database maintenance (VACUUM).

    Returns:
        dict: Vacuum results
    """
    import asyncio

    async def _vacuum():
        async with async_session_maker() as db:
            try:
                # Note: VACUUM cannot be run inside a transaction block
                # This is a simplified version
                await db.execute("ANALYZE")
                await db.commit()

                logger.info("Database analysis complete")

                return {
                    "success": True,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            except Exception as e:
                logger.error(f"Error during database maintenance: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                }

    return asyncio.run(_vacuum())
