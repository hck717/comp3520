"""Train Isolation Forest for transaction anomaly detection."""

import logging
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

def generate_synthetic_data(n_samples: int = 1000, contamination: float = 0.1):
    """
    Generate synthetic LC transaction data for training.
    
    Features:
    - amount_deviation: How much LC amount deviates from entity's average
    - time_deviation: Days since last transaction (normalized)
    - port_risk: Risk score of involved ports (0-1)
    - doc_completeness: Document completeness score (0-1)
    """
    np.random.seed(42)
    
    # Normal transactions
    n_normal = int(n_samples * (1 - contamination))
    normal_data = np.random.randn(n_normal, 4) * 0.5
    normal_data[:, 2] = np.clip(normal_data[:, 2], 0, 1)  # port_risk
    normal_data[:, 3] = np.clip(0.9 + normal_data[:, 3] * 0.1, 0.7, 1.0)  # doc_completeness
    normal_labels = np.zeros(n_normal)
    
    # Anomalous transactions
    n_anomaly = n_samples - n_normal
    anomaly_data = np.random.randn(n_anomaly, 4) * 2.5  # Higher variance
    anomaly_data[:, 0] += 3.0  # High amount deviation
    anomaly_data[:, 2] = np.clip(anomaly_data[:, 2] + 0.7, 0.5, 1.0)  # High port risk
    anomaly_data[:, 3] = np.clip(anomaly_data[:, 3] * 0.3, 0, 0.6)  # Low doc completeness
    anomaly_labels = np.ones(n_anomaly)
    
    # Combine
    X = np.vstack([normal_data, anomaly_data])
    y = np.hstack([normal_labels, anomaly_labels])
    
    # Shuffle
    indices = np.random.permutation(n_samples)
    return X[indices], y[indices]


def train_model(
    n_samples: int = 1000,
    contamination: float = 0.1,
    output_path: str = "models/isolation_forest.pkl"
):
    """
    Train Isolation Forest model for anomaly detection.
    
    Args:
        n_samples: Number of training samples
        contamination: Expected proportion of anomalies
        output_path: Path to save model
        
    Returns:
        Dictionary with metrics
    """
    logger.info("Generating synthetic training data...")
    X, y = generate_synthetic_data(n_samples, contamination)
    
    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Train Isolation Forest
    logger.info("Training Isolation Forest...")
    model = IsolationForest(
        contamination=contamination,
        random_state=42,
        n_estimators=100
    )
    model.fit(X_scaled)
    
    # Predict on training data
    y_pred = model.predict(X_scaled)
    y_pred = np.where(y_pred == -1, 1, 0)  # Convert -1 (anomaly) to 1
    
    # Metrics with safe handling of missing classes
    report = classification_report(y, y_pred, output_dict=True, zero_division=0)
    cm = confusion_matrix(y, y_pred)
    
    # Safely get metrics for class '1' (anomaly)
    if '1' in report:
        precision = report['1']['precision']
        recall = report['1']['recall']
        f1_score = report['1']['f1-score']
    else:
        # Fallback if class '1' not in report
        precision = 0.0
        recall = 0.0
        f1_score = 0.0
        logger.warning("Class '1' (anomaly) not found in classification report!")
    
    logger.info(f"\nModel Performance:")
    logger.info(f"  Precision: {precision:.3f}")
    logger.info(f"  Recall: {recall:.3f}")
    logger.info(f"  F1-Score: {f1_score:.3f}")
    logger.info(f"\nConfusion Matrix:")
    logger.info(f"  TN: {cm[0][0]}, FP: {cm[0][1] if cm.shape[1] > 1 else 0}")
    logger.info(f"  FN: {cm[1][0] if cm.shape[0] > 1 else 0}, TP: {cm[1][1] if cm.shape[0] > 1 and cm.shape[1] > 1 else 0}")
    
    # Save model and scaler
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({'model': model, 'scaler': scaler}, output_path)
    logger.info(f"\nModel saved to {output_path}")
    
    return {
        'precision': precision,
        'recall': recall,
        'f1_score': f1_score,
    }


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    metrics = train_model(n_samples=1000, output_path='models/isolation_forest.pkl')
    print("\nTraining complete!")
