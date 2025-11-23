"""
Sentiment analysis engine using VADER.
"""
import logging
from typing import List, Dict, Any
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import RawData, Metric

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """Analyzer for sentiment analysis of text data."""

    def __init__(self):
        """Initialize sentiment analyzer."""
        self.vader = SentimentIntensityAnalyzer()

    def analyze_text(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment of a single text.

        Args:
            text: Text to analyze

        Returns:
            Dict with sentiment scores
        """
        scores = self.vader.polarity_scores(text)
        return {
            "positive": scores["pos"],
            "negative": scores["neg"],
            "neutral": scores["neu"],
            "compound": scores["compound"],  # Overall sentiment (-1 to 1)
        }

    async def analyze_activity(
        self,
        db: AsyncSession,
        activity: RawData,
    ) -> Dict[str, Any]:
        """
        Analyze sentiment of a single activity.

        Args:
            db: Database session
            activity: RawData instance

        Returns:
            Sentiment analysis results
        """
        # Extract text based on activity type
        text = self._extract_text(activity)

        if not text:
            return None

        # Analyze sentiment
        scores = self.analyze_text(text)

        # Create metric
        metric = Metric(
            user_id=activity.data_source.user_id if hasattr(activity, "data_source") else None,
            metric_type="sentiment",
            metric_name=f"{activity.data_type}_sentiment",
            value=scores["compound"],
            timestamp=activity.timestamp,
            metadata={
                "positive": scores["positive"],
                "negative": scores["negative"],
                "neutral": scores["neutral"],
                "text_length": len(text),
            }
        )

        db.add(metric)
        await db.commit()

        return {
            "activity_id": activity.id,
            "sentiment": scores,
            "classification": self._classify_sentiment(scores["compound"]),
        }

    async def analyze_batch(
        self,
        db: AsyncSession,
        activities: List[RawData],
    ) -> List[Dict[str, Any]]:
        """
        Analyze sentiment of multiple activities.

        Args:
            db: Database session
            activities: List of RawData instances

        Returns:
            List of sentiment analysis results
        """
        results = []

        for activity in activities:
            try:
                result = await self.analyze_activity(db, activity)
                if result:
                    results.append(result)
            except Exception as e:
                logger.error(f"Error analyzing activity {activity.id}: {e}")

        return results

    def _extract_text(self, activity: RawData) -> str:
        """Extract text from activity content."""
        content = activity.content

        # Twitter tweet
        if activity.data_type == "twitter_tweet":
            return content.get("text", "")

        # Gmail email
        elif activity.data_type in ["gmail_sent", "gmail_received"]:
            subject = content.get("subject", "")
            snippet = content.get("snippet", "")
            return f"{subject} {snippet}"

        # GitHub commit
        elif activity.data_type == "github_commit":
            return content.get("message", "")

        # Calendar event
        elif activity.data_type == "calendar_event":
            summary = content.get("summary", "")
            description = content.get("description", "")
            return f"{summary} {description}"

        return ""

    def _classify_sentiment(self, compound: float) -> str:
        """
        Classify sentiment based on compound score.

        Args:
            compound: Compound score from VADER

        Returns:
            Sentiment classification
        """
        if compound >= 0.05:
            return "positive"
        elif compound <= -0.05:
            return "negative"
        else:
            return "neutral"


analyzer = SentimentAnalyzer()
