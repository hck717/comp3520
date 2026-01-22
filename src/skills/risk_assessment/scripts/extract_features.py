"""Extract 12-dimensional risk features from Neo4j for entity risk assessment."""

import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)

# Neo4j connection (use environment variables in production)
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"

def extract_entity_features(
    entity_name: str,
    entity_type: str = "Buyer",
    lookback_days: int = 90,
    neo4j_uri: str = NEO4J_URI,
    neo4j_user: str = NEO4J_USER,
    neo4j_password: str = NEO4J_PASSWORD
) -> Dict:
    """
    Extract 12D risk features for an entity from Neo4j graph.
    
    Features:
    1. transaction_count: Number of LCs in lookback period
    2. total_exposure: Sum of LC amounts
    3. avg_lc_amount: Average LC amount
    4. discrepancy_rate: % of LCs with document discrepancies
    5. late_shipment_rate: % of LCs with late shipments
    6. payment_delay_avg: Average payment delay in days
    7. counterparty_diversity: Number of unique counterparties
    8. high_risk_country_exposure: % exposure to high-risk countries
    9. sanctions_exposure: % counterparties on sanctions lists
    10. doc_completeness: Average document completeness score
    11. amendment_rate: % of LCs requiring amendments
    12. fraud_flags: Number of fraud-related flags
    
    Args:
        entity_name: Name of entity (Buyer/Seller/Bank)
        entity_type: Type of entity ("Buyer", "Seller", "Bank")
        lookback_days: Historical period to analyze
        
    Returns:
        Dictionary with 12 feature values
    """
    driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    
    try:
        with driver.session() as session:
            # Query to extract all features in one pass
            query = f"""
            MATCH (entity:{entity_type} {{name: $entity_name}})
            OPTIONAL MATCH (entity)-[r]-(lc:LC)
            WHERE datetime(lc.issue_date) >= datetime() - duration({{days: $lookback_days}})
            
            WITH entity, collect(lc) AS lcs
            
            RETURN
                size(lcs) AS transaction_count,
                reduce(total = 0.0, lc IN lcs | total + toFloat(coalesce(lc.amount, 0))) AS total_exposure,
                
                // Document quality metrics
                reduce(disc = 0, lc IN lcs | disc + CASE WHEN lc.has_discrepancy = true THEN 1 ELSE 0 END) AS discrepancy_count,
                reduce(late = 0, lc IN lcs | late + CASE WHEN lc.shipment_delayed = true THEN 1 ELSE 0 END) AS late_shipment_count,
                reduce(delay = 0.0, lc IN lcs | delay + toFloat(coalesce(lc.payment_delay_days, 0))) AS total_payment_delay,
                
                // Amendment tracking
                reduce(amend = 0, lc IN lcs | amend + CASE WHEN lc.amended = true THEN 1 ELSE 0 END) AS amendment_count,
                
                // Document completeness
                reduce(comp = 0.0, lc IN lcs | comp + toFloat(coalesce(lc.document_completeness, 1.0))) AS total_completeness
            """
            
            result = session.run(query, entity_name=entity_name, lookback_days=lookback_days)
            record = result.single()
            
            if not record:
                logger.warning(f"Entity '{entity_name}' not found in Neo4j")
                return _get_default_features()
            
            # Extract base metrics
            tx_count = record['transaction_count'] or 0
            total_exposure = record['total_exposure'] or 0.0
            discrepancy_count = record['discrepancy_count'] or 0
            late_shipment_count = record['late_shipment_count'] or 0
            total_payment_delay = record['total_payment_delay'] or 0.0
            amendment_count = record['amendment_count'] or 0
            total_completeness = record['total_completeness'] or 0.0
            
            # Calculate derived metrics
            avg_lc_amount = total_exposure / tx_count if tx_count > 0 else 0.0
            discrepancy_rate = discrepancy_count / tx_count if tx_count > 0 else 0.0
            late_shipment_rate = late_shipment_count / tx_count if tx_count > 0 else 0.0
            payment_delay_avg = total_payment_delay / tx_count if tx_count > 0 else 0.0
            doc_completeness = total_completeness / tx_count if tx_count > 0 else 1.0
            amendment_rate = amendment_count / tx_count if tx_count > 0 else 0.0
            
            # Get counterparty diversity
            counterparty_diversity = _get_counterparty_diversity(
                session, entity_name, entity_type, lookback_days
            )
            
            # Get country risk exposure
            high_risk_country_exposure = _get_high_risk_country_exposure(
                session, entity_name, entity_type, lookback_days
            )
            
            # Get sanctions exposure
            sanctions_exposure = _get_sanctions_exposure(
                session, entity_name, entity_type, lookback_days
            )
            
            # Get fraud flags
            fraud_flags = _get_fraud_flags(
                session, entity_name, entity_type, lookback_days
            )
            
            features = {
                'transaction_count': tx_count,
                'total_exposure': total_exposure,
                'avg_lc_amount': avg_lc_amount,
                'discrepancy_rate': discrepancy_rate,
                'late_shipment_rate': late_shipment_rate,
                'payment_delay_avg': payment_delay_avg,
                'counterparty_diversity': counterparty_diversity,
                'high_risk_country_exposure': high_risk_country_exposure,
                'sanctions_exposure': sanctions_exposure,
                'doc_completeness': doc_completeness,
                'amendment_rate': amendment_rate,
                'fraud_flags': fraud_flags,
            }
            
            logger.info(f"Extracted features for {entity_name}: {tx_count} transactions")
            return features
            
    except Exception as e:
        logger.error(f"Error extracting features for {entity_name}: {e}")
        return _get_default_features()
    finally:
        driver.close()


