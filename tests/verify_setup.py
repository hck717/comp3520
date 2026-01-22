#!/usr/bin/env python3
"""Verify testing prerequisites before running skill tests."""
import sys
import os
from pathlib import Path

def main():
    checks = []
    
    # 1. Check virtual environment
    in_venv = sys.prefix != sys.base_prefix
    checks.append(("Virtual environment", in_venv))
    
    # 2. Check PYTHONPATH
    pythonpath_ok = 'src' in sys.path or os.getcwd() in sys.path
    checks.append(("PYTHONPATH configured", pythonpath_ok))
    
    # 3. Check Neo4j connection and data
    neo4j_ok = False
    node_count = 0
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password'))
        with driver.session() as session:
            result = session.run('MATCH (n) RETURN count(n) as count')
            node_count = result.single()['count']
        driver.close()
        neo4j_ok = node_count > 1000
        checks.append((f"Neo4j running ({node_count:,} nodes)", neo4j_ok))
    except Exception as e:
        checks.append(("Neo4j connection", False))
    
    # 4. Check required data files
    data_files = [
        "data/processed/transactions.csv",
        "data/processed/sanctions_all.csv"
    ]
    for file_path in data_files:
        exists = Path(file_path).exists()
        checks.append((f"{file_path}", exists))
    
    # 5. Check trained models (optional - tests can create light versions)
    models = [
        ("models/risk_model.pkl", "Optional - test creates light version"),
        ("models/prophet_lc_volume.pkl", "Optional - test creates light version"),
        ("models/isolation_forest.pkl", "Optional - test creates light version"),
        ("models/quantum_vqc.pkl", "Optional - test creates light version")
    ]
    
    print("\n" + "="*60)
    print("SENTINEL-ZERO TESTING SETUP VERIFICATION")
    print("="*60)
    
    # Print critical checks
    print("\n📋 Critical Prerequisites:")
    all_critical_ok = True
    for name, status in checks:
        icon = "✅" if status else "❌"
        print(f"  {icon} {name}")
        if not status:
            all_critical_ok = False
    
    # Print model checks
    print("\n📦 Trained Models (Optional):")
    for model_path, note in models:
        exists = Path(model_path).exists()
        icon = "✅" if exists else "⚪"
        print(f"  {icon} {model_path}")
        if not exists:
            print(f"      → {note}")
    
    # Print recommendations
    print("\n" + "="*60)
    if all_critical_ok:
        print("✅ ALL CRITICAL PREREQUISITES MET")
        print("\nYou can now run the tests:")
        print("  python tests/quick_test_compliance.py")
        print("  python tests/quick_test_risk.py")
        print("  python tests/quick_test_predictive.py")
        print("  python tests/quick_test_quantum.py")
        print("\nOr run all tests:")
        print("  bash tests/run_quick_tests.sh")
    else:
        print("❌ MISSING PREREQUISITES")
        print("\n🔧 Fix the issues above:")
        
        if not in_venv:
            print("\n1. Activate virtual environment:")
            print("   source venv/bin/activate")
        
        if not pythonpath_ok:
            print("\n2. Set PYTHONPATH:")
            print("   export PYTHONPATH=\"${PYTHONPATH}:$(pwd):$(pwd)/src\"")
        
        if not neo4j_ok:
            print("\n3. Start Neo4j and ingest data:")
            print("   docker start neo4j-sentinel")
            print("   sleep 30")
            if node_count == 0:
                print("   python src/ingest_trade_finance.py")
        
        for file_path in data_files:
            if not Path(file_path).exists():
                print(f"\n4. Generate {file_path}:")
                if 'sanctions' in file_path:
                    print("   python src/data_generation/generate_sanctions_list.py")
                elif 'transactions' in file_path:
                    print("   python src/data_generation/enrich_transactions.py")
    
    print("="*60 + "\n")
    return 0 if all_critical_ok else 1

if __name__ == '__main__':
    sys.exit(main())
