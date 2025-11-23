"""
Predictive analysis engine using simple time series models.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import Metric

logger = logging.getLogger(__name__)


class ProductivityPredictor:
    """Predictor for productivity metrics."""

    async def predict_tomorrow(
        self,
        db: AsyncSession,
        user_id: int,
        metric_type: str = "productivity",
        metric_name: str = "daily_score",
    ) -> Optional[Dict[str, Any]]:
        """
        Predict tomorrow's productivity score.

        Args:
            db: Database session
            user_id: User ID
            metric_type: Metric type to predict
            metric_name: Metric name to predict

        Returns:
            Prediction results
        """
        # Get last 30 days of data
        start_date = datetime.utcnow() - timedelta(days=30)

        result = await db.execute(
            select(Metric).where(
                Metric.user_id == user_id,
                Metric.metric_type == metric_type,
                Metric.metric_name == metric_name,
                Metric.timestamp >= start_date,
            ).order_by(Metric.timestamp.asc())
        )
        metrics = result.scalars().all()

        if len(metrics) < 7:  # Need at least a week of data
            return None

        # Create DataFrame
        data = [{
            "date": m.timestamp.date(),
            "value": m.value,
        } for m in metrics]

        df = pd.DataFrame(data)

        # Group by date and average (in case of multiple values per day)
        df = df.groupby("date").mean().reset_index()

        # Create features (days since start)
        df["days"] = (df["date"] - df["date"].min()).dt.days

        # Simple linear regression
        X = df[["days"]].values
        y = df["value"].values

        model = LinearRegression()
        model.fit(X, y)

        # Predict tomorrow (next day after last data point)
        last_day = df["days"].max()
        tomorrow_day = last_day + 1

        prediction = model.predict([[tomorrow_day]])[0]

        # Calculate confidence based on R²
        r_squared = model.score(X, y)

        # Calculate trend
        trend = "increasing" if model.coef_[0] > 0 else "decreasing"
        trend_strength = abs(model.coef_[0])

        return {
            "predicted_value": round(float(prediction), 2),
            "confidence": round(float(r_squared), 2),
            "trend": trend,
            "trend_strength": round(float(trend_strength), 4),
            "historical_avg": round(float(df["value"].mean()), 2),
            "historical_std": round(float(df["value"].std()), 2),
            "days_of_data": len(df),
        }

    async def detect_patterns(
        self,
        db: AsyncSession,
        user_id: int,
        metric_type: str = "productivity",
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Detect patterns in productivity data.

        Args:
            db: Database session
            user_id: User ID
            metric_type: Metric type to analyze
            days: Number of days to analyze

        Returns:
            Detected patterns
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        result = await db.execute(
            select(Metric).where(
                Metric.user_id == user_id,
                Metric.metric_type == metric_type,
                Metric.timestamp >= start_date,
            ).order_by(Metric.timestamp.asc())
        )
        metrics = result.scalars().all()

        if not metrics:
            return {}

        # Create DataFrame with datetime index
        data = [{
            "timestamp": m.timestamp,
            "metric_name": m.metric_name,
            "value": m.value,
        } for m in metrics]

        df = pd.DataFrame(data)

        # Analyze by day of week
        df["day_of_week"] = df["timestamp"].dt.day_name()
        day_of_week_avg = df.groupby("day_of_week")["value"].mean().to_dict()

        # Analyze by hour
        df["hour"] = df["timestamp"].dt.hour
        hour_avg = df.groupby("hour")["value"].mean().to_dict()

        # Find best performing times
        if hour_avg:
            best_hour = max(hour_avg.items(), key=lambda x: x[1])
            worst_hour = min(hour_avg.items(), key=lambda x: x[1])
        else:
            best_hour = (None, 0)
            worst_hour = (None, 0)

        # Find best performing day
        if day_of_week_avg:
            best_day = max(day_of_week_avg.items(), key=lambda x: x[1])
            worst_day = min(day_of_week_avg.items(), key=lambda x: x[1])
        else:
            best_day = (None, 0)
            worst_day = (None, 0)

        return {
            "day_of_week_patterns": day_of_week_avg,
            "hourly_patterns": hour_avg,
            "best_hour": {"hour": best_hour[0], "avg_value": round(float(best_hour[1]), 2)},
            "worst_hour": {"hour": worst_hour[0], "avg_value": round(float(worst_hour[1]), 2)},
            "best_day": {"day": best_day[0], "avg_value": round(float(best_day[1]), 2)},
            "worst_day": {"day": worst_day[0], "avg_value": round(float(worst_day[1]), 2)},
        }

    async def detect_anomalies(
        self,
        db: AsyncSession,
        user_id: int,
        metric_type: str = "productivity",
        threshold_std: float = 2.0,
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalies in metric values.

        Args:
            db: Database session
            user_id: User ID
            metric_type: Metric type to analyze
            threshold_std: Number of standard deviations for anomaly threshold

        Returns:
            List of detected anomalies
        """
        # Get last 30 days
        start_date = datetime.utcnow() - timedelta(days=30)

        result = await db.execute(
            select(Metric).where(
                Metric.user_id == user_id,
                Metric.metric_type == metric_type,
                Metric.timestamp >= start_date,
            ).order_by(Metric.timestamp.asc())
        )
        metrics = result.scalars().all()

        if not metrics:
            return []

        # Calculate statistics
        values = [m.value for m in metrics]
        mean = np.mean(values)
        std = np.std(values)

        # Detect anomalies
        anomalies = []
        for metric in metrics:
            z_score = (metric.value - mean) / std if std > 0 else 0

            if abs(z_score) > threshold_std:
                anomalies.append({
                    "id": metric.id,
                    "timestamp": metric.timestamp.isoformat(),
                    "metric_name": metric.metric_name,
                    "value": metric.value,
                    "mean": round(float(mean), 2),
                    "std": round(float(std), 2),
                    "z_score": round(float(z_score), 2),
                    "type": "high" if z_score > 0 else "low",
                })

        return anomalies


predictor = ProductivityPredictor()
