"""
Google Calendar data collector.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import DataSource, RawData, DataSourceType, DataSourceStatus
from app.core.security import encryption_manager

logger = logging.getLogger(__name__)


class CalendarCollector:
    """Collector for Google Calendar data."""

    def __init__(self, data_source: DataSource):
        """
        Initialize Calendar collector.

        Args:
            data_source: DataSource instance with Calendar credentials
        """
        self.data_source = data_source

        # Decrypt OAuth tokens
        access_token = encryption_manager.decrypt(data_source.access_token)
        refresh_token = encryption_manager.decrypt(data_source.refresh_token) if data_source.refresh_token else None

        # Create credentials
        creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=None,
            client_secret=None,
        )

        # Initialize Calendar API client
        self.service = build("calendar", "v3", credentials=creds)

    async def collect_all(
        self,
        db: AsyncSession,
        since: Optional[datetime] = None,
    ) -> Dict[str, int]:
        """
        Collect all Calendar data.

        Args:
            db: Database session
            since: Collect data since this date

        Returns:
            Dict with collection statistics
        """
        if not since and self.data_source.last_sync_at:
            since = self.data_source.last_sync_at
        elif not since:
            # Default to last 30 days
            since = datetime.utcnow() - timedelta(days=30)

        stats = {
            "events": 0,
            "calendars": 0,
        }

        try:
            # Collect calendars
            calendars_count = await self._collect_calendars(db)
            stats["calendars"] = calendars_count

            # Collect events
            events_count = await self._collect_events(db, since)
            stats["events"] = events_count

            # Update data source status
            self.data_source.status = DataSourceStatus.ACTIVE
            self.data_source.last_sync_at = datetime.utcnow()
            self.data_source.sync_error = None

            await db.commit()

            logger.info(f"Calendar collection complete: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Error collecting Calendar data: {e}")
            self.data_source.status = DataSourceStatus.ERROR
            self.data_source.sync_error = str(e)
            await db.commit()
            raise

    async def _collect_calendars(
        self,
        db: AsyncSession,
    ) -> int:
        """Collect user's calendars."""
        count = 0

        try:
            # Get calendar list
            calendar_list = self.service.calendarList().list().execute()
            calendars = calendar_list.get("items", [])

            for calendar in calendars:
                # Check if already collected
                result = await db.execute(
                    select(RawData).where(
                        RawData.external_id == f"cal_{calendar['id']}",
                        RawData.data_source_id == self.data_source.id,
                    )
                )
                if result.scalar_one_or_none():
                    continue

                # Create raw data entry
                raw_data = RawData(
                    data_source_id=self.data_source.id,
                    external_id=f"cal_{calendar['id']}",
                    data_type="calendar_calendar",
                    content={
                        "id": calendar["id"],
                        "summary": calendar.get("summary", ""),
                        "description": calendar.get("description", ""),
                        "time_zone": calendar.get("timeZone", ""),
                        "color_id": calendar.get("colorId", ""),
                    },
                    timestamp=datetime.utcnow(),
                    metadata={
                        "access_role": calendar.get("accessRole", ""),
                        "primary": calendar.get("primary", False),
                    }
                )

                db.add(raw_data)
                count += 1

            await db.commit()
            return count

        except Exception as e:
            logger.error(f"Error collecting calendars: {e}")
            return count

    async def _collect_events(
        self,
        db: AsyncSession,
        since: datetime,
    ) -> int:
        """Collect calendar events."""
        count = 0

        try:
            # Get calendar list
            calendar_list = self.service.calendarList().list().execute()
            calendars = calendar_list.get("items", [])

            # Collect events from each calendar
            for calendar in calendars:
                calendar_id = calendar["id"]

                # Get events
                events_result = self.service.events().list(
                    calendarId=calendar_id,
                    timeMin=since.isoformat() + "Z",
                    maxResults=250,
                    singleEvents=True,
                    orderBy="startTime",
                ).execute()

                events = events_result.get("items", [])

                for event in events:
                    # Check if already collected
                    result = await db.execute(
                        select(RawData).where(
                            RawData.external_id == event["id"],
                            RawData.data_source_id == self.data_source.id,
                        )
                    )
                    if result.scalar_one_or_none():
                        continue

                    # Parse start time
                    start = event.get("start", {})
                    if "dateTime" in start:
                        start_time = datetime.fromisoformat(start["dateTime"].replace("Z", "+00:00"))
                    elif "date" in start:
                        start_time = datetime.fromisoformat(start["date"])
                    else:
                        start_time = datetime.utcnow()

                    # Parse end time
                    end = event.get("end", {})
                    if "dateTime" in end:
                        end_time = datetime.fromisoformat(end["dateTime"].replace("Z", "+00:00"))
                    elif "date" in end:
                        end_time = datetime.fromisoformat(end["date"])
                    else:
                        end_time = start_time

                    # Calculate duration
                    duration_minutes = int((end_time - start_time).total_seconds() / 60)

                    # Create raw data entry
                    raw_data = RawData(
                        data_source_id=self.data_source.id,
                        external_id=event["id"],
                        data_type="calendar_event",
                        content={
                            "id": event["id"],
                            "summary": event.get("summary", ""),
                            "description": event.get("description", ""),
                            "location": event.get("location", ""),
                            "start": start.get("dateTime") or start.get("date"),
                            "end": end.get("dateTime") or end.get("date"),
                            "duration_minutes": duration_minutes,
                            "attendees": [
                                a.get("email") for a in event.get("attendees", [])
                            ] if event.get("attendees") else [],
                            "organizer": event.get("organizer", {}).get("email", ""),
                            "status": event.get("status", ""),
                        },
                        timestamp=start_time.replace(tzinfo=None),
                        metadata={
                            "calendar_id": calendar_id,
                            "calendar_name": calendar.get("summary", ""),
                            "is_all_day": "date" in start,
                            "attendees_count": len(event.get("attendees", [])),
                        }
                    )

                    db.add(raw_data)
                    count += 1

            await db.commit()
            return count

        except Exception as e:
            logger.error(f"Error collecting events: {e}")
            return count


async def collect_calendar_data(
    data_source_id: int,
    db: AsyncSession,
) -> Dict[str, int]:
    """
    Collect Calendar data for a data source.

    Args:
        data_source_id: Data source ID
        db: Database session

    Returns:
        Collection statistics
    """
    # Get data source
    result = await db.execute(
        select(DataSource).where(DataSource.id == data_source_id)
    )
    data_source = result.scalar_one_or_none()

    if not data_source or data_source.source_type != DataSourceType.CALENDAR:
        raise ValueError("Invalid data source")

    # Create collector and run collection
    collector = CalendarCollector(data_source)
    return await collector.collect_all(db)
