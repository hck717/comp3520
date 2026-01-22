# Development Guide - COMP3520

## Current Status: ✅ ALL TESTS PASSING (4/4)

As of January 22, 2026, all core functionality is working:
- ✅ Balanced data generation
- ✅ Risk Assessment (XGBoost) - Perfect metrics
- ✅ Quantum VQC training - 87.2% F1-Score
- ✅ Quantum vs Classical benchmark

## Testing Workflow

### Primary Test Suite
Use `test_improvements.py` for all testing:

```bash
cd ~/comp3520
source venv/bin/activate
python test_improvements.py
```

This replaces all previous testing scripts.

## No Longer Used (Deprecated)

These files/folders are **no longer actively maintained**:

### Deprecated Files
- ❌ `TESTING_FIXES.md` - Replaced by this guide
- ❌ `KAGGLE_SETUP.md` - Integrated into main README
- ❌ `setup_testing.sh` - Use virtual environment activation instead
- ❌ `tests/` folder - Replaced by `test_improvements.py`
  - `tests/quick_test_*.py` - Individual component tests
  - `tests/run_quick_tests.sh` - Shell script runner
  - `tests/verify_setup.py` - Setup verification

### Why Consolidated?
1. **Single source of truth:** `test_improvements.py` tests all components
2. **Better error handling:** Graceful degradation when Neo4j unavailable
3. **Comprehensive output:** Clear pass/fail status with metrics
4. **Maintainability:** One file to update vs multiple scripts

## Development Commands

### Quick Validation
```bash
# Full test suite (recommended)
python test_improvements.py

# Test specific skill manually
python -m src.skills.risk_assessment.scripts.train_model
python -m src.skills.quantum_anomaly.scripts.train_vqc
```

### Data Generation
```bash
# Generate new balanced dataset
python -m src.data_generation.generate_balanced_data \
  --samples 1000 \
  --anomaly-ratio 0.30
```

### Neo4j Management
```bash
# Start Neo4j
docker run -d --name neo4j-sentinel -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password123 neo4j:5.26.0

# Stop Neo4j
docker stop neo4j-sentinel

# Remove Neo4j (clean slate)
docker rm -f neo4j-sentinel
```

## Code Organization Best Practices

### Adding New Skills
1. Create skill folder: `src/skills/new_skill/`
2. Add training script: `scripts/train.py`
3. Add inference script: `scripts/predict.py`
4. Update `test_improvements.py` with new test function
5. Document in README.md

### Feature Naming Convention
All scripts support flexible column naming:
- Use `label` OR `is_anomaly` for target variable
- Script auto-detects which column exists
- Excludes `transaction_id`, `entity_name` automatically

### Testing Philosophy
- **Integration over Unit:** Test end-to-end workflows
- **Graceful Degradation:** Skip Neo4j tests if unavailable
- **Clear Output:** Log all metrics and decisions
- **Fast Feedback:** Run full suite in < 10 minutes

## Known Issues & Solutions

### Issue: NumPy Version Warning (PennyLane)
**Warning:** `PennyLane v0.44 has dropped support for NumPy < 2.0.0`

**Solution:**
```bash
pip install numpy --upgrade
```

**Status:** Non-blocking warning, system works with NumPy 1.26.4

### Issue: Neo4j Authentication Failure
**Error:** `Neo.ClientError.Security.Unauthorized`

**Solution:**
```bash
# Ensure Neo4j is running
docker ps | grep neo4j

# Restart with correct auth
docker run -d --name neo4j-sentinel -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password123 neo4j:5.26.0
```

**Status:** Test suite gracefully skips entity scoring if Neo4j unavailable

### Issue: Import Errors
**Error:** `ModuleNotFoundError: No module named 'src'`

**Solution:**
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

**Permanent Fix:** Add to `~/.bashrc` or `~/.zshrc`:
```bash
export PYTHONPATH="${PYTHONPATH}:$HOME/comp3520/src"
```

## Performance Benchmarks

### Training Times (M1 MacBook Air)
- **Data Generation:** ~1 second (1000 samples)
- **XGBoost Training:** ~2 seconds (800 train samples)
- **VQC Training:** ~264 seconds (30 epochs, 4 qubits)
- **Full Test Suite:** ~540 seconds (~9 minutes)

### Model Sizes
- `risk_model.pkl`: ~50 KB
- `quantum_vqc_balanced.pkl`: ~10 KB

## Next Steps for Development

### Phase 1: Core Improvements (Immediate)
- [x] Balanced data generation
- [x] Fix column name handling
- [x] Quantum VQC training
- [x] Benchmark quantum vs classical
- [ ] Graph RAG implementation
- [ ] Agent orchestration testing

### Phase 2: Production Features
- [ ] REST API for model serving
- [ ] Streamlit dashboard for visualization
- [ ] Real-time anomaly detection pipeline
- [ ] Model versioning and A/B testing

### Phase 3: Advanced ML
- [ ] Graph Neural Network integration
- [ ] Multi-model ensemble
- [ ] Active learning with human feedback
- [ ] Explainability (SHAP, LIME)

## Contributing

### Pull Request Guidelines
1. Run full test suite: `python test_improvements.py`
2. Ensure all 4/4 tests pass
3. Update README.md if adding new features
4. Document any new dependencies in `requirements.txt`

### Commit Message Format
```
type: Short description (50 chars)

- Detailed change 1
- Detailed change 2

Resolves: #issue_number
```

**Types:** `feat`, `fix`, `docs`, `test`, `refactor`, `perf`

## Useful Links

- **PennyLane Docs:** https://docs.pennylane.ai
- **Neo4j Cypher Manual:** https://neo4j.com/docs/cypher-manual/
- **XGBoost Docs:** https://xgboost.readthedocs.io
- **LangChain Docs:** https://python.langchain.com

## Contact

Brian Ho - [@hck717](https://github.com/hck717)
