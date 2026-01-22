"""LC volume forecasting using Prophet."""

import logging
import joblib
import pandas as pd
from typing import Dict, List
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def forecast_lc_volume(
    forecast_days: int = 7,
    model_path: str = "models/prophet_lc_volume.pkl"
) -> Dict:
    """
    Forecast LC transaction volume using Prophet.
    
    Args:
        forecast_days: Number of days to forecast
        model_path: Path to trained Prophet model
        
    Returns:
        Dictionary with:
        - predictions: List of {date, lc_count, lower_bound, upper_bound}
        - trend: "increasing", "decreasing", or "stable"
    """
    if not Path(model_path).exists():
        logger.error(f"Model not found: {model_path}")
        raise FileNotFoundError(f"Model not found: {model_path}")
    
    # Load model
    model = joblib.load(model_path)
    logger.info(f"Loaded Prophet model from {model_path}")
    
    # Create future dataframe
    future = model.make_future_dataframe(periods=forecast_days)
    
    # Forecast
    forecast = model.predict(future)
    
    # Extract last N days (the forecast)
    forecast_subset = forecast.tail(forecast_days)
    
    # Format predictions
    predictions = []
    for _, row in forecast_subset.iterrows():
        predictions.append({
            'date': row['ds'].strftime('%Y-%m-%d'),
            'lc_count': int(max(0, row['yhat'])),  # No negative counts
            'lower_bound': int(max(0, row['yhat_lower'])),
            'upper_bound': int(max(0, row['yhat_upper']))
        })
    
    # Determine trend
    first_value = predictions[0]['lc_count']
    last_value = predictions[-1]['lc_count']
    
    if last_value > first_value * 1.1:
        trend = "increasing"
    elif last_value < first_value * 0.9:
        trend = "decreasing"
    else:
        trend = "stable"
    
    logger.info(f"Forecasted {forecast_days} days: {trend} trend")
    
    return {
        'predictions': predictions,
        'trend': trend
    }


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Forecast next 7 days
    result = forecast_lc_volume(forecast_days=7)
    
    print("\nLC Volume Forecast (Next 7 Days):")
    for pred in result['predictions']:
        print(f"  {pred['date']}: {pred['lc_count']} LCs (range: {pred['lower_bound']}-{pred['upper_bound']})")
    print(f"\nTrend: {result['trend']}")
