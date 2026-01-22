#!/usr/bin/env python3
"""
Quick test for Risk Assessment Skill.

Run: python tests/quick_test_risk.py
"""

import sys
import time
import pandas as pd
sys.path.insert(0, 'src')

from skills.risk_assessment.scripts.extract_features import extract_entity_features

def main():
    print("\n" + "="*60)
    print("QUICK TEST: Risk Assessment Skill")
    print("="*60)
    
    # Test 1: Feature extraction
    print("\n[Test 1] Extracting 12D features from Neo4j...")
    
    # Get a buyer from Neo4j
    from neo4j import GraphDatabase
    driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password'))
    
    with driver.session() as session:
        result = session.run("MATCH (b:Buyer) RETURN b.name AS name LIMIT 1")
        buyer_name = result.single()['name']
    
    driver.close()
    
    print(f"  Testing with buyer: {buyer_name}")
    
    start = time.time()
    features = extract_entity_features(
        entity_name=buyer_name,
        entity_type="Buyer",
        lookback_days=90
    )
    extraction_time = (time.time() - start) * 1000
    
    # Verify all 12 features
    expected_features = [
        'transaction_count', 'total_exposure', 'avg_lc_amount',
        'discrepancy_rate', 'late_shipment_rate', 'payment_delay_avg',
        'counterparty_diversity', 'high_risk_country_exposure', 'sanctions_exposure',
        'doc_completeness', 'amendment_rate', 'fraud_flags'
    ]
    
    for feat in expected_features:
        assert feat in features, f"Missing feature: {feat}"
    
    print(f"  Features Extracted: 12/12")
    print(f"  Extraction Time: {extraction_time:.1f}ms")
    print(f"  Sample features:")
    print(f"    - transaction_count: {features['transaction_count']}")
    print(f"    - discrepancy_rate: {features['discrepancy_rate']:.2f}")
    print(f"    - high_risk_country_exposure: {features['high_risk_country_exposure']:.2f}")
    
    assert extraction_time < 500, f"Extraction {extraction_time:.1f}ms > 500ms"
    print("  ✅ PASSED")
    
    # Test 2: Training data generation
    print("\n[Test 2] Generating training labels...")
    from skills.risk_assessment.scripts.generate_training_labels import generate_labels
    
    training_data = generate_labels(n_entities=50)
    
    print(f"  Training samples: {len(training_data)}")
    print(f"  High-risk samples: {training_data['label'].sum()}")
    print(f"  Clean samples: {(1 - training_data['label']).sum()}")
    
    assert len(training_data) == 50
    assert 'label' in training_data.columns
    print("  ✅ PASSED")
    
    # Test 3: Model training (light version)
    print("\n[Test 3] Training XGBoost model (light)...")
    print("  (Using small dataset for quick test)")
    
    from skills.risk_assessment.scripts.train_model import train_xgboost_model
    
    # Save training data
    training_data.to_csv('data/processed/training_data_test.csv', index=False)
    
    start = time.time()
    metrics = train_xgboost_model(
        training_data_path='data/processed/training_data_test.csv',
        model_output_path='models/risk_model_test.pkl',
        test_size=0.3,
        n_estimators=50  # Reduced for quick test
    )
    train_time = time.time() - start
    
    print(f"  Training Time: {train_time:.1f}s")
    print(f"  AUC-ROC: {metrics['auc_roc']:.3f}")
    print(f"  Precision: {metrics['precision']:.3f}")
    print(f"  Recall: {metrics['recall']:.3f}")
    
    assert metrics['auc_roc'] >= 0.70, "Model AUC too low for light test"
    print("  ✅ PASSED")
    
    print("\n" + "="*60)
    print("✅ ALL RISK ASSESSMENT TESTS PASSED")
    print("="*60)
    print("\n💡 For full model training (1000 samples), run:")
    print("   python src/skills/risk_assessment/scripts/train_model.py")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
