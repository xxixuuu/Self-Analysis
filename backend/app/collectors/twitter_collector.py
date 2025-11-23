"""
Twitter/X data collector.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import tweepy
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import DataSource, RawData, DataSourceType, DataSourceStatus
from app.core.security import encryption_manager

logger = logging.getLogger(__name__)


class TwitterCollector:
    """Collector for Twitter/X data."""

    def __init__(self, data_source: DataSource):
        """
        Initialize Twitter collector.

        Args:
            data_source: DataSource instance with Twitter credentials
        """
        self.data_source = data_source

        # Decrypt access token
        access_token = encryption_manager.decrypt(data_source.access_token)

        # Initialize Twitter API client (v2)
        self.client = tweepy.Client(bearer_token=access_token)

    async def collect_all(
        self,
        db: AsyncSession,
        since: Optional[datetime] = None,
    ) -> Dict[str, int]:
        """
        Collect all Twitter data.

        Args:
            db: Database session
            since: Collect data since this date

        Returns:
            Dict with collection statistics
        """
        if not since and self.data_source.last_sync_at:
            since = self.data_source.last_sync_at
        elif not since:
            # Default to last 7 days (Twitter API limitation)
            since = datetime.utcnow() - timedelta(days=7)

        stats = {
            "tweets": 0,
            "likes": 0,
            "retweets": 0,
        }

        try:
            # Get authenticated user
            me = self.client.get_me()
            if not me.data:
                raise Exception("Failed to get authenticated user")

            user_id = me.data.id

            # Collect tweets
            tweets_count = await self._collect_tweets(db, user_id, since)
            stats["tweets"] = tweets_count

            # Collect liked tweets
            likes_count = await self._collect_liked_tweets(db, user_id, since)
            stats["likes"] = likes_count

            # Update data source status
            self.data_source.status = DataSourceStatus.ACTIVE
            self.data_source.last_sync_at = datetime.utcnow()
            self.data_source.sync_error = None

            await db.commit()

            logger.info(f"Twitter collection complete: {stats}")
            return stats

        except tweepy.TweepyException as e:
            logger.error(f"Twitter API error: {e}")
            self.data_source.status = DataSourceStatus.ERROR
            self.data_source.sync_error = str(e)
            await db.commit()
            raise

        except Exception as e:
            logger.error(f"Error collecting Twitter data: {e}")
            self.data_source.status = DataSourceStatus.ERROR
            self.data_source.sync_error = str(e)
            await db.commit()
            raise

    async def _collect_tweets(
        self,
        db: AsyncSession,
        user_id: str,
        since: datetime,
    ) -> int:
        """Collect user tweets."""
        count = 0

        try:
            # Get user's tweets
            tweets = self.client.get_users_tweets(
                id=user_id,
                start_time=since.isoformat() + "Z",
                max_results=100,
                tweet_fields=["created_at", "public_metrics", "entities", "lang"],
            )

            if not tweets.data:
                return 0

            for tweet in tweets.data:
                # Check if already collected
                result = await db.execute(
                    select(RawData).where(
                        RawData.external_id == str(tweet.id),
                        RawData.data_source_id == self.data_source.id,
                    )
                )
                if result.scalar_one_or_none():
                    continue

                # Create raw data entry
                raw_data = RawData(
                    data_source_id=self.data_source.id,
                    external_id=str(tweet.id),
                    data_type="twitter_tweet",
                    content={
                        "id": str(tweet.id),
                        "text": tweet.text,
                        "created_at": tweet.created_at.isoformat() if tweet.created_at else None,
                        "lang": tweet.lang if hasattr(tweet, "lang") else None,
                        "public_metrics": tweet.public_metrics if hasattr(tweet, "public_metrics") else {},
                        "entities": tweet.entities if hasattr(tweet, "entities") else {},
                    },
                    timestamp=tweet.created_at if tweet.created_at else datetime.utcnow(),
                    metadata={
                        "retweet_count": tweet.public_metrics.get("retweet_count", 0) if hasattr(tweet, "public_metrics") else 0,
                        "like_count": tweet.public_metrics.get("like_count", 0) if hasattr(tweet, "public_metrics") else 0,
                        "reply_count": tweet.public_metrics.get("reply_count", 0) if hasattr(tweet, "public_metrics") else 0,
                    }
                )

                db.add(raw_data)
                count += 1

            await db.commit()
            return count

        except Exception as e:
            logger.error(f"Error collecting tweets: {e}")
            return count

    async def _collect_liked_tweets(
        self,
        db: AsyncSession,
        user_id: str,
        since: datetime,
    ) -> int:
        """Collect liked tweets."""
        count = 0

        try:
            # Get liked tweets
            likes = self.client.get_liked_tweets(
                id=user_id,
                max_results=100,
                tweet_fields=["created_at", "author_id"],
            )

            if not likes.data:
                return 0

            for tweet in likes.data:
                # Filter by date (Twitter API doesn't support start_time for likes)
                if tweet.created_at and tweet.created_at < since:
                    continue

                # Check if already collected
                result = await db.execute(
                    select(RawData).where(
                        RawData.external_id == f"like_{tweet.id}",
                        RawData.data_source_id == self.data_source.id,
                    )
                )
                if result.scalar_one_or_none():
                    continue

                # Create raw data entry
                raw_data = RawData(
                    data_source_id=self.data_source.id,
                    external_id=f"like_{tweet.id}",
                    data_type="twitter_like",
                    content={
                        "tweet_id": str(tweet.id),
                        "text": tweet.text,
                        "author_id": tweet.author_id if hasattr(tweet, "author_id") else None,
                        "created_at": tweet.created_at.isoformat() if tweet.created_at else None,
                    },
                    timestamp=tweet.created_at if tweet.created_at else datetime.utcnow(),
                    metadata={}
                )

                db.add(raw_data)
                count += 1

            await db.commit()
            return count

        except Exception as e:
            logger.error(f"Error collecting liked tweets: {e}")
            return count


async def collect_twitter_data(
    data_source_id: int,
    db: AsyncSession,
) -> Dict[str, int]:
    """
    Collect Twitter data for a data source.

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

    if not data_source or data_source.source_type != DataSourceType.TWITTER:
        raise ValueError("Invalid data source")

    # Create collector and run collection
    collector = TwitterCollector(data_source)
    return await collector.collect_all(db)
