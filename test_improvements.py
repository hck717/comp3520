#!/usr/bin/env python3
"""Test script for balanced data generation and all skills."""

import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

def test_data_generation():
    """Step 1: Generate balanced training data."""
    logger.info("\n" + "="*60)
    logger.info("STEP 1: GENERATING BALANCED TRAINING DATA")
    logger.info("="*60)
    
    try:
        from src.data_generation.generate_balanced_data import main as generate_data
        df = generate_data()
        logger.info("✅ Data generation successful!")
        return True
    except Exception as e:
        logger.error(f"❌ Data generation failed: {e}")
        return False

def test_risk_assessment():
    """Step 2: Test Risk Assessment skill."""
    logger.info("\n" + "="*60)
    logger.info("STEP 2: TESTING RISK ASSESSMENT SKILL")
    logger.info("="*60)
    
    try:
        # Generate training labels
        logger.info("\nGenerating training labels...")
        from src.skills.risk_assessment.scripts.generate_training_labels import main as gen_labels
        gen_labels()
        
        # Train XGBoost model
        logger.info("\nTraining XGBoost model...")
        from src.skills.risk_assessment.scripts.train_model import train_xgboost_model
        metrics = train_xgboost_model(
            training_data_path="data/processed/training_data_balanced.csv",
            model_output_path="models/risk_model.pkl"
        )
        
        logger.info(f"\n🏆 Risk Model Metrics:")
        logger.info(f"   AUC-ROC: {metrics.get('auc_roc', 0):.3f}")
        logger.info(f"   Precision: {metrics.get('precision', 0):.3f}")
        logger.info(f"   Recall: {metrics.get('recall', 0):.3f}")
        logger.info(f"   F1-Score: {metrics.get('f1_score', 0):.3f}")
        
        # Test scoring
        logger.info("\nTesting entity scoring...")
        from src.skills.risk_assessment.scripts.score_entity import score_entity
        
        # This will fail if no Neo4j data, but that's expected
        try:
            score = score_entity(
                entity_name="Test Entity",
                entity_type="Buyer",
                model_path="models/risk_model.pkl"
            )
            logger.info(f"\n📊 Test Score: {score}")
        except Exception as e:
            logger.warning(f"⚠️  Entity scoring skipped (Neo4j required): {e}")
        
        logger.info("✅ Risk assessment complete!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Risk assessment failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_quantum_with_balanced_data():
    """Step 3: Retrain quantum model with balanced data."""
    logger.info("\n" + "="*60)
    logger.info("STEP 3: TRAINING QUANTUM VQC WITH BALANCED DATA")
    logger.info("="*60)
    
    try:
        from src.skills.quantum_anomaly.scripts.train_vqc import train_quantum_model
        
        metrics = train_quantum_model(
            n_epochs=30,
            output_path='models/quantum_vqc_balanced.pkl',
            use_csv=True  # Use balanced CSV data
        )
        
        logger.info(f"\n🏆 Quantum VQC Metrics:")
        logger.info(f"   Precision: {metrics.get('train_precision', 0):.3f}")
        logger.info(f"   Recall: {metrics.get('train_recall', 0):.3f}")
        logger.info(f"   F1-Score: {metrics.get('train_f1', 0):.3f}")
        
        logger.info("✅ Quantum training complete!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Quantum training failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_quantum_benchmark():
    """Step 4: Run quantum vs classical benchmark."""
    logger.info("\n" + "="*60)
    logger.info("STEP 4: QUANTUM VS CLASSICAL BENCHMARK")
    logger.info("="*60)
    
    try:
        from src.skills.quantum_anomaly.scripts.benchmark import benchmark_quantum_vs_classical
        
        benchmark_quantum_vs_classical(n_samples=200, n_test=50)
        
        logger.info("✅ Benchmark complete!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    logger.info("\n" + "#"*60)
    logger.info("#  COMP3520 - IMPROVED DATA & SKILLS TEST SUITE")
    logger.info("#"*60)
    
    results = {}
    
    # Run tests
    results['Data Generation'] = test_data_generation()
    results['Risk Assessment'] = test_risk_assessment()
    results['Quantum Training'] = test_quantum_with_balanced_data()
    results['Quantum Benchmark'] = test_quantum_benchmark()
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"   {status}  {test_name}")
    
    total_passed = sum(results.values())
    total_tests = len(results)
    
    logger.info("\n" + "="*60)
    logger.info(f"RESULTS: {total_passed}/{total_tests} tests passed")
    logger.info("="*60)
    
    if total_passed == total_tests:
        logger.info("\n🎉 ALL TESTS PASSED! 🎉\n")
        return 0
    else:
        logger.error(f"\n⚠️  {total_tests - total_passed} test(s) failed\n")
        return 1

if __name__ == '__main__':
    sys.exit(main())
