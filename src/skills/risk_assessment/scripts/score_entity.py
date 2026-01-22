"""Real-time entity risk scoring using trained XGBoost model."""

import logging
import joblib
import numpy as np
from typing import Dict
from pathlib import Path
from .extract_features import extract_entity_features

logger = logging.getLogger(__name__)

FEATURE_COLUMNS = [
    'transaction_count',
    'total_exposure',
    'avg_lc_amount',
    'discrepancy_rate',
    'late_shipment_rate',
    'payment_delay_avg',
    'counterparty_diversity',
    'high_risk_country_exposure',
    'sanctions_exposure',
    'doc_completeness',
    'amendment_rate',
    'fraud_flags',
]

def score_entity_risk(
    entity_name: str,
    entity_type: str = "Buyer",
    lookback_days: int = 90,
    model_path: str = "models/risk_model.pkl"
) -> Dict:
    """
    Score entity risk using trained XGBoost model.
    
    Args:
        entity_name: Name of entity to score
        entity_type: Type of entity ("Buyer", "Seller", "Bank")
        lookback_days: Historical period for feature extraction
        model_path: Path to trained model
        
    Returns:
        Dictionary with:
        - risk_score: Probability of high risk (0-1)
        - risk_level: "low", "medium", "high"
        - risk_factors: List of contributing factors
        - features: Raw feature values
    """
    # Check if model exists
    if not Path(model_path).exists():
        logger.error(f"Model not found at {model_path}. Train model first.")
        raise FileNotFoundError(f"Model not found: {model_path}")
    
    # Load trained model
    model = joblib.load(model_path)
    logger.info(f"Loaded model from {model_path}")
    
    # Extract features
    features = extract_entity_features(
        entity_name=entity_name,
        entity_type=entity_type,
        lookback_days=lookback_days
    )
    
    # Check if entity has history
    if features['transaction_count'] == 0:
        return {
            'entity_name': entity_name,
            'risk_score': 0.5,  # Neutral score for new entities
            'risk_level': 'unknown',
            'risk_factors': ['No transaction history'],
            'features': features,
            'recommendation': 'REVIEW - New entity, no history'
        }
    
    # Prepare feature vector
    X = np.array([[features[col] for col in FEATURE_COLUMNS]])
    
    # Predict risk
    risk_score = model.predict_proba(X)[0][1]  # Probability of class 1 (high-risk)
    
    # Determine risk level
    if risk_score >= 0.7:
        risk_level = "high"
        recommendation = "BLOCK - High risk entity"
    elif risk_score >= 0.4:
        risk_level = "medium"
        recommendation = "REVIEW - Medium risk, manual review required"
    else:
        risk_level = "low"
        recommendation = "APPROVE - Low risk entity"
    
    # Identify top risk factors
    risk_factors = _identify_risk_factors(features)
    
    logger.info(f"Scored {entity_name}: {risk_score:.2f} ({risk_level})")
    
    return {
        'entity_name': entity_name,
        'risk_score': float(risk_score),
        'risk_level': risk_level,
        'risk_factors': risk_factors,
        'features': features,
        'recommendation': recommendation
    }


def _identify_risk_factors(features: Dict) -> list:
    """
    Identify specific risk factors based on feature values.
    
    Returns:
        List of human-readable risk factor descriptions
    """
    factors = []
    
    if features['discrepancy_rate'] > 0.3:
        factors.append(f"High document discrepancy rate ({features['discrepancy_rate']*100:.0f}%)")
    
    if features['late_shipment_rate'] > 0.4:
        factors.append(f"Frequent late shipments ({features['late_shipment_rate']*100:.0f}%)")
    
    if features['payment_delay_avg'] > 15:
        factors.append(f"Average payment delay: {features['payment_delay_avg']:.0f} days")
    
    if features['sanctions_exposure'] > 0:
        factors.append(f"Sanctions exposure ({features['sanctions_exposure']*100:.0f}% of counterparties)")
    
    if features['fraud_flags'] > 2:
        factors.append(f"{features['fraud_flags']} fraud flags detected")
    
    if features['high_risk_country_exposure'] > 0.5:
        factors.append(f"High-risk country exposure ({features['high_risk_country_exposure']*100:.0f}%)")
    
    if features['doc_completeness'] < 0.7:
        factors.append(f"Low document completeness ({features['doc_completeness']*100:.0f}%)")
    
    if features['amendment_rate'] > 0.4:
        factors.append(f"High LC amendment rate ({features['amendment_rate']*100:.0f}%)")
    
    if features['counterparty_diversity'] < 3 and features['transaction_count'] > 10:
        factors.append("Low counterparty diversity")
    
    if not factors:
        factors.append("No significant risk factors detected")
    
    return factors


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Test scoring
    result = score_entity_risk(
        entity_name="Global Import Export Ltd",
        entity_type="Buyer",
        model_path="models/risk_model.pkl"
    )
    
    print("\nRisk Scoring Result:")
    print(f"  Entity: {result['entity_name']}")
    print(f"  Risk Score: {result['risk_score']:.2f}")
    print(f"  Risk Level: {result['risk_level']}")
    print(f"  Recommendation: {result['recommendation']}")
    print(f"\n  Risk Factors:")
    for factor in result['risk_factors']:
        print(f"    - {factor}")
