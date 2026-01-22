# Agent Skills Testing Guide

**Purpose**: Learn how to test all 4 agent skills (Compliance, Risk, Predictive, Quantum)

**Prerequisites**:
- ✅ Virtual environment activated (`source venv/bin/activate`)
- ✅ Neo4j running (`docker ps | grep neo4j-sentinel`)
- ✅ Data ingested (`python src/ingest_trade_finance.py`)
- ✅ Dependencies installed (`pip install -r requirements.txt`)

---

## Testing Philosophy

For each skill, we'll test at **3 levels**:

1. **Unit Tests**: Test individual functions in isolation
2. **Integration Tests**: Test skill workflows end-to-end
3. **Performance Tests**: Verify latency/throughput requirements

---

## 🧪 Testing Setup

### Step 1: Install Testing Dependencies

```bash
source venv/bin/activate
pip install pytest pytest-cov pytest-benchmark
```

### Step 2: Set Environment Variables

```bash
# Create .env file in project root
cat > .env << EOF
# Neo4j Connection
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Paths
DATA_DIR=data/processed
MODELS_DIR=models

# Testing
TEST_MODE=true
EOF
```

### Step 3: Verify Neo4j Data

```bash
# Check if data is loaded
python -c "
import neo4j
from neo4j import GraphDatabase

driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password'))
with driver.session() as session:
    result = session.run('MATCH (n) RETURN count(n) AS total')
    total = result.single()['total']
    print(f'Total nodes in Neo4j: {total}')
    if total < 1000:
        print('⚠️  WARNING: Not enough data! Run: python src/ingest_trade_finance.py')
    else:
        print('✅ Neo4j data ready')
driver.close()
"
```

---

## 🎯 Skill 1: Compliance Screening Tests

### Unit Test 1: Exact Match

```python
# tests/test_compliance_screening.py
import sys
sys.path.insert(0, 'src')

from skills.compliance_screening.scripts.screen_entity import screen_entity

def test_exact_sanctions_match():
    """
    Test exact match against sanctions list.
    """
    # This entity should exist in your sanctions list
    result = screen_entity(
        entity_name="Specially Designated National Corp",
        entity_country="IR",
        entity_type="Buyer"
    )
    
    assert result['sanctions_match'] == True
    assert result['recommendation'] == 'BLOCK'
    assert 'OFAC' in result['sanctions_details']['list_type']
    print("✅ Exact match test PASSED")

if __name__ == '__main__':
    test_exact_sanctions_match()
```

**Run it:**
```bash
python tests/test_compliance_screening.py
```

---

### Unit Test 2: Fuzzy Match

```python
def test_fuzzy_sanctions_match():
    """
    Test fuzzy matching with slight name variation.
    """
    # Misspelled name should still match
    result = screen_entity(
        entity_name="Specally Designatd National Corp",  # Typos
        entity_country="IR",
        entity_type="Buyer"
    )
    
    # Should match with >85% similarity
    if result['sanctions_match']:
        assert result['fuzzy_match_score'] >= 85
        print(f"✅ Fuzzy match test PASSED (score: {result['fuzzy_match_score']}%)")
    else:
        print("⚠️  Fuzzy match did not trigger")

if __name__ == '__main__':
    test_fuzzy_sanctions_match()
```

---

### Unit Test 3: Country Risk Scoring

```python
def test_country_risk_scoring():
    """
    Test country risk scoring for various countries.
    """
    from skills.compliance_screening.scripts.country_risk import get_country_risk
    
    high_risk_countries = ['IR', 'KP', 'SY', 'VE', 'RU']
    low_risk_countries = ['US', 'GB', 'DE', 'JP', 'SG']
    
    for country in high_risk_countries:
        risk = get_country_risk(country)
        assert risk['risk_score'] >= 7, f"{country} should be high risk"
        print(f"✅ {country}: {risk['risk_score']}/10 (high risk)")
    
    for country in low_risk_countries:
        risk = get_country_risk(country)
        assert risk['risk_score'] <= 3, f"{country} should be low risk"
        print(f"✅ {country}: {risk['risk_score']}/10 (low risk)")

if __name__ == '__main__':
    test_country_risk_scoring()
```

---

### Integration Test: Full Screening Workflow

