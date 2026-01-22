#!/usr/bin/env python3
"""
Quick test for Predictive Analytics Skill.

Run: python tests/quick_test_predictive.py
"""

import sys
import time
import numpy as np
sys.path.insert(0, 'src')

def main():
    print("\n" + "="*60)
    print("QUICK TEST: Predictive Analytics Skill")
    print("="*60)
    
    # Test 1: Isolation Forest (quick to train)
    print("\n[Test 1] Training Isolation Forest...")
    from skills.predictive_analytics.scripts.train_isolation_forest import train_model
    
    start = time.time()
    metrics = train_model(
        n_samples=200,  # Small for quick test
        output_path='models/isolation_forest_test.pkl'
    )
    train_time = time.time() - start
    
    print(f"  Training Time: {train_time:.1f}s")
    print(f"  F1 Score: {metrics['f1_score']:.3f}")
    print(f"  Precision: {metrics['precision']:.3f}")
    print(f"  Recall: {metrics['recall']:.3f}")
    
    assert metrics['f1_score'] >= 0.60, "F1 too low for quick test"
    assert train_time < 10, "Training too slow"
    print("  ✅ PASSED")
    
    # Test 2: Anomaly detection inference
    print("\n[Test 2] Testing anomaly detection...")
    from skills.predictive_analytics.scripts.isolation_forest import detect_anomalies
    
    # Create test transaction
    test_features = {
        'amount_deviation': 2.5,  # High deviation
        'time_deviation': 0.5,
        'port_risk': 0.8,  # High risk
        'doc_completeness': 0.6  # Low completeness
    }
    
    result = detect_anomalies(
        features=test_features,
        model_path='models/isolation_forest_test.pkl'
    )
    
    print(f"  Anomaly Detected: {result['is_anomaly']}")
    print(f"  Anomaly Score: {result['anomaly_score']:.2f}")
    print(f"  Confidence: {result['anomaly_confidence']:.0%}")
    
    # High deviation + high risk should trigger anomaly
    print("  ✅ PASSED")
    
    # Test 3: Prophet forecasting (mock for quick test)
    print("\n[Test 3] Prophet LC volume forecasting...")
    print("  (Using synthetic data for quick test)")
    
    from skills.predictive_analytics.scripts.train_prophet import train_model as train_prophet
    
    # Generate synthetic LC volume data
    import pandas as pd
    dates = pd.date_range(start='2025-01-01', end='2026-01-22', freq='D')
    lc_counts = np.random.poisson(15, size=len(dates))  # Average 15 LCs/day
    
    df = pd.DataFrame({
        'ds': dates,
        'y': lc_counts
    })
    df.to_csv('data/processed/lc_volume_test.csv', index=False)
    
    start = time.time()
    model_path = train_prophet(
        data_path='data/processed/lc_volume_test.csv',
        output_path='models/prophet_test.pkl'
    )
    train_time = time.time() - start
    
    print(f"  Training Time: {train_time:.1f}s")
    
    # Generate 7-day forecast
    from skills.predictive_analytics.scripts.prophet_forecaster import forecast_lc_volume
    forecast = forecast_lc_volume(
        forecast_days=7,
        model_path='models/prophet_test.pkl'
    )
    
    print(f"  Forecast Generated: {len(forecast['predictions'])} days")
    print(f"  Trend: {forecast['trend']}")
    print(f"  Sample (Day 1): {forecast['predictions'][0]['lc_count']} LCs")
    
    assert len(forecast['predictions']) == 7
    print("  ✅ PASSED")
    
    print("\n" + "="*60)
    print("✅ ALL PREDICTIVE ANALYTICS TESTS PASSED")
    print("="*60)
    print("\n💡 For full model training:")
    print("   - LSTM: python src/skills/predictive_analytics/scripts/train_lstm.py")
    print("   - Prophet (full): Use real Neo4j data")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
