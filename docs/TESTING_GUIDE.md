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
pip install pytest pytest-cov
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

### Quick Test (All 3 Tests)

```bash
# Run the quick test suite (recommended)
python tests/quick_test_compliance.py
```

**Expected Output:**
```
============================================================
QUICK TEST: Compliance Screening Skill
============================================================

[Test 1] Screening clean entity...
  Entity: HSBC Hong Kong
  Sanctions Match: False
  Country Risk: low (2/10)
  Recommendation: APPROVE
  Latency: 87.3ms
  ✅ PASSED

[Test 2] Screening high-risk country entity...
  Entity: Tehran Trading Corp
  Country Risk: high (9/10)
  Recommendation: REVIEW
  Latency: 124.5ms
  ✅ PASSED

[Test 3] Batch screening (10 entities)...
  Entities Screened: 10
  Total Time: 0.24s
  Throughput: 42.3 entities/sec
  ✅ PASSED

============================================================
✅ ALL COMPLIANCE SCREENING TESTS PASSED
============================================================
```

---

### Manual Testing (Individual Functions)

If you want to test individual functions:

#### Test 1: Exact Match

```python
# Create a test file: test_compliance_manual.py
import sys
sys.path.insert(0, 'src')

from skills.compliance_screening.scripts.screen_entity import screen_entity

# Test exact match
result = screen_entity(
    entity_name="HSBC Hong Kong",
    entity_country="HK",
    entity_type="Bank"
)

print(f"Sanctions Match: {result['sanctions_match']}")
print(f"Country Risk: {result['country_risk']} ({result['country_risk_score']}/10)")
print(f"Recommendation: {result['recommendation']}")
```

**Run it:**
```bash
python test_compliance_manual.py
```

---

#### Test 2: Country Risk Scoring

```python
import sys
sys.path.insert(0, 'src')

from skills.compliance_screening.scripts.country_risk import get_country_risk

# Test various countries
countries = ['IR', 'KP', 'SY', 'US', 'HK', 'SG']

for country in countries:
    risk = get_country_risk(country)
    print(f"{country}: {risk['risk_score']}/10 ({risk['risk_level']})")
```

---

#### Test 3: Batch Screening

```python
import sys
sys.path.insert(0, 'src')

from skills.compliance_screening.scripts.batch_screen import batch_screen

# Test batch screening
entities = [
    {"name": "Company A", "country": "HK", "type": "Buyer"},
    {"name": "Company B", "country": "IR", "type": "Seller"},
    {"name": "Company C", "country": "US", "type": "Buyer"},
]

results = batch_screen(entities, show_progress=True)

for result in results:
    print(f"\n{result['entity_name']}:")
    print(f"  Recommendation: {result['recommendation']}")
    print(f"  Country Risk: {result['country_risk_score']}/10")
```

---

## 🎯 Skill 2: Risk Assessment Tests

**Status**: ⚠️ Scripts not implemented yet (Week 2 Day 3-4)

The SKILL.md documentation is complete, but the Python scripts need to be implemented:

```bash
# These scripts need to be created:
src/skills/risk_assessment/scripts/
├── extract_features.py       # Extract 12D features from Neo4j
├── generate_training_labels.py  # Create labeled dataset
├── train_model.py            # Train XGBoost
└── score_entity.py           # Inference
```

**To test** (once implemented):
```bash
python tests/quick_test_risk.py
```

---

## 🎯 Skill 3: Predictive Analytics Tests

**Status**: ⚠️ Scripts not implemented yet (Week 2 Day 5-6)

**To test** (once implemented):
```bash
python tests/quick_test_predictive.py
```

---

## 🎯 Skill 4: Quantum Anomaly Detection Tests

**Status**: ⚠️ Scripts not implemented yet (Week 2 Day 7)

**To test** (once implemented):
```bash
python tests/quick_test_quantum.py
```

---

## 🚀 Running All Tests (Once Implemented)

### Option 1: Using Bash Script

```bash
bash tests/run_quick_tests.sh
```

### Option 2: Manually Run Each Test

```bash
# Currently working:
python tests/quick_test_compliance.py   # ✅ WORKS

# Not yet implemented:
python tests/quick_test_risk.py         # ⏳ Needs scripts
python tests/quick_test_predictive.py   # ⏳ Needs scripts
python tests/quick_test_quantum.py      # ⏳ Needs scripts
```