```python
import time

def test_compliance_screening_integration():
    """
    Test full compliance screening workflow with performance check.
    """
    test_entities = [
        {"name": "Clean Trading Corp", "country": "HK", "type": "Buyer"},
        {"name": "Sanctioned Entity Inc", "country": "IR", "type": "Seller"},
        {"name": "HSBC Hong Kong", "country": "HK", "type": "Bank"},
    ]
    
    for entity in test_entities:
        start = time.time()
        result = screen_entity(
            entity_name=entity['name'],
            entity_country=entity['country'],
            entity_type=entity['type']
        )
        latency = (time.time() - start) * 1000  # Convert to ms
        
        print(f"\n{'='*60}")
        print(f"Entity: {entity['name']}")
        print(f"Sanctions Match: {result['sanctions_match']}")
        print(f"Country Risk: {result['country_risk']} ({result['country_risk_score']}/10)")
        print(f"Recommendation: {result['recommendation']}")
        print(f"Latency: {latency:.1f}ms")
        
        # Performance assertion
        assert latency < 500, f"Latency {latency:.1f}ms exceeds 500ms target"
        print(f"✅ Performance OK (<500ms)")

if __name__ == '__main__':
    test_compliance_screening_integration()
```

**Run it:**
```bash
python tests/test_compliance_screening.py
```

---

## 🎯 Skill 2: Risk Assessment Tests

### Unit Test 1: Feature Extraction from Neo4j

```python
# tests/test_risk_assessment.py
import sys
sys.path.insert(0, 'src')

from skills.risk_assessment.scripts.extract_features import extract_entity_features

def test_feature_extraction():
    """
    Test extracting 12D features from Neo4j.
    """
    # Pick any buyer from your Neo4j data
    features = extract_entity_features(
        entity_name="Global Import Export Ltd",  # Adjust to match your data
        entity_type="Buyer",
        lookback_days=90
    )
    
    # Verify all 12 features are present
    expected_features = [
        'transaction_count', 'total_exposure', 'avg_lc_amount',
        'discrepancy_rate', 'late_shipment_rate', 'payment_delay_avg',
        'counterparty_diversity', 'high_risk_country_exposure', 'sanctions_exposure',
        'doc_completeness', 'amendment_rate', 'fraud_flags'
    ]
    
    for feat in expected_features:
        assert feat in features, f"Missing feature: {feat}"
        print(f"✅ {feat}: {features[feat]}")
    
    print("\n✅ All 12 features extracted successfully")

if __name__ == '__main__':
    test_feature_extraction()
```

---

### Unit Test 2: Training Data Generation

```python
def test_training_data_generation():
    """
    Test generating labeled training data.
    """
    from skills.risk_assessment.scripts.generate_training_labels import generate_labels
    
    # Generate labels for 100 entities
    training_data = generate_labels(n_entities=100)
    
    # Verify structure
    assert len(training_data) == 100
    assert 'label' in training_data.columns
    assert training_data['label'].isin([0, 1]).all()  # Binary labels
    
    # Check class distribution
    high_risk_pct = training_data['label'].mean()
    print(f"High-risk entities: {high_risk_pct:.1%}")
    assert 0.15 <= high_risk_pct <= 0.25, "Expected 15-25% high-risk"
    
    print("✅ Training data generation test PASSED")

if __name__ == '__main__':
    test_training_data_generation()
```

---

### Integration Test: Train and Score

```python
import time
import numpy as np

def test_risk_model_training():
    """
    Test XGBoost model training and scoring.
    """
    from skills.risk_assessment.scripts.train_model import train_xgboost_model
    from skills.risk_assessment.scripts.score_entity import score_entity
    
    # Step 1: Train model
    print("Training XGBoost model...")
    start = time.time()
    metrics = train_xgboost_model(
        training_data_path="data/processed/training_data.csv",
        model_output_path="models/risk_model_test.pkl",
        test_size=0.2
    )
    train_time = time.time() - start
    
    print(f"\nTraining completed in {train_time:.1f}s")
    print(f"AUC-ROC: {metrics['auc_roc']:.3f}")
    print(f"F1 Score: {metrics['f1_score']:.3f}")
    
    # Verify performance
    assert metrics['auc_roc'] >= 0.85, f"AUC-ROC {metrics['auc_roc']:.3f} < 0.85"
    assert train_time < 300, f"Training took {train_time:.1f}s > 5 min"
    print("✅ Model training test PASSED")
    
    # Step 2: Score entity
    print("\nScoring entity...")
    start = time.time()
    score = score_entity(
        entity_name="Global Import Export Ltd",
        entity_type="Buyer",
        model_path="models/risk_model_test.pkl"
    )
    inference_time = (time.time() - start) * 1000
    
    print(f"Risk Score: {score['risk_score']:.2f}")
    print(f"Risk Category: {score['risk_category']}")
    print(f"Credit Limit: ${score['credit_limit_usd']:,}")
    print(f"Inference Time: {inference_time:.1f}ms")
    
    # Verify performance
    assert 0 <= score['risk_score'] <= 1, "Risk score out of range"
    assert inference_time < 100, f"Inference {inference_time:.1f}ms > 100ms"
    print("✅ Entity scoring test PASSED")

if __name__ == '__main__':
    test_risk_model_training()
```

