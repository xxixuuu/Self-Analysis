"""
Celery application configuration.
"""
from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

# Create Celery application
celery_app = Celery(
    "lifemetrics",
    broker=settings.celery_broker,
    backend=settings.celery_backend,
    include=[
        "app.tasks.collection",
        "app.tasks.analysis",
    ],
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Configure periodic tasks
celery_app.conf.beat_schedule = {
    # Collect GitHub data every hour
    "collect-github-data-hourly": {
        "task": "app.tasks.collection.collect_all_github_data",
        "schedule": crontab(minute=0),  # Every hour
    },
    # Generate daily summaries at midnight
    "generate-daily-summaries": {
        "task": "app.tasks.analysis.generate_daily_summaries",
        "schedule": crontab(hour=0, minute=30),  # 00:30 every day
    },
    # Analyze productivity weekly
    "analyze-productivity-weekly": {
        "task": "app.tasks.analysis.analyze_weekly_productivity",
        "schedule": crontab(day_of_week=1, hour=8, minute=0),  # Monday 8:00 AM
    },
    # Clean old data monthly
    "clean-old-data": {
        "task": "app.tasks.maintenance.clean_old_data",
        "schedule": crontab(day_of_month=1, hour=2, minute=0),  # 1st of month, 2:00 AM
    },
}

# Task routing
celery_app.conf.task_routes = {
    "app.tasks.collection.*": {"queue": "collection"},
    "app.tasks.analysis.*": {"queue": "analysis"},
    "app.tasks.maintenance.*": {"queue": "maintenance"},
}
