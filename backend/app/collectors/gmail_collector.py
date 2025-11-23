"""
Gmail data collector.
"""
import logging
import base64
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import DataSource, RawData, DataSourceType, DataSourceStatus
from app.core.security import encryption_manager

logger = logging.getLogger(__name__)


class GmailCollector:
    """Collector for Gmail data."""

    def __init__(self, data_source: DataSource):
        """
        Initialize Gmail collector.

        Args:
            data_source: DataSource instance with Gmail credentials
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
            client_id=None,  # Will be set from config
            client_secret=None,  # Will be set from config
        )

        # Initialize Gmail API client
        self.service = build("gmail", "v1", credentials=creds)

    async def collect_all(
        self,
        db: AsyncSession,
        since: Optional[datetime] = None,
    ) -> Dict[str, int]:
        """
        Collect all Gmail data.

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
            "sent_emails": 0,
            "received_emails": 0,
            "labels": 0,
        }

        try:
            # Collect sent emails
            sent_count = await self._collect_sent_emails(db, since)
            stats["sent_emails"] = sent_count

            # Collect received emails
            received_count = await self._collect_received_emails(db, since)
            stats["received_emails"] = received_count

            # Collect labels (for categorization)
            labels_count = await self._collect_labels(db)
            stats["labels"] = labels_count

            # Update data source status
            self.data_source.status = DataSourceStatus.ACTIVE
            self.data_source.last_sync_at = datetime.utcnow()
            self.data_source.sync_error = None

            await db.commit()

            logger.info(f"Gmail collection complete: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Error collecting Gmail data: {e}")
            self.data_source.status = DataSourceStatus.ERROR
            self.data_source.sync_error = str(e)
            await db.commit()
            raise

    async def _collect_sent_emails(
        self,
        db: AsyncSession,
        since: datetime,
    ) -> int:
        """Collect sent emails."""
        count = 0

        try:
            # Search for sent emails
            query = f"in:sent after:{since.strftime('%Y/%m/%d')}"
            results = self.service.users().messages().list(
                userId="me",
                q=query,
                maxResults=500,
            ).execute()

            messages = results.get("messages", [])

            for message in messages:
                # Get full message details
                msg = self.service.users().messages().get(
                    userId="me",
                    id=message["id"],
                    format="full",
                ).execute()

                # Check if already collected
                result = await db.execute(
                    select(RawData).where(
                        RawData.external_id == msg["id"],
                        RawData.data_source_id == self.data_source.id,
                    )
                )
                if result.scalar_one_or_none():
                    continue

                # Extract metadata
                headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
                subject = headers.get("Subject", "")
                to_addr = headers.get("To", "")
                date_str = headers.get("Date", "")

                # Parse date
                try:
                    msg_date = datetime.strptime(date_str.split(" (")[0], "%a, %d %b %Y %H:%M:%S %z")
                except:
                    msg_date = datetime.utcnow()

                # Get snippet (preview)
                snippet = msg.get("snippet", "")

                # Create raw data entry
                raw_data = RawData(
                    data_source_id=self.data_source.id,
                    external_id=msg["id"],
                    data_type="gmail_sent",
                    content={
                        "id": msg["id"],
                        "thread_id": msg.get("threadId"),
                        "subject": subject,
                        "to": to_addr,
                        "snippet": snippet,
                        "label_ids": msg.get("labelIds", []),
                    },
                    timestamp=msg_date.replace(tzinfo=None),
                    metadata={
                        "size": msg.get("sizeEstimate", 0),
                        "labels": msg.get("labelIds", []),
                    }
                )

                db.add(raw_data)
                count += 1

            await db.commit()
            return count

        except Exception as e:
            logger.error(f"Error collecting sent emails: {e}")
            return count

    async def _collect_received_emails(
        self,
        db: AsyncSession,
        since: datetime,
    ) -> int:
        """Collect received emails."""
        count = 0

        try:
            # Search for received emails (inbox)
            query = f"in:inbox after:{since.strftime('%Y/%m/%d')}"
            results = self.service.users().messages().list(
                userId="me",
                q=query,
                maxResults=500,
            ).execute()

            messages = results.get("messages", [])

            for message in messages:
                # Get full message details
                msg = self.service.users().messages().get(
                    userId="me",
                    id=message["id"],
                    format="full",
                ).execute()

                # Check if already collected
                result = await db.execute(
                    select(RawData).where(
                        RawData.external_id == f"inbox_{msg['id']}",
                        RawData.data_source_id == self.data_source.id,
                    )
                )
                if result.scalar_one_or_none():
                    continue

                # Extract metadata
                headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
                subject = headers.get("Subject", "")
                from_addr = headers.get("From", "")
                date_str = headers.get("Date", "")

                # Parse date
                try:
                    msg_date = datetime.strptime(date_str.split(" (")[0], "%a, %d %b %Y %H:%M:%S %z")
                except:
                    msg_date = datetime.utcnow()

                # Get snippet
                snippet = msg.get("snippet", "")

                # Create raw data entry
                raw_data = RawData(
                    data_source_id=self.data_source.id,
                    external_id=f"inbox_{msg['id']}",
                    data_type="gmail_received",
                    content={
                        "id": msg["id"],
                        "thread_id": msg.get("threadId"),
                        "subject": subject,
                        "from": from_addr,
                        "snippet": snippet,
                        "label_ids": msg.get("labelIds", []),
                    },
                    timestamp=msg_date.replace(tzinfo=None),
                    metadata={
                        "size": msg.get("sizeEstimate", 0),
                        "labels": msg.get("labelIds", []),
                        "unread": "UNREAD" in msg.get("labelIds", []),
                    }
                )

                db.add(raw_data)
                count += 1

            await db.commit()
            return count

        except Exception as e:
            logger.error(f"Error collecting received emails: {e}")
            return count

    async def _collect_labels(
        self,
        db: AsyncSession,
    ) -> int:
        """Collect Gmail labels."""
        count = 0

        try:
            # Get all labels
            results = self.service.users().labels().list(userId="me").execute()
            labels = results.get("labels", [])

            for label in labels:
                # Check if already collected
                result = await db.execute(
                    select(RawData).where(
                        RawData.external_id == f"label_{label['id']}",
                        RawData.data_source_id == self.data_source.id,
                    )
                )
                if result.scalar_one_or_none():
                    continue

                # Create raw data entry
                raw_data = RawData(
                    data_source_id=self.data_source.id,
                    external_id=f"label_{label['id']}",
                    data_type="gmail_label",
                    content={
                        "id": label["id"],
                        "name": label["name"],
                        "type": label.get("type", "user"),
                    },
                    timestamp=datetime.utcnow(),
                    metadata={}
                )

                db.add(raw_data)
                count += 1

            await db.commit()
            return count

        except Exception as e:
            logger.error(f"Error collecting labels: {e}")
            return count


async def collect_gmail_data(
    data_source_id: int,
    db: AsyncSession,
) -> Dict[str, int]:
    """
    Collect Gmail data for a data source.

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

    if not data_source or data_source.source_type != DataSourceType.GMAIL:
        raise ValueError("Invalid data source")

    # Create collector and run collection
    collector = GmailCollector(data_source)
    return await collector.collect_all(db)
