"""Train Facebook Prophet for LC volume forecasting."""

import logging
import pandas as pd
import joblib
from pathlib import Path
from prophet import Prophet
import numpy as np
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def generate_synthetic_lc_volume(days: int = 365) -> pd.DataFrame:
    """
    Generate synthetic LC volume time series data.
    
    Returns:
        DataFrame with 'ds' (date) and 'y' (LC count) columns
    """
    np.random.seed(42)
    
    # Generate dates
    start_date = datetime.now() - timedelta(days=days)
    dates = [start_date + timedelta(days=i) for i in range(days)]
    
    # Generate LC counts with:
    # - Trend: slight increase over time
    # - Seasonality: weekly pattern (higher on weekdays)
    # - Noise: random variation
    
    trend = np.linspace(10, 20, days)
    seasonality = 5 * np.sin(np.arange(days) * 2 * np.pi / 7)  # Weekly
    noise = np.random.normal(0, 2, days)
    
    lc_counts = trend + seasonality + noise
    lc_counts = np.maximum(lc_counts, 0).astype(int)  # No negative counts
    
    df = pd.DataFrame({
        'ds': dates,
        'y': lc_counts
    })
    
    return df


def train_model(
    data_path: str = None,
    output_path: str = "models/prophet_lc_volume.pkl"
) -> str:
    """
    Train Prophet model for LC volume forecasting.
    
    Args:
        data_path: Path to CSV with 'ds' and 'y' columns (if None, uses synthetic data)
        output_path: Path to save model
        
    Returns:
        Path to saved model
    """
    # Load or generate data
    if data_path and Path(data_path).exists():
        logger.info(f"Loading data from {data_path}")
        df = pd.read_csv(data_path)
        df['ds'] = pd.to_datetime(df['ds'])
    else:
        logger.info("Generating synthetic LC volume data...")
        df = generate_synthetic_lc_volume(days=365)
    
    logger.info(f"Training on {len(df)} days of data")
    logger.info(f"Date range: {df['ds'].min()} to {df['ds'].max()}")
    logger.info(f"LC count range: {df['y'].min()} to {df['y'].max()}")
    
    # Train Prophet
    logger.info("Training Prophet model...")
    model = Prophet(
        daily_seasonality=False,
        weekly_seasonality=True,
        yearly_seasonality=False,
        changepoint_prior_scale=0.05
    )
    model.fit(df)
    
    # Save model
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output_path)
    logger.info(f"Model saved to {output_path}")
    
    return output_path


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    model_path = train_model(output_path='models/prophet_lc_volume.pkl')
    print(f"\nTraining complete! Model saved to {model_path}")
