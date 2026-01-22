"""Extract and normalize 4D features for quantum anomaly detection."""

import logging
import numpy as np
from typing import Dict

logger = logging.getLogger(__name__)

def normalize_features(features: Dict) -> np.ndarray:
    """
    Normalize 4D features to [0, 1] range for quantum encoding.
    
    Features:
    1. amount_deviation: LC amount deviation from average (z-score)
    2. time_deviation: Time since last transaction (0-1)
    3. port_risk: Port risk score (0-1)
    4. doc_completeness: Document completeness (0-1)
    
    Args:
        features: Dictionary with raw feature values
        
    Returns:
        Normalized 4D numpy array in [0, 1]
    """
    # Extract features
    amount_dev = features.get('amount_deviation', 0.0)
    time_dev = features.get('time_deviation', 0.5)
    port_risk = features.get('port_risk', 0.0)
    doc_comp = features.get('doc_completeness', 1.0)
    
    # Normalize amount_deviation (z-score) to [0, 1]
    # Assume z-scores typically in [-3, 3]
    amount_norm = np.clip((amount_dev + 3) / 6, 0, 1)
    
    # Time deviation already in [0, 1]
    time_norm = np.clip(time_dev, 0, 1)
    
    # Port risk already in [0, 1]
    port_norm = np.clip(port_risk, 0, 1)
    
    # Document completeness already in [0, 1]
    doc_norm = np.clip(doc_comp, 0, 1)
    
    normalized = np.array([amount_norm, time_norm, port_norm, doc_norm])
    
    logger.debug(f"Normalized features: {normalized}")
    
    return normalized


def extract_quantum_features(transaction_data: Dict) -> np.ndarray:
    """
    Extract and normalize features from transaction data.
    
    Args:
        transaction_data: Dictionary with transaction details
        
    Returns:
        4D normalized feature array
    """
    # Calculate features from transaction data
    features = {
        'amount_deviation': transaction_data.get('amount_deviation', 0.0),
        'time_deviation': transaction_data.get('time_deviation', 0.5),
        'port_risk': transaction_data.get('port_risk', 0.0),
        'doc_completeness': transaction_data.get('doc_completeness', 1.0),
    }
    
    return normalize_features(features)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Test normalization
    test_features = {
        'amount_deviation': 2.5,  # High deviation
        'time_deviation': 0.2,
        'port_risk': 0.8,
        'doc_completeness': 0.6
    }
    
    normalized = normalize_features(test_features)
    print(f"\nInput features: {test_features}")
    print(f"Normalized: {normalized}")
    print(f"Range check: min={normalized.min():.2f}, max={normalized.max():.2f}")
