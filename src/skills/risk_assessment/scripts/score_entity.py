"""Score single entity using trained risk model."""

import logging
import joblib
import numpy as np
from typing import Dict
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from skills.risk_assessment.scripts.extract_features import extract_entity_features

logger = logging.getLogger(__name__)

# Risk thresholds
LOW_RISK_THRESHOLD = 0.3
MEDIUM_RISK_THRESHOLD = 0.7

# Credit limits (USD)
CREDIT_LIMIT_LOW_RISK = 2_000_000
CREDIT_LIMIT_MEDIUM_RISK = 500_000
CREDIT_LIMIT_HIGH_RISK = 100_000


def score_entity(
    entity_name: str,
    entity_type: str = "Buyer",
    model_path: str = "models/risk_model.pkl",
    lookback_days: int = 90
) -> Dict:
    """
    Score entity for credit risk using trained XGBoost model.
    
    Args:
        entity_name: Name of entity to score
        entity_type: "Buyer" or "Seller"
        model_path: Path to trained model pickle
        lookback_days: Historical window for feature extraction
        
    Returns:
        Dictionary with:
        - entity_name: str
        - risk_score: float (0-1, higher = riskier)
        - risk_category: "low" | "medium" | "high"
        - credit_limit_usd: int
        - recommendation: str
        - features: Dict of 12 features
        - model_version: str
    """
    logger.info(f"Scoring entity: {entity_name} ({entity_type})")
    
    # Load trained model
    try:
        model_data = joblib.load(model_path)
        model = model_data['model']
        feature_cols = model_data['feature_cols']
        logger.info(f"Loaded model from {model_path}")
    except FileNotFoundError:
        logger.error(f"Model not found: {model_path}")
        logger.error("Please train model first: python src/skills/risk_assessment/scripts/train_model.py")
        raise
    
    # Extract features from Neo4j
    logger.info(f"Extracting features (lookback: {lookback_days} days)...")
    features = extract_entity_features(
        entity_name=entity_name,
        entity_type=entity_type,
        lookback_days=lookback_days
    )
    
    # Prepare feature vector in correct order
    X = np.array([[features[col] for col in feature_cols]])
    
    # Predict risk score
    risk_score = float(model.predict_proba(X)[0, 1])  # Probability of high-risk class
    
    # Categorize risk
    if risk_score < LOW_RISK_THRESHOLD:
        risk_category = "low"
        credit_limit = CREDIT_LIMIT_LOW_RISK
        recommendation = "APPROVE"
    elif risk_score < MEDIUM_RISK_THRESHOLD:
        risk_category = "medium"
        credit_limit = CREDIT_LIMIT_MEDIUM_RISK
        recommendation = "APPROVE_WITH_CONDITIONS"
    else:
        risk_category = "high"
        credit_limit = CREDIT_LIMIT_HIGH_RISK
        recommendation = "REQUIRE_COLLATERAL"
    
    logger.info(f"Risk score: {risk_score:.3f} ({risk_category})")
    logger.info(f"Credit limit: ${credit_limit:,}")
    logger.info(f"Recommendation: {recommendation}")
    
    return {
        'entity_name': entity_name,
        'entity_type': entity_type,
        'risk_score': round(risk_score, 3),
        'risk_category': risk_category,
        'credit_limit_usd': credit_limit,
        'recommendation': recommendation,
        'features': features,
        'model_version': 'v1.0',
        'scored_at': str(np.datetime64('now'))
    }


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Test scoring
    result = score_entity(
        entity_name="HSBC Hong Kong",
        entity_type="Buyer",
        model_path="models/risk_model.pkl"
    )
    
    print("\n" + "="*60)
    print("  CREDIT RISK ASSESSMENT RESULT")
    print("="*60)
    print(f"\n  Entity: {result['entity_name']}")
    print(f"  Risk Score: {result['risk_score']:.3f}")
    print(f"  Risk Category: {result['risk_category'].upper()}")
    print(f"  Credit Limit: ${result['credit_limit_usd']:,}")
    print(f"  Recommendation: {result['recommendation']}")
    print(f"\n  Key Risk Features:")
    print(f"    Discrepancy Rate: {result['features']['discrepancy_rate']:.1%}")
    print(f"    Late Shipment Rate: {result['features']['late_shipment_rate']:.1%}")
    print(f"    Document Completeness: {result['features']['doc_completeness']:.1%}")
    print(f"    High-Risk Exposure: {result['features']['high_risk_country_exposure']:.1%}")
    print("\n" + "="*60)
