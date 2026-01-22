"""Quantum-enhanced anomaly detection using trained VQC."""

import logging
import numpy as np
import pennylane as qml
from pennylane import numpy as pnp
import joblib
from typing import Dict
from pathlib import Path

# Fix: Use absolute import instead of relative
try:
    from src.skills.quantum_anomaly.scripts.extract_quantum_features import normalize_features
except ImportError:
    # Fallback for when run as module
    from extract_quantum_features import normalize_features

logger = logging.getLogger(__name__)

# Quantum device
dev = qml.device('default.qubit', wires=4)

@qml.qnode(dev)
def quantum_circuit(features, weights):
    """VQC inference circuit."""
    # AmplitudeEmbedding requires 16 features for 4 qubits
    qml.AmplitudeEmbedding(features, wires=range(4), normalize=True, pad_with=0.0)
    
    n_layers = 3
    for layer in range(n_layers):
        for i in range(4):
            qml.RY(weights[layer][i][0], wires=i)
            qml.RZ(weights[layer][i][1], wires=i)
        for i in range(3):
            qml.CNOT(wires=[i, i+1])
        qml.CNOT(wires=[3, 0])
    
    return qml.expval(qml.PauliZ(0))


def detect_anomaly_quantum(
    features: Dict,
    model_path: str = "models/quantum_vqc.pkl"
) -> Dict:
    """
    Detect anomalies using quantum VQC.
    
    Args:
        features: Dictionary with:
            - amount_deviation
            - time_deviation
            - port_risk
            - doc_completeness
        model_path: Path to trained VQC weights
        
    Returns:
        Dictionary with:
        - quantum_score: VQC output (-1 to +1)
        - is_anomaly: Boolean
        - anomaly_confidence: Confidence (0-1)
    """
    if not Path(model_path).exists():
        logger.error(f"Model not found: {model_path}")
        raise FileNotFoundError(f"Model not found: {model_path}")
    
    # Load trained weights
    artifacts = joblib.load(model_path)
    weights = artifacts['weights']
    
    # Normalize features to 4D array
    normalized = normalize_features(features)
    
    # Pad to 16D for AmplitudeEmbedding (2^4 = 16)
    normalized_padded = np.pad(normalized, (0, 12), mode='constant', constant_values=0)
    normalized_padded = pnp.array(normalized_padded, requires_grad=False)
    
    # Run quantum circuit
    quantum_score = quantum_circuit(normalized_padded, weights)
    
    # Interpret score
    # Negative score -> anomaly
    is_anomaly = float(quantum_score) < 0
    
    # Convert to confidence [0, 1]
    # More negative = higher anomaly confidence
    anomaly_confidence = (1 - float(quantum_score)) / 2  # Map [-1,1] -> [1,0]
    
    logger.info(f"Quantum detection: {is_anomaly} (score: {quantum_score:.2f})")
    
    return {
        'quantum_score': float(quantum_score),
        'is_anomaly': bool(is_anomaly),
        'anomaly_confidence': float(anomaly_confidence)
    }


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Test with normal transaction
    result_normal = detect_anomaly_quantum({
        'amount_deviation': 0.5,
        'time_deviation': 0.3,
        'port_risk': 0.2,
        'doc_completeness': 0.95
    })
    print(f"\nNormal transaction: {result_normal}")
    
    # Test with anomalous transaction
    result_anomaly = detect_anomaly_quantum({
        'amount_deviation': 3.0,
        'time_deviation': 0.1,
        'port_risk': 0.9,
        'doc_completeness': 0.4
    })
    print(f"\nAnomalous transaction: {result_anomaly}")
