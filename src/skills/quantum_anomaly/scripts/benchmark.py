"""Benchmark quantum vs classical anomaly detection."""

import logging
import time
import numpy as np
from .train_vqc import train_quantum_model, generate_synthetic_data
from ..scripts.detect_quantum import detect_anomaly_quantum
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report

logger = logging.getLogger(__name__)

def benchmark_quantum_vs_classical(
    n_samples: int = 200,
    n_test: int = 50
):
    """
    Compare quantum VQC vs classical Isolation Forest.
    
    Args:
        n_samples: Training samples
        n_test: Test samples
    """
    logger.info("=" * 60)
    logger.info("QUANTUM VS CLASSICAL ANOMALY DETECTION BENCHMARK")
    logger.info("=" * 60)
    
    # Generate data
    logger.info("\nGenerating data...")
    X_train, y_train = generate_synthetic_data(n_samples)
    X_test, y_test = generate_synthetic_data(n_test, seed=99)
    
    # --- Quantum VQC ---
    logger.info("\n[1/2] Training Quantum VQC...")
    start = time.time()
    quantum_metrics = train_quantum_model(
        n_samples=n_samples,
        n_epochs=30,  # Fewer epochs for benchmark
        output_path='models/quantum_vqc_benchmark.pkl'
    )
    quantum_train_time = time.time() - start
    
    # Test quantum inference
    logger.info("Testing quantum inference...")
    start = time.time()
    quantum_predictions = []
    for features in X_test:
        result = detect_anomaly_quantum(
            {
                'amount_deviation': float(features[0] * 6 - 3),  # Denormalize
                'time_deviation': float(features[1]),
                'port_risk': float(features[2]),
                'doc_completeness': float(features[3])
            },
            model_path='models/quantum_vqc_benchmark.pkl'
        )
        quantum_predictions.append(1 if result['is_anomaly'] else 0)
    quantum_inference_time = (time.time() - start) / n_test * 1000  # ms per sample
    
    quantum_report = classification_report(y_test, quantum_predictions, output_dict=True, zero_division=0)
    
    # --- Classical Isolation Forest ---
    logger.info("\n[2/2] Training Classical Isolation Forest...")
    start = time.time()
    clf = IsolationForest(contamination=0.3, random_state=42)
    clf.fit(X_train)
    classical_train_time = time.time() - start
    
    # Test classical inference
    start = time.time()
    classical_predictions = clf.predict(X_test)
    classical_predictions = np.where(classical_predictions == -1, 1, 0)
    classical_inference_time = (time.time() - start) / n_test * 1000  # ms per sample
    
    classical_report = classification_report(y_test, classical_predictions, output_dict=True, zero_division=0)
    
    # --- Results ---
    logger.info("\n" + "=" * 60)
    logger.info("BENCHMARK RESULTS")
    logger.info("=" * 60)
    
    logger.info("\nAccuracy Metrics:")
    logger.info(f"  Quantum VQC:")
    logger.info(f"    Precision: {quantum_report['1']['precision']:.3f}")
    logger.info(f"    Recall:    {quantum_report['1']['recall']:.3f}")
    logger.info(f"    F1-Score:  {quantum_report['1']['f1-score']:.3f}")
    
    logger.info(f"\n  Classical IF:")
    logger.info(f"    Precision: {classical_report['1']['precision']:.3f}")
    logger.info(f"    Recall:    {classical_report['1']['recall']:.3f}")
    logger.info(f"    F1-Score:  {classical_report['1']['f1-score']:.3f}")
    
    logger.info("\nPerformance Metrics:")
    logger.info(f"  Quantum VQC:")
    logger.info(f"    Training time:   {quantum_train_time:.2f}s")
    logger.info(f"    Inference time:  {quantum_inference_time:.2f}ms/sample")
    
    logger.info(f"\n  Classical IF:")
    logger.info(f"    Training time:   {classical_train_time:.2f}s")
    logger.info(f"    Inference time:  {classical_inference_time:.2f}ms/sample")
    
    logger.info("\n" + "=" * 60)
    logger.info("Quantum advantage: Potentially better feature representation")
    logger.info("Classical advantage: Faster inference for production")
    logger.info("=" * 60)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    benchmark_quantum_vs_classical(n_samples=200, n_test=50)
