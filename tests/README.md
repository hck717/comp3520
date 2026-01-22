# Agent Skills Testing

This folder contains tests for all 4 agent skills in Sentinel-Zero.

---

## 🚀 Quick Start (5 minutes)

### Step 1: Setup

```bash
cd ~/comp3520
source venv/bin/activate

# Install test dependencies
pip install pytest pytest-cov
```

### Step 2: Verify Prerequisites

```bash
# Check Neo4j is running
docker ps | grep neo4j-sentinel

# Check data is loaded
python -c "from neo4j import GraphDatabase; driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password')); result = driver.session().run('MATCH (n) RETURN count(n)').single()[0]; print(f'Nodes: {result}'); driver.close()"
```

### Step 3: Run Quick Tests

```bash
# Test individual skills
python tests/quick_test_compliance.py     # ~5 seconds
python tests/quick_test_risk.py           # ~10 seconds
python tests/quick_test_predictive.py     # ~15 seconds
python tests/quick_test_quantum.py        # ~30 seconds

# Or run all at once
bash tests/run_quick_tests.sh             # ~1 minute
```

---

## 📝 Test Files Overview

| File | Tests | Duration |
|------|-------|----------|
| `quick_test_compliance.py` | Exact match, fuzzy match, country risk, batch | ~5s |
| `quick_test_risk.py` | Feature extraction, training labels, XGBoost | ~10s |
| `quick_test_predictive.py` | Isolation Forest, Prophet, anomaly detection | ~15s |
| `quick_test_quantum.py` | Feature normalization, VQC circuit, training | ~30s |

---

## 🧰 What Each Test Does

### 1. Compliance Screening Tests

```bash
python tests/quick_test_compliance.py
```

**Tests**:
- ✅ Exact sanctions list matching
- ✅ Fuzzy matching with typos
- ✅ Country risk scoring (Iran=9/10, US=1/10)
- ✅ Batch screening (10 entities)
- ✅ Performance: <500ms per entity

**Expected Output**:
```
[Test 1] Screening clean entity...
  Recommendation: APPROVE
  Latency: 87ms
  ✅ PASSED

[Test 2] High-risk country...
  Country Risk: high (9/10)
  ✅ PASSED

[Test 3] Batch screening (10 entities)...
  Throughput: 42.3 entities/sec
  ✅ PASSED
```

---

### 2. Risk Assessment Tests

```bash
python tests/quick_test_risk.py
```

**Tests**:
- ✅ Extract 12D features from Neo4j
- ✅ Generate training labels (50 samples)
- ✅ Train XGBoost model (light version)
- ✅ Performance: <500ms feature extraction

**Expected Output**:
```
[Test 1] Extracting 12D features...
  Features Extracted: 12/12
  Extraction Time: 234ms
  ✅ PASSED

[Test 2] Training labels...
  High-risk samples: 12
  ✅ PASSED

[Test 3] Training XGBoost...
  AUC-ROC: 0.847
  ✅ PASSED
```

---

### 3. Predictive Analytics Tests

```bash
python tests/quick_test_predictive.py
```

**Tests**:
- ✅ Train Isolation Forest (200 samples)
- ✅ Anomaly detection inference
- ✅ Prophet LC volume forecasting (synthetic data)

**Expected Output**:
```
[Test 1] Training Isolation Forest...
  F1 Score: 0.763
  ✅ PASSED

[Test 2] Anomaly detection...
  Anomaly Detected: True
  Confidence: 82%
  ✅ PASSED

[Test 3] Prophet forecasting...
  Forecast Generated: 7 days
  ✅ PASSED
```

---

### 4. Quantum Anomaly Tests

```bash
python tests/quick_test_quantum.py
```

**Tests**:
- ✅ 4D feature normalization
- ✅ 4-qubit VQC circuit execution
- ✅ Light VQC training (10 epochs)
- ✅ Quantum anomaly detection

**Expected Output**:
```
[Test 1] Feature normalization...
  Normalized: [0.58 0.20 0.30 0.95]
  ✅ PASSED

[Test 2] VQC circuit...
  Circuit Output: -0.4231
  Inference Time: 145ms
  ✅ PASSED

[Test 3] Training VQC...
  Training Time: 28.3s
  ✅ PASSED

[Test 4] Quantum inference...
  Quantum Score: -0.67
  Is Anomaly: True
  ✅ PASSED
```

---

## 🔧 Full Test Suite (Advanced)

For comprehensive testing with pytest:

```bash
# Run all tests with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src/skills --cov-report=html
open htmlcov/index.html

# Run specific skill tests
pytest tests/quick_test_compliance.py -v

# Run with benchmarking
pytest tests/ --benchmark-only
```

---

## 🐛 Troubleshooting

### Error: "Module not found"

```bash
# Make sure you're in project root
cd ~/comp3520
source venv/bin/activate

# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

### Error: "Neo4j connection failed"

```bash
# Check if Neo4j is running
docker ps | grep neo4j-sentinel

# If not running, start it
docker start neo4j-sentinel

# Wait 30 seconds for Neo4j to start
sleep 30
```

### Error: "No data in Neo4j"

```bash
# Ingest data first
python src/ingest_trade_finance.py
```

### Error: "Model file not found"

```bash
# Quick tests create light models automatically
# For production models, train them:
python src/skills/risk_assessment/scripts/train_model.py
python src/skills/predictive_analytics/scripts/train_prophet.py
python src/skills/quantum_anomaly/scripts/train_vqc.py
```

---

## 📋 Testing Checklist

Before running tests:
- [ ] Virtual environment activated
- [ ] Neo4j container running
- [ ] Data ingested (1000+ nodes)
- [ ] pytest installed

---

## 📚 Documentation

- **Detailed Testing Guide**: [`docs/TESTING_GUIDE.md`](../docs/TESTING_GUIDE.md)
- **Skill Documentation**:
  - [Compliance Screening](../src/skills/compliance_screening/SKILL.md)
  - [Risk Assessment](../src/skills/risk_assessment/SKILL.md)
  - [Predictive Analytics](../src/skills/predictive_analytics/SKILL.md)
  - [Quantum Anomaly](../src/skills/quantum_anomaly/SKILL.md)

---

## 🎯 Next Steps

1. **Run quick tests** to verify skills work
2. **Implement missing scripts** (Week 2 completion)
3. **Run full test suite** with pytest
4. **Check coverage** (target: >80%)
5. **Set up CI/CD** (GitHub Actions)

---

**Happy Testing!** 🚀
