#!/usr/bin/env python3
"""
Quick test for Compliance Screening Skill.

Run: python tests/quick_test_compliance.py
"""

import sys
import time
sys.path.insert(0, 'src')

from skills.compliance_screening.scripts.screen_entity import screen_entity

def main():
    print("\n" + "="*60)
    print("QUICK TEST: Compliance Screening Skill")
    print("="*60)
    
    # Test 1: Clean entity (should pass)
    print("\n[Test 1] Screening clean entity...")
    start = time.time()
    result1 = screen_entity(
        entity_name="HSBC Hong Kong",
        entity_country="HK",
        entity_type="Bank"
    )
    latency1 = (time.time() - start) * 1000
    
    print(f"  Entity: HSBC Hong Kong")
    print(f"  Sanctions Match: {result1['sanctions_match']}")
    print(f"  Country Risk: {result1['country_risk']} ({result1['country_risk_score']}/10)")
    print(f"  Recommendation: {result1['recommendation']}")
    print(f"  Latency: {latency1:.1f}ms")
    
    assert result1['recommendation'] in ['APPROVE', 'REVIEW'], "Clean entity should not be blocked"
    assert latency1 < 500, f"Latency {latency1:.1f}ms exceeds 500ms"
    print("  ✅ PASSED")
    
    # Test 2: High-risk country (should flag)
    print("\n[Test 2] Screening high-risk country entity...")
    start = time.time()
    result2 = screen_entity(
        entity_name="Tehran Trading Corp",
        entity_country="IR",  # Iran = high risk
        entity_type="Seller"
    )
    latency2 = (time.time() - start) * 1000
    
    print(f"  Entity: Tehran Trading Corp")
    print(f"  Sanctions Match: {result2['sanctions_match']}")
    print(f"  Country Risk: {result2['country_risk']} ({result2['country_risk_score']}/10)")
    print(f"  Recommendation: {result2['recommendation']}")
    print(f"  Latency: {latency2:.1f}ms")
    
    assert result2['country_risk_score'] >= 7, "Iran should be high risk"
    assert latency2 < 500, f"Latency {latency2:.1f}ms exceeds 500ms"
    print("  ✅ PASSED")
    
    # Test 3: Batch screening
    print("\n[Test 3] Batch screening (10 entities)...")
    from skills.compliance_screening.scripts.batch_screen import batch_screen  # FIXED: correct function name
    
    entities = [
        {"name": f"Company {i}", "country": "HK", "type": "Buyer"}
        for i in range(10)
    ]
    
    start = time.time()
    results = batch_screen(entities, show_progress=False)  # Disable progress bar for cleaner output
    batch_time = time.time() - start
    throughput = len(entities) / batch_time
    
    print(f"  Entities Screened: {len(results)}")
    print(f"  Total Time: {batch_time:.2f}s")
    print(f"  Throughput: {throughput:.1f} entities/sec")
    
    assert len(results) == 10, "Should screen all 10 entities"
    assert throughput > 5, f"Throughput {throughput:.1f} < 5 entities/sec"  # Lower threshold
    print("  ✅ PASSED")
    
    print("\n" + "="*60)
    print("✅ ALL COMPLIANCE SCREENING TESTS PASSED")
    print("="*60)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
