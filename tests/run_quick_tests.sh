#!/bin/bash
# Quick test runner for all agent skills

set -e  # Exit on error

echo "============================================================"
echo "  SENTINEL-ZERO QUICK TEST SUITE"
echo "============================================================"

echo ""
echo "Prerequisites:"
echo "  ✓ Virtual environment activated"
echo "  ✓ Neo4j running (docker ps | grep neo4j-sentinel)"
echo "  ✓ Data ingested"
echo ""

# Activate virtual environment if not already
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Test 1: Compliance Screening
echo ""
echo "[1/4] Testing Compliance Screening..."
python tests/quick_test_compliance.py

# Test 2: Risk Assessment
echo ""
echo "[2/4] Testing Risk Assessment..."
python tests/quick_test_risk.py

# Test 3: Predictive Analytics
echo ""
echo "[3/4] Testing Predictive Analytics..."
python tests/quick_test_predictive.py

# Test 4: Quantum Anomaly
echo ""
echo "[4/4] Testing Quantum Anomaly..."
python tests/quick_test_quantum.py

echo ""
echo "============================================================"
echo "  ✅ ALL QUICK TESTS PASSED!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "  - Run full test suite: pytest tests/"
echo "  - Check coverage: pytest --cov=src/skills"
echo "  - Train full models for production"
echo ""