---

## 📊 Current Implementation Status

| Skill | Scripts Status | Tests Status | Can Test? |
|-------|---------------|--------------|----------|
| **Compliance Screening** | ✅ Complete | ✅ Passing | ✅ YES |
| **Risk Assessment** | ⏳ Design only | ⏳ Pending | ❌ Not yet |
| **Predictive Analytics** | ⏳ Design only | ⏳ Pending | ❌ Not yet |
| **Quantum Anomaly** | ⏳ Design only | ⏳ Pending | ❌ Not yet |

---

## 🔧 Testing Custom Entities

Create your own test script to try different entities:

```python
# create_custom_test.py
import sys
sys.path.insert(0, 'src')
from skills.compliance_screening.scripts.screen_entity import screen_entity

# Test your own entities
test_cases = [
    ("Apple Inc", "US", "Buyer"),
    ("Moscow Trading Co", "RU", "Seller"),
    ("Standard Chartered", "HK", "Bank"),
    ("Tehran Oil Corp", "IR", "Seller"),
    ("Samsung Electronics", "KR", "Buyer"),
]

print("\n" + "="*60)
print("CUSTOM ENTITY SCREENING TEST")
print("="*60)

for name, country, entity_type in test_cases:
    result = screen_entity(name, country, entity_type)
    print(f"\n{name} ({country}):")
    print(f"  Sanctions Match: {result['sanctions_match']}")
    print(f"  Country Risk: {result['country_risk_score']}/10")
    print(f"  Recommendation: {result['recommendation']}")

print("\n" + "="*60)
```

**Run it:**
```bash
python create_custom_test.py
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

### Error: "cannot import name 'batch_screen_entities'"

**Fix**: The function is named `batch_screen`, not `batch_screen_entities`.

```python
# Correct:
from skills.compliance_screening.scripts.batch_screen import batch_screen

# Incorrect:
from skills.compliance_screening.scripts.batch_screen import batch_screen_entities
```

---

## 📋 Testing Checklist

Before running tests:
- [ ] Virtual environment activated (`source venv/bin/activate`)
- [ ] Neo4j container running (`docker ps | grep neo4j-sentinel`)
- [ ] Data ingested (4000+ nodes in Neo4j)
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] In project root directory (`cd ~/comp3520`)

---

## 📚 Documentation

- **Tests README**: [`tests/README.md`](../tests/README.md)
- **Week 2 Summary**: [`docs/WEEK2_SUMMARY.md`](WEEK2_SUMMARY.md)
- **Skill Documentation**:
  - [Compliance Screening SKILL.md](../src/skills/compliance_screening/SKILL.md)
  - [Risk Assessment SKILL.md](../src/skills/risk_assessment/SKILL.md)
  - [Predictive Analytics SKILL.md](../src/skills/predictive_analytics/SKILL.md)
  - [Quantum Anomaly SKILL.md](../src/skills/quantum_anomaly/SKILL.md)

---

## 🎯 Next Steps

### Immediate (Now)
1. ✅ Test compliance screening skill
2. ✅ Verify it works with your Neo4j data
3. ✅ Try custom entities

### Short-Term (This Week)
1. ⏳ Implement risk assessment scripts
2. ⏳ Implement predictive analytics scripts
3. ⏳ Implement quantum anomaly scripts
4. ⏳ Test all 4 skills end-to-end

### Long-Term (Week 3+)
- Set up GitHub Actions for CI/CD
- Add property-based testing (Hypothesis)
- Implement stress tests (1000+ entities/sec)
- Add integration tests with LangGraph agent

---

## 🎓 What You've Learned

By following this guide, you now know how to:
1. ✅ **Test individual functions** with unit tests
2. ✅ **Test complete workflows** with integration tests
3. ✅ **Benchmark performance** (latency, throughput)
4. ✅ **Debug import errors** and fix function names
5. ✅ **Verify Neo4j integration** works correctly
6. ✅ **Create custom test cases** for your use cases

---

**Testing Guide Updated**: January 22, 2026  
**Status**: Compliance screening fully tested ✅  
**Next**: Implement Week 2 Day 3-7 scripts