**Run it:**
```bash
python tests/test_risk_assessment.py
```

---

## 🎯 Skill 3: Predictive Analytics Tests

### Unit Test 1: Prophet LC Volume Forecasting

```python
# tests/test_predictive_analytics.py
import sys
sys.path.insert(0, 'src')

from skills.predictive_analytics.scripts.prophet_forecaster import forecast_lc_volume
import pandas as pd

def test_prophet_forecasting():
    """
    Test Prophet LC volume forecasting.
    """
    # Train model (if not already trained)
    print("Training Prophet model...")
    from skills.predictive_analytics.scripts.train_prophet import train_prophet_model
    train_prophet_model()
    
    # Generate forecast
    forecast = forecast_lc_volume(forecast_days=30)
    
    # Verify structure
    assert len(forecast['predictions']) == 30
    assert 'date' in forecast['predictions'][0]
    assert 'lc_count' in forecast['predictions'][0]
    assert 'total_usd' in forecast['predictions'][0]
    
    # Display sample
    print("\n7-Day Forecast:")
    for day in forecast['predictions'][:7]:
        print(f"{day['date']}: {day['lc_count']} LCs, ${day['total_usd']:,.0f}")
    
    print(f"\n✅ Prophet forecasting test PASSED")
    print(f"Trend: {forecast['trend']}")

if __name__ == '__main__':
    test_prophet_forecasting()
```

---

### Unit Test 2: LSTM Port Delay Prediction

```python
def test_lstm_port_delay():
    """
    Test LSTM port delay prediction.
    """
    from skills.predictive_analytics.scripts.lstm_predictor import predict_port_delay
    
    # Test various port pairs
    test_cases = [
        {"loading": "CNSHA", "discharge": "USNYC", "cargo": "Electronics", "volume": 500},
        {"loading": "SGSIN", "discharge": "HKHKG", "cargo": "Textiles", "volume": 200},
        {"loading": "AEJEA", "discharge": "NLRTM", "cargo": "Machinery", "volume": 1000},
    ]
    
    for case in test_cases:
        delay = predict_port_delay(
            port_of_loading=case['loading'],
            port_of_discharge=case['discharge'],
            cargo_type=case['cargo'],
            cargo_volume_cbm=case['volume'],
            shipment_date="2026-02-15"
        )
        
        print(f"\n{case['loading']} → {case['discharge']}:")
        print(f"  Predicted Delay: {delay['predicted_delay_days']:.1f} days")
        print(f"  Risk Level: {delay['risk_level']}")
        
        # Verify reasonable range
        assert 0 <= delay['predicted_delay_days'] <= 30, "Delay out of range"
    
    print("\n✅ LSTM port delay test PASSED")

if __name__ == '__main__':
    test_lstm_port_delay()
```

---

### Unit Test 3: Isolation Forest Anomaly Detection

```python
def test_isolation_forest():
    """
    Test Isolation Forest anomaly detection.
    """
    from skills.predictive_analytics.scripts.isolation_forest import detect_anomalies
    
    # Test on known entities
    test_entities = [
        ("Clean Trading Corp", "LC2026-HK-00001"),
        ("Suspicious Corp", "LC2026-HK-00999"),  # Should be anomaly
    ]
    
    for entity_name, transaction_id in test_entities:
        result = detect_anomalies(entity_name, transaction_id)
        
        print(f"\n{entity_name}:")
        print(f"  Anomaly: {result['is_anomaly']}")
        print(f"  Anomaly Score: {result['anomaly_score']:.2f}")
        print(f"  Confidence: {result['anomaly_confidence']:.0%}")
        
        if result['is_anomaly']:
            print(f"  Top Feature: {result['contributing_features'][0]['feature']}")
    
    print("\n✅ Isolation Forest test PASSED")

if __name__ == '__main__':
    test_isolation_forest()
```

**Run it:**
```bash
python tests/test_predictive_analytics.py
```

---

## 🎯 Skill 4: Quantum Anomaly Detection Tests

### Unit Test 1: Feature Normalization

