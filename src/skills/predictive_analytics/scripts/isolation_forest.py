"""Real-time anomaly detection using Isolation Forest."""

import logging
import joblib
import numpy as np
from typing import Dict
from pathlib import Path

logger = logging.getLogger(__name__)

def detect_anomalies(
    features: Dict,
    model_path: str = "models/isolation_forest.pkl"
) -> Dict:
    """
    Detect anomalies in LC transactions using Isolation Forest.
    
    Args:
        features: Dictionary with:
            - amount_deviation: Deviation from average LC amount
            - time_deviation: Days since last transaction (normalized)
            - port_risk: Risk score of ports (0-1)
            - doc_completeness: Document completeness (0-1)
        model_path: Path to trained model
        
    Returns:
        Dictionary with:
        - is_anomaly: Boolean
        - anomaly_score: Decision function score
        - anomaly_confidence: Confidence level (0-1)
    """
    if not Path(model_path).exists():
        logger.error(f"Model not found: {model_path}")
        raise FileNotFoundError(f"Model not found: {model_path}")
    
    # Load model and scaler
    artifacts = joblib.load(model_path)
    model = artifacts['model']
    scaler = artifacts['scaler']
    
    # Prepare feature vector
    X = np.array([[
        features['amount_deviation'],
        features['time_deviation'],
        features['port_risk'],
        features['doc_completeness']
    ]])
    
    # Scale features
    X_scaled = scaler.transform(X)
    
    # Predict
    prediction = model.predict(X_scaled)[0]
    anomaly_score = model.decision_function(X_scaled)[0]
    
    is_anomaly = prediction == -1
    
    # Convert score to confidence (0-1)
    # More negative = more anomalous
    anomaly_confidence = 1 / (1 + np.exp(anomaly_score))  # Sigmoid
    
    logger.info(f"Anomaly detection: {is_anomaly} (score: {anomaly_score:.2f})")
    
    return {
        'is_anomaly': bool(is_anomaly),
        'anomaly_score': float(anomaly_score),
        'anomaly_confidence': float(anomaly_confidence)
    }


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Test with normal transaction
    result_normal = detect_anomalies({
        'amount_deviation': 0.5,
        'time_deviation': 0.3,
        'port_risk': 0.2,
        'doc_completeness': 0.95
    })
    print(f"\nNormal transaction: {result_normal}")
    
    # Test with anomalous transaction
    result_anomaly = detect_anomalies({
        'amount_deviation': 3.5,
        'time_deviation': 0.1,
        'port_risk': 0.9,
        'doc_completeness': 0.4
    })
    print(f"\nAnomalous transaction: {result_anomaly}")
