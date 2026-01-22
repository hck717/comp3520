"""Generate synthetic training labels for XGBoost risk model."""

import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from skills.risk_assessment.scripts.extract_features import extract_entity_features

logger = logging.getLogger(__name__)

# Sample entities for training (would be extracted from Neo4j in production)
SAMPLE_BUYERS = [
    "HSBC Hong Kong", "Standard Chartered", "DBS Bank", 
    "Citibank Asia", "Bank of China HK", "Hang Seng Bank",
    "OCBC Bank", "UOB Singapore", "Maybank", "CIMB Bank"
]

SAMPLE_SELLERS = [
    "ABC Trading Ltd", "XYZ Exports Co", "Global Shipping Inc",
    "Asia Commodities", "Euro Importers", "Pacific Trade Co"
]


def generate_synthetic_features(n_samples: int = 100) -> pd.DataFrame:
    """
    Generate synthetic feature data for training.
    
    In production, this would extract real features from Neo4j.
    For development, we generate realistic synthetic data.
    """
    np.random.seed(42)
    
    # Create two populations: clean (70%) and high-risk (30%)
    n_clean = int(n_samples * 0.7)
    n_risky = n_samples - n_clean
    
    # Clean entities: low risk patterns
    clean_data = {
        'transaction_count': np.random.poisson(25, n_clean),  # 15-35 transactions
        'total_exposure': np.random.lognormal(14, 0.5, n_clean),  # ~$1-5M
        'avg_lc_amount': np.random.lognormal(12, 0.3, n_clean),  # ~$200K avg
        'discrepancy_rate': np.random.beta(2, 20, n_clean),  # Low: 0-15%
        'late_shipment_rate': np.random.beta(2, 15, n_clean),  # Low: 0-20%
        'payment_delay_avg': np.random.gamma(2, 1.5, n_clean),  # 2-5 days
        'counterparty_diversity': np.random.beta(8, 2, n_clean),  # High: 70-95%
        'high_risk_country_exposure': np.random.beta(2, 10, n_clean),  # Low: 0-30%
        'sanctions_exposure': np.random.binomial(1, 0.05, n_clean),  # 5% chance
        'doc_completeness': np.random.beta(20, 2, n_clean),  # High: 85-100%
        'amendment_rate': np.random.beta(2, 10, n_clean),  # Low: 0-25%
        'fraud_flags': np.random.binomial(2, 0.1, n_clean),  # 0-2 flags
    }
    
    # High-risk entities: elevated risk patterns
    risky_data = {
        'transaction_count': np.random.poisson(8, n_risky),  # Fewer: 3-15
        'total_exposure': np.random.lognormal(13, 0.8, n_risky),  # Lower/volatile
        'avg_lc_amount': np.random.lognormal(11.5, 0.5, n_risky),  # Smaller LCs
        'discrepancy_rate': np.random.beta(5, 5, n_risky),  # High: 30-70%
        'late_shipment_rate': np.random.beta(5, 3, n_risky),  # High: 40-80%
        'payment_delay_avg': np.random.gamma(5, 3, n_risky),  # 10-25 days
        'counterparty_diversity': np.random.beta(2, 5, n_risky),  # Low: 20-50%
        'high_risk_country_exposure': np.random.beta(5, 3, n_risky),  # High: 40-80%
        'sanctions_exposure': np.random.binomial(2, 0.3, n_risky),  # 30% chance, 1-2 links
        'doc_completeness': np.random.beta(3, 8, n_risky),  # Low: 20-50%
        'amendment_rate': np.random.beta(5, 5, n_risky),  # High: 30-70%
        'fraud_flags': np.random.binomial(5, 0.4, n_risky),  # 1-5 flags
    }
    
    # Combine datasets
    clean_df = pd.DataFrame(clean_data)
    clean_df['label'] = 0  # Clean
    clean_df['entity_name'] = [f"Clean_Entity_{i}" for i in range(n_clean)]
    
    risky_df = pd.DataFrame(risky_data)
    risky_df['label'] = 1  # High-risk
    risky_df['entity_name'] = [f"Risky_Entity_{i}" for i in range(n_risky)]
    
    # Concatenate and shuffle
    df = pd.concat([clean_df, risky_df], ignore_index=True)
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    logger.info(f"Generated {len(df)} samples: {n_clean} clean, {n_risky} high-risk")
    return df


def label_entity(features: Dict) -> int:
    """
    Apply rule-based labeling logic.
    
    High Risk (1) if ANY of:
    - discrepancy_rate > 0.25
    - late_shipment_rate > 0.35
    - sanctions_exposure > 0
    - fraud_flags > 2
    - high_risk_country_exposure > 0.60
    - doc_completeness < 0.60
    
    Otherwise Clean (0)
    """
    if (
        features.get('discrepancy_rate', 0) > 0.25 or
        features.get('late_shipment_rate', 0) > 0.35 or
        features.get('sanctions_exposure', 0) > 0 or
        features.get('fraud_flags', 0) > 2 or
        features.get('high_risk_country_exposure', 0) > 0.60 or
        features.get('doc_completeness', 1) < 0.60
    ):
        return 1  # High-risk
    return 0  # Clean


def main(
    n_samples: int = 1000,
    output_path: str = "data/processed/training_data.csv"
):
    """
    Generate training dataset with labels.
    
    Args:
        n_samples: Number of samples to generate
        output_path: Path to save CSV
    """
    logger.info("="*60)
    logger.info("GENERATING TRAINING DATA FOR RISK MODEL")
    logger.info("="*60)
    
    # Generate synthetic features
    logger.info(f"\nGenerating {n_samples} synthetic samples...")
    df = generate_synthetic_features(n_samples)
    
    # Summary statistics
    logger.info("\nDataset Summary:")
    logger.info(f"  Total samples: {len(df)}")
    logger.info(f"  Clean entities (0): {(df['label'] == 0).sum()}")
    logger.info(f"  High-risk entities (1): {(df['label'] == 1).sum()}")
    logger.info(f"  Class balance: {(df['label'] == 1).sum() / len(df) * 100:.1f}% high-risk")
    
    # Feature statistics
    logger.info("\nFeature Ranges:")
    feature_cols = [col for col in df.columns if col not in ['label', 'entity_name']]
    for col in feature_cols:
        logger.info(f"  {col:30s}: [{df[col].min():.2f}, {df[col].max():.2f}]")
    
    # Save to CSV
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"\n✅ Training data saved to: {output_path}")
    logger.info(f"   Shape: {df.shape}")
    logger.info("\n" + "="*60)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main(n_samples=1000)