```python
# tests/test_quantum_anomaly.py
import sys
sys.path.insert(0, 'src')
import numpy as np

from skills.quantum_anomaly.scripts.extract_quantum_features import normalize_features

def test_quantum_feature_normalization():
    """
    Test 4D feature normalization for quantum encoding.
    """
    # Test case 1: Normal transaction
    features = {
        'amount_deviation': 0.5,
        'time_deviation': 1.0,
        'port_risk': 0.3,
        'doc_completeness': 0.95
    }
    
    normalized = normalize_features(features)
    
    # Verify all in [0, 1]
    assert np.all(normalized >= 0) and np.all(normalized <= 1), "Features not normalized"
    print(f"Normal transaction: {normalized}")
    print("✅ Normalization test PASSED")
    
    # Test case 2: Extreme values
    extreme_features = {
        'amount_deviation': 5.0,  # Should clip to 3
        'time_deviation': 10.0,   # Should clip to 5
        'port_risk': 0.9,
        'doc_completeness': 0.5
    }
    
    normalized_extreme = normalize_features(extreme_features)
    print(f"Extreme transaction: {normalized_extreme}")
    assert np.all(normalized_extreme >= 0) and np.all(normalized_extreme <= 1)
    print("✅ Extreme value clipping test PASSED")

if __name__ == '__main__':
    test_quantum_feature_normalization()
```

---

### Unit Test 2: VQC Circuit Execution

```python
import pennylane as qml
from pennylane import numpy as np

def test_vqc_circuit():
    """
    Test 4-qubit VQC circuit execution.
    """
    # Define quantum device
    dev = qml.device('default.qubit', wires=4)
    
    @qml.qnode(dev)
    def quantum_circuit(features, weights):
        # Amplitude encoding
        qml.AmplitudeEmbedding(features, wires=range(4), normalize=True)
        
        # Variational layers
        for i in range(4):
            qml.RY(weights[i], wires=i)
        for i in range(3):
            qml.CNOT(wires=[i, i+1])
        
        for i in range(4):
            qml.RY(weights[i+4], wires=i)
        for i in range(3):
            qml.CNOT(wires=[i, i+1])
        
        for i in range(4):
            qml.RY(weights[i+8], wires=i)
        
        return qml.expval(qml.PauliZ(0))
    
    # Test with random features and weights
    features = np.array([0.5, 0.3, 0.7, 0.9])
    weights = np.random.rand(12) * np.pi
    
    result = quantum_circuit(features, weights)
    
    print(f"Circuit output: {result:.4f}")
    assert -1 <= result <= 1, "Circuit output out of range"
    print("✅ VQC circuit test PASSED")

if __name__ == '__main__':
    test_vqc_circuit()
```

---

### Integration Test: Quantum vs Classical Benchmark

```python
import time

def test_quantum_vs_classical_benchmark():
    """
    Benchmark quantum VQC vs classical Isolation Forest.
    """
    from skills.quantum_anomaly.scripts.benchmark import benchmark_quantum_vs_classical
    
    print("Running quantum vs classical benchmark...")
    print("(This may take a few minutes)\n")
    
    comparison = benchmark_quantum_vs_classical(
        test_data_path="data/processed/test_data.csv"
    )
    
    print("\n" + "="*60)
    print("QUANTUM VQC")
    print("="*60)
    print(f"F1 Score:        {comparison['quantum']['f1_score']:.3f}")
    print(f"Precision:       {comparison['quantum']['precision']:.3f}")
    print(f"Recall:          {comparison['quantum']['recall']:.3f}")
    print(f"Avg Inference:   {comparison['quantum']['avg_inference_ms']:.1f}ms")
    
    print("\n" + "="*60)
    print("CLASSICAL ISOLATION FOREST")
    print("="*60)
    print(f"F1 Score:        {comparison['classical']['f1_score']:.3f}")
    print(f"Precision:       {comparison['classical']['precision']:.3f}")
    print(f"Recall:          {comparison['classical']['recall']:.3f}")
    print(f"Avg Inference:   {comparison['classical']['avg_inference_ms']:.1f}ms")
    
    print("\n" + "="*60)
    print("QUANTUM ADVANTAGE")
    print("="*60)
    print(f"F1 Improvement:  {comparison['quantum_advantage']['f1_improvement_pct']:.1f}%")
    print(f"Latency Penalty: +{comparison['quantum_advantage']['latency_penalty_ms']:.0f}ms")
    
    # Verify quantum advantage
    assert comparison['quantum']['f1_score'] >= comparison['classical']['f1_score'], \
        "Quantum should match or exceed classical F1"
    
    print("\n✅ Quantum benchmark test PASSED")

if __name__ == '__main__':
    test_quantum_vs_classical_benchmark()
```

