"""
AI-powered analysis engine using Ollama.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.ollama.client import ollama_client

logger = logging.getLogger(__name__)


class AIAnalyzer:
    """AI analyzer for generating insights from user data."""

    async def generate_daily_summary(
        self,
        activities: List[Dict[str, Any]],
        date: datetime,
    ) -> Optional[str]:
        """
        Generate daily summary from activities.

        Args:
            activities: List of daily activities
            date: Date for the summary

        Returns:
            Daily summary text
        """
        if not activities:
            return "No activities recorded for this day."

        # Prepare activity summary
        activity_text = self._format_activities(activities)

        prompt = f"""
Based on the following activities from {date.strftime('%Y-%m-%d')}, generate a concise daily summary:

{activity_text}

Provide a brief summary (3-5 sentences) highlighting:
1. Main accomplishments
2. Overall productivity level
3. Notable patterns or insights
"""

        system = "You are a helpful AI assistant analyzing personal life data to provide insights."

        return await ollama_client.generate(
            prompt=prompt,
            system=system,
            temperature=0.7,
        )

    async def analyze_emotion(
        self,
        text: str,
    ) -> Dict[str, Any]:
        """
        Analyze emotion from text.

        Args:
            text: Text to analyze

        Returns:
            Dict with emotion analysis results
        """
        prompt = f"""
Analyze the emotional tone of the following text and provide:
1. Overall sentiment (positive/neutral/negative)
2. Dominant emotion (joy, sadness, anger, fear, surprise, etc.)
3. Confidence score (0-1)

Text: {text}

Respond in JSON format:
{{
    "sentiment": "positive/neutral/negative",
    "emotion": "emotion_name",
    "confidence": 0.0-1.0
}}
"""

        system = "You are an emotion analysis AI. Respond only with valid JSON."

        response = await ollama_client.generate(
            prompt=prompt,
            system=system,
            temperature=0.3,
        )

        try:
            import json
            return json.loads(response) if response else {}
        except Exception:
            logger.error("Failed to parse emotion analysis response")
            return {"sentiment": "neutral", "emotion": "unknown", "confidence": 0.0}

    async def extract_topics(
        self,
        texts: List[str],
        max_topics: int = 5,
    ) -> List[str]:
        """
        Extract main topics from texts.

        Args:
            texts: List of texts to analyze
            max_topics: Maximum number of topics to extract

        Returns:
            List of topic names
        """
        if not texts:
            return []

        combined_text = "\n\n".join(texts[:50])  # Limit to first 50 texts

        prompt = f"""
Analyze the following texts and extract the top {max_topics} main topics or themes:

{combined_text[:2000]}  # Limit length

List only the topic names, one per line.
"""

        system = "You are a topic extraction AI. Extract only the main topics without explanations."

        response = await ollama_client.generate(
            prompt=prompt,
            system=system,
            temperature=0.5,
        )

        if response:
            topics = [
                topic.strip()
                for topic in response.split("\n")
                if topic.strip() and not topic.strip().startswith("-")
            ]
            return topics[:max_topics]

        return []

    async def generate_productivity_advice(
        self,
        metrics: Dict[str, Any],
    ) -> Optional[str]:
        """
        Generate productivity advice based on metrics.

        Args:
            metrics: User productivity metrics

        Returns:
            Productivity advice text
        """
        metrics_text = self._format_metrics(metrics)

        prompt = f"""
Based on the following productivity metrics, provide actionable advice:

{metrics_text}

Generate 3-5 specific, actionable recommendations to improve productivity.
"""

        system = "You are a productivity coach providing personalized advice."

        return await ollama_client.generate(
            prompt=prompt,
            system=system,
            temperature=0.7,
        )

    async def answer_natural_language_query(
        self,
        query: str,
        context: Dict[str, Any],
    ) -> Optional[str]:
        """
        Answer natural language query about user data.

        Args:
            query: User's question
            context: Relevant data context

        Returns:
            Answer to the question
        """
        context_text = self._format_context(context)

        messages = [
            {
                "role": "system",
                "content": "You are an AI assistant helping users understand their personal data. "
                          "Provide clear, concise answers based on the data provided."
            },
            {
                "role": "user",
                "content": f"Data context:\n{context_text}\n\nQuestion: {query}"
            }
        ]

        return await ollama_client.chat(
            messages=messages,
            temperature=0.5,
        )

    async def generate_weekly_report(
        self,
        weekly_data: Dict[str, Any],
    ) -> Optional[str]:
        """
        Generate weekly report from data.

        Args:
            weekly_data: Week's data summary

        Returns:
            Weekly report text
        """
        data_text = self._format_context(weekly_data)

        prompt = f"""
Generate a comprehensive weekly report based on the following data:

{data_text}

Include:
1. Overview of the week
2. Key achievements
3. Productivity trends
4. Areas for improvement
5. Goals for next week
"""

        system = "You are a personal analytics assistant generating weekly reports."

        return await ollama_client.generate(
            prompt=prompt,
            system=system,
            temperature=0.7,
            max_tokens=1000,
        )

    def _format_activities(self, activities: List[Dict[str, Any]]) -> str:
        """Format activities for prompt."""
        lines = []
        for activity in activities:
            activity_type = activity.get("type", "unknown")
            content = activity.get("content", "")
            timestamp = activity.get("timestamp", "")
            lines.append(f"- [{timestamp}] {activity_type}: {content}")
        return "\n".join(lines[:50])  # Limit to 50 activities

    def _format_metrics(self, metrics: Dict[str, Any]) -> str:
        """Format metrics for prompt."""
        lines = []
        for key, value in metrics.items():
            lines.append(f"- {key}: {value}")
        return "\n".join(lines)

    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context for prompt."""
        import json
        try:
            return json.dumps(context, indent=2, default=str)
        except Exception:
            return str(context)


# Global AI analyzer instance
ai_analyzer = AIAnalyzer()
