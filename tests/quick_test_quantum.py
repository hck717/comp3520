#!/usr/bin/env python3
"""
Quick test for Quantum Anomaly Detection Skill.

Run: python tests/quick_test_quantum.py
"""

import sys
import time
import numpy as np
sys.path.insert(0, 'src')

def main():
    print("\n" + "="*60)
    print("QUICK TEST: Quantum Anomaly Detection Skill")
    print("="*60)
    
    # Test 1: Feature normalization
    print("\n[Test 1] Testing 4D feature normalization...")
    from skills.quantum_anomaly.scripts.extract_quantum_features import normalize_features
    
    # Normal transaction
    features_normal = {
        'amount_deviation': 0.5,
        'time_deviation': 1.0,
        'port_risk': 0.3,
        'doc_completeness': 0.95
    }
    
    normalized = normalize_features(features_normal)
    
    print(f"  Input: {features_normal}")
    print(f"  Normalized: {normalized}")
    
    assert np.all(normalized >= 0) and np.all(normalized <= 1), "Not in [0,1]"
    assert len(normalized) == 4, "Should be 4D"
    print("  ✅ PASSED")
    
    # Test 2: VQC circuit execution
    print("\n[Test 2] Testing 4-qubit VQC circuit...")
    
    import pennylane as qml
    from pennylane import numpy as pnp
    
    # Define quantum device
    dev = qml.device('default.qubit', wires=4)
    
    @qml.qnode(dev)
    def quantum_circuit(features, weights):
        # Amplitude encoding
        qml.AmplitudeEmbedding(features, wires=range(4), normalize=True)
        
        # Variational layers (simplified for quick test)
        for i in range(4):
            qml.RY(weights[i], wires=i)
        for i in range(3):
            qml.CNOT(wires=[i, i+1])
        
        return qml.expval(qml.PauliZ(0))
    
    # Test circuit
    test_features = pnp.array([0.5, 0.3, 0.7, 0.9])
    test_weights = pnp.random.rand(4) * np.pi
    
    start = time.time()
    output = quantum_circuit(test_features, test_weights)
    inference_time = (time.time() - start) * 1000
    
    print(f"  Circuit Output: {output:.4f}")
    print(f"  Inference Time: {inference_time:.1f}ms")
    
    assert -1 <= output <= 1, "Output out of range"
    print("  ✅ PASSED")
    
    # Test 3: Light VQC training
    print("\n[Test 3] Training VQC (10 epochs, quick test)...")
    from skills.quantum_anomaly.scripts.train_vqc import train_quantum_model
    
    start = time.time()
    metrics = train_quantum_model(
        n_samples=100,  # Small dataset
        n_epochs=10,    # Few epochs
        output_path='models/quantum_vqc_test.pkl'
    )
    train_time = time.time() - start
    
    print(f"  Training Time: {train_time:.1f}s")
    print(f"  Final Loss: {metrics['final_loss']:.3f}")
    print(f"  Train F1: {metrics['train_f1']:.3f}")
    
    assert train_time < 60, "Training too slow for quick test"
    print("  ✅ PASSED")
    
    # Test 4: Quantum inference
    print("\n[Test 4] Testing quantum anomaly detection...")
    from skills.quantum_anomaly.scripts.detect_quantum import detect_anomaly_quantum
    
    # Anomalous features (high deviation, high risk)
    anomalous_features = {
        'amount_deviation': 2.8,
        'time_deviation': 0.2,
        'port_risk': 0.9,
        'doc_completeness': 0.5
    }
    
    result = detect_anomaly_quantum(
        features=anomalous_features,
        model_path='models/quantum_vqc_test.pkl'
    )
    
    print(f"  Quantum Score: {result['quantum_score']:.2f}")
    print(f"  Is Anomaly: {result['is_anomaly']}")
    print(f"  Confidence: {result['anomaly_confidence']:.0%}")
    
    print("  ✅ PASSED")
    
    print("\n" + "="*60)
    print("✅ ALL QUANTUM ANOMALY TESTS PASSED")
    print("="*60)
    print("\n💡 For full quantum training & benchmarking:")
    print("   python src/skills/quantum_anomaly/scripts/benchmark.py")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
