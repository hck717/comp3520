"""Train Variational Quantum Classifier for anomaly detection."""

import logging
import numpy as np
import pennylane as qml
from pennylane import numpy as pnp
import joblib
from pathlib import Path
from sklearn.metrics import classification_report

logger = logging.getLogger(__name__)

# Define 4-qubit quantum device
dev = qml.device('default.qubit', wires=4)

@qml.qnode(dev)
def quantum_circuit(features, weights):
    """
    4-qubit VQC with amplitude encoding and parameterized rotation gates.
    
    Args:
        features: 4D normalized feature vector (will be padded to 16D)
        weights: Trainable parameters (3 layers x 4 qubits x 3 rotations)
        
    Returns:
        Expectation value of Pauli-Z on qubit 0
    """
    # AmplitudeEmbedding requires 2^n features for n qubits
    # For 4 qubits, need 16 features. Pad with parameter.
    qml.AmplitudeEmbedding(features, wires=range(4), normalize=True, pad_with=0.0)
    
    # Variational layers
    n_layers = 3
    for layer in range(n_layers):
        # Parameterized rotations
        for i in range(4):
            qml.RY(weights[layer][i][0], wires=i)
            qml.RZ(weights[layer][i][1], wires=i)
        
        # Entanglement
        for i in range(3):
            qml.CNOT(wires=[i, i+1])
        qml.CNOT(wires=[3, 0])  # Circular entanglement
    
    return qml.expval(qml.PauliZ(0))


def cost_function(weights, features, labels):
    """
    Mean squared error loss for binary classification.
    
    Args:
        weights: VQC parameters
        features: Batch of normalized features (each padded to 16D)
        labels: True labels (0 or 1)
        
    Returns:
        Average MSE loss
    """
    predictions = [quantum_circuit(f, weights) for f in features]
    predictions = pnp.array(predictions)
    
    # Convert labels: 0 -> +1, 1 -> -1 (for Pauli-Z expectation)
    target_values = 1 - 2 * labels
    
    loss = pnp.mean((predictions - target_values) ** 2)
    return loss


def generate_synthetic_data(n_samples=200, seed=42):
    """
    Generate synthetic 4D data for quantum training.
    Features are padded to 16D for AmplitudeEmbedding.
    
    Returns:
        features (n_samples, 16), labels (n_samples,)
    """
    np.random.seed(seed)
    
    # Normal transactions (label=0) - generate 4D, will pad to 16D
    n_normal = int(n_samples * 0.7)
    normal_features_4d = np.random.rand(n_normal, 4) * 0.5 + 0.25  # Clustered
    normal_labels = np.zeros(n_normal)
    
    # Anomalous transactions (label=1)
    n_anomaly = n_samples - n_normal
    anomaly_features_4d = np.random.rand(n_anomaly, 4)
    anomaly_features_4d[:, 0] *= 0.3  # Low amount norm
    anomaly_features_4d[:, 2] += 0.5  # High port risk
    anomaly_features_4d = np.clip(anomaly_features_4d, 0, 1)
    anomaly_labels = np.ones(n_anomaly)
    
    # Combine 4D features
    features_4d = np.vstack([normal_features_4d, anomaly_features_4d])
    labels = np.hstack([normal_labels, anomaly_labels])
    
    # Pad to 16D for AmplitudeEmbedding (2^4 = 16)
    features = np.pad(features_4d, ((0, 0), (0, 12)), mode='constant', constant_values=0)
    
    # Shuffle
    indices = np.random.permutation(n_samples)
    return features[indices], labels[indices]


def train_quantum_model(
    n_samples: int = 200,
    n_epochs: int = 50,
    learning_rate: float = 0.1,
    output_path: str = "models/quantum_vqc.pkl"
):
    """
    Train VQC for anomaly detection.
    
    Args:
        n_samples: Number of training samples
        n_epochs: Training epochs
        learning_rate: Optimizer learning rate
        output_path: Path to save trained weights
        
    Returns:
        Dictionary with metrics
    """
    logger.info("Generating synthetic training data...")
    features, labels = generate_synthetic_data(n_samples)
    
    # Convert to PennyLane arrays
    features = pnp.array(features, requires_grad=False)
    labels = pnp.array(labels, requires_grad=False)
    
    # Initialize weights (3 layers x 4 qubits x 2 rotations)
    np.random.seed(42)
    weights = pnp.random.rand(3, 4, 2) * 2 * np.pi
    weights = pnp.array(weights, requires_grad=True)
    
    # Optimizer
    optimizer = qml.GradientDescentOptimizer(stepsize=learning_rate)
    
    # Training loop
    logger.info("Training VQC...")
    for epoch in range(n_epochs):
        weights = optimizer.step(lambda w: cost_function(w, features, labels), weights)
        
        if (epoch + 1) % 10 == 0:
            loss = cost_function(weights, features, labels)
            logger.info(f"Epoch {epoch+1}/{n_epochs}, Loss: {loss:.4f}")
    
    # Final evaluation
    predictions = pnp.array([quantum_circuit(f, weights) for f in features])
    pred_labels = (predictions < 0).astype(int)  # Negative -> anomaly (1)
    
    report = classification_report(labels, pred_labels, output_dict=True, zero_division=0)
    
    # Safe metric extraction
    if '1' in report:
        precision = report['1']['precision']
        recall = report['1']['recall']
        f1_score = report['1']['f1-score']
    else:
        precision = recall = f1_score = 0.0
        logger.warning("Class '1' not found in classification report")
    
    logger.info(f"\nFinal Performance:")
    logger.info(f"  Precision: {precision:.3f}")
    logger.info(f"  Recall: {recall:.3f}")
    logger.info(f"  F1-Score: {f1_score:.3f}")
    
    # Save weights
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({'weights': weights, 'n_qubits': 4}, output_path)
    logger.info(f"\nModel saved to {output_path}")
    
    return {
        'final_loss': float(cost_function(weights, features, labels)),
        'train_precision': precision,
        'train_recall': recall,
        'train_f1': f1_score,
    }


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    metrics = train_quantum_model(n_samples=200, n_epochs=50)
    print("\nQuantum training complete!")
