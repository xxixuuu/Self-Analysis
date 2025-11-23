"""
Correlation analysis engine.
"""
import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
import pandas as pd
from scipy import stats
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import Metric

logger = logging.getLogger(__name__)


class CorrelationAnalyzer:
    """Analyzer for detecting correlations between different metrics."""

    async def analyze_correlations(
        self,
        db: AsyncSession,
        user_id: int,
        days: int = 30,
        min_correlation: float = 0.3,
    ) -> List[Dict[str, Any]]:
        """
        Analyze correlations between metrics.

        Args:
            db: Database session
            user_id: User ID
            days: Number of days to analyze
            min_correlation: Minimum correlation coefficient to report

        Returns:
            List of significant correlations
        """
        # Get metrics for the period
        start_date = datetime.utcnow() - timedelta(days=days)

        result = await db.execute(
            select(Metric).where(
                Metric.user_id == user_id,
                Metric.timestamp >= start_date,
            ).order_by(Metric.timestamp.asc())
        )
        metrics = result.scalars().all()

        if not metrics:
            return []

        # Create DataFrame
        data = []
        for metric in metrics:
            data.append({
                "date": metric.timestamp.date(),
                "metric_type": metric.metric_type,
                "metric_name": metric.metric_name,
                "value": metric.value,
            })

        df = pd.DataFrame(data)

        # Pivot to get metrics as columns
        pivot_df = df.pivot_table(
            index="date",
            columns=["metric_type", "metric_name"],
            values="value",
            aggfunc="mean",
        )

        # Calculate correlations
        correlations = []

        for col1 in pivot_df.columns:
            for col2 in pivot_df.columns:
                if col1 >= col2:  # Avoid duplicates
                    continue

                # Calculate Pearson correlation
                col1_data = pivot_df[col1].dropna()
                col2_data = pivot_df[col2].dropna()

                # Need at least 3 data points
                common_dates = col1_data.index.intersection(col2_data.index)
                if len(common_dates) < 3:
                    continue

                col1_values = pivot_df.loc[common_dates, col1]
                col2_values = pivot_df.loc[common_dates, col2]

                corr, p_value = stats.pearsonr(col1_values, col2_values)

                # Only report significant correlations
                if abs(corr) >= min_correlation and p_value < 0.05:
                    correlations.append({
                        "metric1": f"{col1[0]}:{col1[1]}",
                        "metric2": f"{col2[0]}:{col2[1]}",
                        "correlation": round(corr, 3),
                        "p_value": round(p_value, 4),
                        "strength": self._interpret_correlation(corr),
                        "interpretation": self._generate_interpretation(col1, col2, corr),
                    })

        # Sort by absolute correlation
        correlations.sort(key=lambda x: abs(x["correlation"]), reverse=True)

        return correlations

    def _interpret_correlation(self, corr: float) -> str:
        """Interpret correlation strength."""
        abs_corr = abs(corr)
        if abs_corr >= 0.7:
            return "strong"
        elif abs_corr >= 0.4:
            return "moderate"
        else:
            return "weak"

    def _generate_interpretation(
        self,
        metric1: Tuple,
        metric2: Tuple,
        corr: float,
    ) -> str:
        """Generate human-readable interpretation."""
        direction = "positively" if corr > 0 else "negatively"
        metric1_name = f"{metric1[0]} {metric1[1]}"
        metric2_name = f"{metric2[0]} {metric2[1]}"

        return (
            f"{metric1_name} is {direction} correlated with {metric2_name}. "
            f"When {metric1_name} increases, {metric2_name} tends to "
            f"{'increase' if corr > 0 else 'decrease'}."
        )


analyzer = CorrelationAnalyzer()
