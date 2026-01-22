"""Generate labeled training data for risk assessment model."""

import logging
import pandas as pd
from typing import List, Dict
from neo4j import GraphDatabase
from .extract_features import extract_entity_features

logger = logging.getLogger(__name__)

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"

def generate_labels(
    n_entities: int = 1000,
    entity_type: str = "Buyer",
    lookback_days: int = 90,
    output_path: str = "data/processed/training_data.csv"
) -> pd.DataFrame:
    """
    Generate labeled training dataset by extracting features and labeling entities.
    
    Labeling criteria (HIGH RISK if any of the following):
    - discrepancy_rate > 0.3 (30% of transactions have issues)
    - late_shipment_rate > 0.4
    - payment_delay_avg > 15 days
    - sanctions_exposure > 0
    - fraud_flags > 2
    - high_risk_country_exposure > 0.5
    
    Args:
        n_entities: Number of entities to label
        entity_type: Type of entities ("Buyer" or "Seller")
        lookback_days: Historical period
        output_path: Path to save training data CSV
        
    Returns:
        DataFrame with features and labels
    """
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        # Get list of entities from Neo4j
        with driver.session() as session:
            query = f"""
            MATCH (e:{entity_type})
            RETURN e.name AS name
            LIMIT $n_entities
            """
            result = session.run(query, n_entities=n_entities)
            entity_names = [record['name'] for record in result]
        
        logger.info(f"Found {len(entity_names)} {entity_type} entities")
        
        # Extract features for each entity
        training_data = []
        
        for i, entity_name in enumerate(entity_names):
            if i % 50 == 0:
                logger.info(f"Processing entity {i+1}/{len(entity_names)}")
            
            features = extract_entity_features(
                entity_name=entity_name,
                entity_type=entity_type,
                lookback_days=lookback_days
            )
            
            # Skip entities with no transaction history
            if features['transaction_count'] == 0:
                continue
            
            # Label entity as high-risk (1) or low-risk (0)
            label = _label_entity(features)
            
            # Add to training data
            row = features.copy()
            row['entity_name'] = entity_name
            row['label'] = label
            training_data.append(row)
        
        # Convert to DataFrame
        df = pd.DataFrame(training_data)
        
        logger.info(f"Generated {len(df)} training samples")
        logger.info(f"High-risk entities: {df['label'].sum()} ({df['label'].mean()*100:.1f}%)")
        
        # Save to CSV
        if output_path:
            df.to_csv(output_path, index=False)
            logger.info(f"Saved training data to {output_path}")
        
        return df
        
    finally:
        driver.close()


def _label_entity(features: Dict) -> int:
    """
    Label entity as high-risk (1) or low-risk (0) based on features.
    
    Returns:
        1 if high-risk, 0 if low-risk
    """
    # High-risk conditions
    high_risk_conditions = [
        features['discrepancy_rate'] > 0.3,
        features['late_shipment_rate'] > 0.4,
        features['payment_delay_avg'] > 15,
        features['sanctions_exposure'] > 0,
        features['fraud_flags'] > 2,
        features['high_risk_country_exposure'] > 0.5,
        features['doc_completeness'] < 0.7,
        features['amendment_rate'] > 0.4,
    ]
    
    # Label as high-risk if 2+ conditions met
    if sum(high_risk_conditions) >= 2:
        return 1
    else:
        return 0


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Generate training data
    df = generate_labels(
        n_entities=100,  # Start with 100 for quick test
        entity_type="Buyer",
        output_path="data/processed/training_data.csv"
    )
    
    print("\nTraining Data Summary:")
    print(df.describe())
    print(f"\nClass distribution:")
    print(df['label'].value_counts())
