"""Batch scoring for multiple entities."""

import logging
import joblib
import numpy as np
import pandas as pd
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from skills.risk_assessment.scripts.score_entity import score_entity

logger = logging.getLogger(__name__)


def batch_score_entities(
    entity_names: List[str],
    entity_type: str = "Buyer",
    model_path: str = "models/risk_model.pkl",
    max_workers: int = 4
) -> List[Dict]:
    """
    Score multiple entities in parallel.
    
    Args:
        entity_names: List of entity names to score
        entity_type: "Buyer" or "Seller"
        model_path: Path to trained model
        max_workers: Number of parallel threads
        
    Returns:
        List of scoring results (one per entity)
    """
    logger.info("="*60)
    logger.info(f"  BATCH SCORING: {len(entity_names)} ENTITIES")
    logger.info("="*60)
    
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all scoring tasks
        future_to_entity = {
            executor.submit(
                score_entity,
                entity_name=name,
                entity_type=entity_type,
                model_path=model_path
            ): name
            for name in entity_names
        }
        
        # Collect results as they complete
        for i, future in enumerate(as_completed(future_to_entity), 1):
            entity_name = future_to_entity[future]
            try:
                result = future.result()
                results.append(result)
                logger.info(f"  [{i}/{len(entity_names)}] {entity_name}: {result['risk_score']:.3f} ({result['risk_category']})")
            except Exception as e:
                logger.error(f"  [{i}/{len(entity_names)}] {entity_name}: ERROR - {e}")
                results.append({
                    'entity_name': entity_name,
                    'error': str(e),
                    'risk_score': None,
                    'risk_category': 'error'
                })
    
    logger.info("\n" + "="*60)
    logger.info(f"  BATCH SCORING COMPLETE")
    logger.info("="*60)
    
    # Summary statistics
    valid_scores = [r['risk_score'] for r in results if r['risk_score'] is not None]
    if valid_scores:
        logger.info(f"\n  Summary Statistics:")
        logger.info(f"    Total scored: {len(valid_scores)}")
        logger.info(f"    Mean risk score: {np.mean(valid_scores):.3f}")
        logger.info(f"    Std dev: {np.std(valid_scores):.3f}")
        logger.info(f"    Min: {np.min(valid_scores):.3f}")
        logger.info(f"    Max: {np.max(valid_scores):.3f}")
        
        # Risk distribution
        categories = [r['risk_category'] for r in results if r['risk_score'] is not None]
        logger.info(f"\n  Risk Distribution:")
        logger.info(f"    Low: {categories.count('low')} ({categories.count('low')/len(categories)*100:.1f}%)")
        logger.info(f"    Medium: {categories.count('medium')} ({categories.count('medium')/len(categories)*100:.1f}%)")
        logger.info(f"    High: {categories.count('high')} ({categories.count('high')/len(categories)*100:.1f}%)")
    
    return results


def export_to_csv(results: List[Dict], output_path: str = "data/batch_scores.csv"):
    """Export batch scoring results to CSV."""
    
    rows = []
    for r in results:
        if 'error' not in r:
            row = {
                'entity_name': r['entity_name'],
                'risk_score': r['risk_score'],
                'risk_category': r['risk_category'],
                'credit_limit_usd': r['credit_limit_usd'],
                'recommendation': r['recommendation'],
                'transaction_count': r['features']['transaction_count'],
                'discrepancy_rate': r['features']['discrepancy_rate'],
                'late_shipment_rate': r['features']['late_shipment_rate'],
                'doc_completeness': r['features']['doc_completeness'],
                'high_risk_country_exposure': r['features']['high_risk_country_exposure'],
                'sanctions_exposure': r['features']['sanctions_exposure'],
                'fraud_flags': r['features']['fraud_flags']
            }
            rows.append(row)
    
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    logger.info(f"\n  💾 Results exported to: {output_path}")
    logger.info(f"     Shape: {df.shape}")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Test batch scoring
    test_entities = [
        "HSBC Hong Kong",
        "Standard Chartered",
        "DBS Bank",
        "Citibank Asia",
        "Bank of China HK"
    ]
    
    results = batch_score_entities(
        entity_names=test_entities,
        entity_type="Buyer",
        model_path="models/risk_model.pkl",
        max_workers=2
    )
    
    # Export results
    export_to_csv(results, "data/batch_scores.csv")
    
    print("\n✅ Batch scoring complete!")