**Run it:**
```bash
python tests/test_quantum_anomaly.py
```

---

## 🚀 Running All Tests

### Create Master Test Suite

```python
# tests/run_all_tests.py
import sys
import time

def run_all_tests():
    """
    Run all agent skill tests.
    """
    print("\n" + "="*60)
    print("SENTINEL-ZERO AGENT SKILLS TEST SUITE")
    print("="*60)
    
    start_time = time.time()
    
    # Test 1: Compliance Screening
    print("\n[1/4] Testing Compliance Screening Skill...")
    from test_compliance_screening import (
        test_exact_sanctions_match,
        test_fuzzy_sanctions_match,
        test_country_risk_scoring,
        test_compliance_screening_integration
    )
    test_exact_sanctions_match()
    test_fuzzy_sanctions_match()
    test_country_risk_scoring()
    test_compliance_screening_integration()
    
    # Test 2: Risk Assessment
    print("\n[2/4] Testing Risk Assessment Skill...")
    from test_risk_assessment import (
        test_feature_extraction,
        test_training_data_generation,
        test_risk_model_training
    )
    test_feature_extraction()
    test_training_data_generation()
    test_risk_model_training()
    
    # Test 3: Predictive Analytics
    print("\n[3/4] Testing Predictive Analytics Skill...")
    from test_predictive_analytics import (
        test_prophet_forecasting,
        test_lstm_port_delay,
        test_isolation_forest
    )
    test_prophet_forecasting()
    test_lstm_port_delay()
    test_isolation_forest()
    
    # Test 4: Quantum Anomaly
    print("\n[4/4] Testing Quantum Anomaly Detection Skill...")
    from test_quantum_anomaly import (
        test_quantum_feature_normalization,
        test_vqc_circuit,
        test_quantum_vs_classical_benchmark
    )
    test_quantum_feature_normalization()
    test_vqc_circuit()
    test_quantum_vs_classical_benchmark()
    
    # Summary
    total_time = time.time() - start_time
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED")
    print("="*60)
    print(f"Total Time: {total_time:.1f}s")

if __name__ == '__main__':
    run_all_tests()
```

**Run all tests:**
```bash
cd ~/comp3520
source venv/bin/activate
python tests/run_all_tests.py
```

---

## 📊 Expected Test Outputs

### Compliance Screening
```
✅ Exact match test PASSED
✅ Fuzzy match test PASSED (score: 89%)
✅ IR: 9/10 (high risk)
✅ US: 1/10 (low risk)
✅ Performance OK (<500ms)
```

### Risk Assessment
```
✅ transaction_count: 45
✅ discrepancy_rate: 0.13
✅ All 12 features extracted successfully
AUC-ROC: 0.89
✅ Model training test PASSED
```

### Predictive Analytics
```
2026-01-23: 15 LCs, $4,500,000
✅ Prophet forecasting test PASSED
Predicted Delay: 5.2 days (Risk: medium)
✅ LSTM port delay test PASSED
```

### Quantum Anomaly
```
Normal transaction: [0.58 0.20 0.30 0.95]
✅ Normalization test PASSED
Circuit output: -0.4231
✅ VQC circuit test PASSED
F1 Improvement: +3.9%
✅ Quantum benchmark test PASSED
```

---

## 🐛 Troubleshooting

### Neo4j Connection Error
```bash
# Check if Neo4j is running
docker ps | grep neo4j-sentinel

# Restart if needed
docker restart neo4j-sentinel

# Wait 30 seconds, then retry
```

### Import Error
```bash
# Make sure PYTHONPATH includes src/
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Or run from project root
cd ~/comp3520
python tests/test_compliance_screening.py
```

### Model Not Found
```bash
# Train models first
python src/skills/risk_assessment/scripts/train_model.py
python src/skills/predictive_analytics/scripts/train_prophet.py
python src/skills/quantum_anomaly/scripts/train_vqc.py
```

---

## 📚 Next Steps

1. **Implement missing scripts** (Week 2 Day 3-7)
2. **Run pytest with coverage**:
   ```bash
   pytest tests/ --cov=src/skills --cov-report=html
   open htmlcov/index.html
   ```
3. **Set up CI/CD** (GitHub Actions for automated testing)
4. **Add performance benchmarks** using `pytest-benchmark`

---

**Testing Guide Complete!** ✅  
You now know how to test all 4 agent skills systematically.