def _get_counterparty_diversity(session, entity_name: str, entity_type: str, lookback_days: int) -> int:
    """Count unique counterparties."""
    if entity_type == "Buyer":
        counterparty_type = "Seller"
    elif entity_type == "Seller":
        counterparty_type = "Buyer"
    else:
        return 0
    
    query = f"""
    MATCH (entity:{entity_type} {{name: $entity_name}})-[r]-(lc:LC)-[]-(counterparty:{counterparty_type})
    WHERE datetime(lc.issue_date) >= datetime() - duration({{days: $lookback_days}})
    RETURN count(DISTINCT counterparty.name) AS diversity
    """
    
    result = session.run(query, entity_name=entity_name, lookback_days=lookback_days)
    record = result.single()
    return record['diversity'] if record else 0


def _get_high_risk_country_exposure(session, entity_name: str, entity_type: str, lookback_days: int) -> float:
    """Calculate % of transactions involving high-risk countries (risk_score >= 7)."""
    query = f"""
    MATCH (entity:{entity_type} {{name: $entity_name}})-[r]-(lc:LC)
    WHERE datetime(lc.issue_date) >= datetime() - duration({{days: $lookback_days}})
    OPTIONAL MATCH (lc)-[:AT_PORT]-(port:Port)-[:IN_COUNTRY]-(country:Country)
    WITH count(lc) AS total_lcs,
         reduce(high_risk = 0, country IN collect(country) | 
                high_risk + CASE WHEN country.risk_score >= 7 THEN 1 ELSE 0 END) AS high_risk_count
    RETURN CASE WHEN total_lcs > 0 THEN toFloat(high_risk_count) / total_lcs ELSE 0.0 END AS exposure
    """
    
    result = session.run(query, entity_name=entity_name, lookback_days=lookback_days)
    record = result.single()
    return record['exposure'] if record else 0.0


def _get_sanctions_exposure(session, entity_name: str, entity_type: str, lookback_days: int) -> float:
    """Calculate % of counterparties on sanctions lists."""
    if entity_type == "Buyer":
        counterparty_type = "Seller"
    elif entity_type == "Seller":
        counterparty_type = "Buyer"
    else:
        return 0.0
    
    query = f"""
    MATCH (entity:{entity_type} {{name: $entity_name}})-[r]-(lc:LC)-[]-(counterparty:{counterparty_type})
    WHERE datetime(lc.issue_date) >= datetime() - duration({{days: $lookback_days}})
    WITH count(DISTINCT counterparty) AS total_counterparties,
         reduce(sanctioned = 0, cp IN collect(DISTINCT counterparty) | 
                sanctioned + CASE WHEN cp.on_sanctions_list = true THEN 1 ELSE 0 END) AS sanctioned_count
    RETURN CASE WHEN total_counterparties > 0 THEN toFloat(sanctioned_count) / total_counterparties ELSE 0.0 END AS exposure
    """
    
    result = session.run(query, entity_name=entity_name, lookback_days=lookback_days)
    record = result.single()
    return record['exposure'] if record else 0.0


def _get_fraud_flags(session, entity_name: str, entity_type: str, lookback_days: int) -> int:
    """Count fraud-related flags (suspicious patterns)."""
    query = f"""
    MATCH (entity:{entity_type} {{name: $entity_name}})-[r]-(lc:LC)
    WHERE datetime(lc.issue_date) >= datetime() - duration({{days: $lookback_days}})
    WITH lc
    WHERE lc.suspicious_activity = true OR lc.fraud_flag = true OR lc.aml_alert = true
    RETURN count(lc) AS fraud_count
    """
    
    result = session.run(query, entity_name=entity_name, lookback_days=lookback_days)
    record = result.single()
    return record['fraud_count'] if record else 0


def _get_default_features() -> Dict:
    """Return default feature values for entities with no history."""
    return {
        'transaction_count': 0,
        'total_exposure': 0.0,
        'avg_lc_amount': 0.0,
        'discrepancy_rate': 0.0,
        'late_shipment_rate': 0.0,
        'payment_delay_avg': 0.0,
        'counterparty_diversity': 0,
        'high_risk_country_exposure': 0.0,
        'sanctions_exposure': 0.0,
        'doc_completeness': 1.0,
        'amendment_rate': 0.0,
        'fraud_flags': 0,
    }


if __name__ == '__main__':
    # Test feature extraction
    logging.basicConfig(level=logging.INFO)
    
    # Extract features for a sample buyer
    features = extract_entity_features(
        entity_name="Global Import Export Ltd",
        entity_type="Buyer",
        lookback_days=90
    )
    
    print("\nExtracted Features:")
    for key, value in features.items():
        print(f"  {key}: {value}")
