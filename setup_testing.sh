#!/bin/bash
# Sentinel-Zero Testing Setup Script
# Run this script to prepare your environment for testing all 4 agent skills

set -e  # Exit on error

echo "============================================================"
echo "  SENTINEL-ZERO TESTING SETUP"
echo "============================================================"
echo ""

# 1. Check if in project directory
if [ ! -f "README.md" ] || [ ! -d "src" ]; then
    echo "❌ Error: Please run this script from the project root (~/comp3520)"
    exit 1
fi

echo "✅ Step 1: In project root directory"
echo ""

# 2. Check virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment not activated"
    echo "   Activating venv..."
    if [ -d "venv" ]; then
        source venv/bin/activate
        echo "✅ Virtual environment activated"
    else
        echo "❌ No venv found. Creating one..."
        python3 -m venv venv
        source venv/bin/activate
        echo "✅ Virtual environment created and activated"
    fi
else
    echo "✅ Step 2: Virtual environment active"
fi
echo ""

# 3. Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd):$(pwd)/src"
echo "✅ Step 3: PYTHONPATH configured"
echo "   PYTHONPATH=$PYTHONPATH"
echo ""

# 4. Install dependencies
echo "Step 4: Checking dependencies..."
pip install -q -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# 5. Check Neo4j
echo "Step 5: Checking Neo4j..."
if docker ps | grep -q neo4j-sentinel; then
    echo "✅ Neo4j is running"
else
    echo "⚠️  Neo4j is not running"
    echo "   Starting Neo4j..."
    docker start neo4j-sentinel 2>/dev/null || {
        echo "   Creating new Neo4j container..."
        docker run -d --name neo4j-sentinel \
          -p 7474:7474 -p 7687:7687 \
          -e NEO4J_AUTH=neo4j/password \
          -e NEO4J_PLUGINS='["apoc", "graph-data-science"]' \
          neo4j:5.18.0
    }
    echo "   Waiting 30 seconds for Neo4j to start..."
    sleep 30
    echo "✅ Neo4j started"
fi
echo ""

# 6. Check data in Neo4j
echo "Step 6: Checking Neo4j data..."
NODE_COUNT=$(python3 -c "from neo4j import GraphDatabase; driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password')); result = driver.session().run('MATCH (n) RETURN count(n)').single()[0]; driver.close(); print(result)" 2>/dev/null || echo "0")

if [ "$NODE_COUNT" -gt 1000 ]; then
    echo "✅ Neo4j has data ($NODE_COUNT nodes)"
else
    echo "⚠️  Neo4j has insufficient data ($NODE_COUNT nodes)"
    echo "   Generating data and ingesting..."
    
    # Generate sanctions list
    if [ ! -f "data/processed/sanctions_all.csv" ]; then
        echo "   - Generating sanctions list..."
        python src/data_generation/generate_sanctions_list.py
    fi
    
    # Generate transactions
    if [ ! -f "data/processed/transactions.csv" ]; then
        echo "   - Generating transaction data..."
        python src/data_generation/enrich_transactions.py
    fi
    
    # Ingest into Neo4j
    echo "   - Ingesting into Neo4j..."
    python src/ingest_trade_finance.py
    
    echo "✅ Data ingested successfully"
fi
echo ""

# 7. Create models directory
if [ ! -d "models" ]; then
    mkdir models
    echo "✅ Step 7: Created models/ directory"
else
    echo "✅ Step 7: models/ directory exists"
fi
echo ""

echo "============================================================"
echo "✅ SETUP COMPLETE!"
echo "============================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Verify setup:"
echo "   python tests/verify_setup.py"
echo ""
echo "2. Run individual skill tests:"
echo "   python tests/quick_test_compliance.py"
echo "   python tests/quick_test_risk.py"
echo "   python tests/quick_test_predictive.py"
echo "   python tests/quick_test_quantum.py"
echo ""
echo "3. Or run all tests:"
echo "   bash tests/run_quick_tests.sh"
echo ""
echo "Note: Tests will create light ML models automatically if needed."
echo "For production models, run the training scripts manually."
echo ""
