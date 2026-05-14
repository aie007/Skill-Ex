import pandas as pd
import numpy as np
from shared.core.interfaces import ITrendEngine

class TrendAnalyzer(ITrendEngine):
    def get_timeseries_trends(self, df: pd.DataFrame, freq: str = 'D') -> pd.DataFrame:
        """Transforms raw links into a time-series of skill penetration."""
        # Pivot to get counts per skill per time period
        pivot_df = df.groupby([pd.Grouper(key='posted_at', freq=freq), 'skill_name']).size().unstack(fill_value=0)
        
        # Calculate market share (percentage of jobs mentioning the skill)
        total_jobs = pivot_df.sum(axis=1)
        relative_trends = pivot_df.divide(total_jobs, axis=0).fillna(0) * 100
        return relative_trends

    def calculate_momentum(self, trend_df: pd.DataFrame, window: int = 3) -> pd.Series:
        """Identifies which skills are growing fastest."""
        if len(trend_df) < window:
            return pd.Series()
        
        # Compare current average to previous average to smooth out noise
        current_val = trend_df.iloc[-window:].mean()
        previous_val = trend_df.iloc[-window*2:-window].mean()
        
        momentum = ((current_val - previous_val) / previous_val).replace([np.inf, -np.inf], 0).fillna(0)
        return momentum.sort_values(ascending=False)
