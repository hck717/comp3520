"""Extract risk features from Neo4j for credit scoring."""

import logging
import numpy as np
from typing import Dict, Optional
from neo4j import GraphDatabase
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Neo4j connection
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "sentinel2025"


def extract_entity_features(
    entity_name: str,
    entity_type: str = "Buyer",
    lookback_days: int = 90
) -> Dict:
    """
    Extract 12 risk features from Neo4j graph for credit scoring.
    
    Args:
        entity_name: Name of the entity (e.g., "HSBC Hong Kong")
        entity_type: "Buyer" or "Seller"
        lookback_days: Historical window (default: 90 days)
        
    Returns:
        Dictionary with 12 features:
        - Behavioral: transaction_count, total_exposure, avg_lc_amount,
                     discrepancy_rate, late_shipment_rate, payment_delay_avg
        - Network: counterparty_diversity, high_risk_country_exposure, sanctions_exposure
        - Document: doc_completeness, amendment_rate, fraud_flags
    """
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        with driver.session() as session:
            # 1. Basic transaction metrics
            behavioral = session.execute_read(
                _get_behavioral_features,
                entity_name, entity_type, lookback_days
            )
            
            # 2. Network risk metrics
            network = session.execute_read(
                _get_network_features,
                entity_name, entity_type, lookback_days
            )
            
            # 3. Document quality metrics
            doc_quality = session.execute_read(
                _get_document_features,
                entity_name, entity_type, lookback_days
            )
            
            # Combine all features
            features = {**behavioral, **network, **doc_quality}
            
            logger.info(f"Extracted {len(features)} features for {entity_name}")
            return features
            
    finally:
        driver.close()


def _get_behavioral_features(tx, entity_name: str, entity_type: str, lookback_days: int) -> Dict:
    """Extract behavioral features from transaction history."""
    
    # Get all LCs for this entity in lookback window
    query = f"""
    MATCH (e:{entity_type} {{name: $entity_name}})-[rel]->(lc:LetterOfCredit)
    WHERE lc.issue_date >= date() - duration({{days: $lookback_days}})
    OPTIONAL MATCH (lc)-[:REFERENCES]->(inv:CommercialInvoice)
    OPTIONAL MATCH (lc)-[:SHIPPED_VIA]->(bl:BillOfLading)
    RETURN 
        count(DISTINCT lc) as lc_count,
        sum(lc.amount) as total_amount,
        avg(lc.amount) as avg_amount,
        count(DISTINCT inv) as invoice_count,
        count(DISTINCT bl) as bl_count,
        collect({{lc_amount: lc.amount, inv_amount: inv.invoice_amount}}) as amounts,
        collect({{shipment_date: bl.shipment_date, lc_date: lc.issue_date}}) as dates
    """
    
    result = tx.run(query, entity_name=entity_name, lookback_days=lookback_days)
    record = result.single()
    
    if not record or record['lc_count'] == 0:
        # No transaction history - return conservative defaults
        return {
            'transaction_count': 0,
            'total_exposure': 0.0,
            'avg_lc_amount': 0.0,
            'discrepancy_rate': 0.5,  # Unknown = medium risk
            'late_shipment_rate': 0.3,
            'payment_delay_avg': 15.0
        }
    
    lc_count = record['lc_count']
    total_amount = record['total_amount'] or 0
    avg_amount = record['avg_amount'] or 0
    
    # Calculate discrepancy rate (invoice != LC amount)
    discrepancies = 0
    for item in record['amounts']:
        if item['lc_amount'] and item['inv_amount']:
            diff_pct = abs(item['lc_amount'] - item['inv_amount']) / item['lc_amount']
            if diff_pct > 0.10:  # >10% difference
                discrepancies += 1
    discrepancy_rate = discrepancies / lc_count if lc_count > 0 else 0
    
    # Calculate late shipment rate
    late_shipments = 0
    payment_delays = []
    for item in record['dates']:
        if item['shipment_date'] and item['lc_date']:
            # Assuming 30-day standard window
            days_diff = (item['shipment_date'] - item['lc_date']).days
            if days_diff > 30:
                late_shipments += 1
            payment_delays.append(max(0, days_diff))
    
    late_rate = late_shipments / len(record['dates']) if len(record['dates']) > 0 else 0
    avg_delay = np.mean(payment_delays) if payment_delays else 0
    
    return {
        'transaction_count': int(lc_count),
        'total_exposure': float(total_amount),
        'avg_lc_amount': float(avg_amount),
        'discrepancy_rate': round(discrepancy_rate, 3),
        'late_shipment_rate': round(late_rate, 3),
        'payment_delay_avg': round(avg_delay, 2)
    }


def _get_network_features(tx, entity_name: str, entity_type: str, lookback_days: int) -> Dict:
    """Extract network risk features."""
    
    # Counterparty diversity
    counterparty_type = "Seller" if entity_type == "Buyer" else "Buyer"
    
    query = f"""
    MATCH (e:{entity_type} {{name: $entity_name}})-[]->(lc:LetterOfCredit)
    WHERE lc.issue_date >= date() - duration({{days: $lookback_days}})
    OPTIONAL MATCH (lc)-[]-(counterparty:{counterparty_type})
    WITH count(DISTINCT lc) as total_lcs, count(DISTINCT counterparty) as unique_counterparties
    RETURN 
        CASE WHEN total_lcs > 0 THEN unique_counterparties * 1.0 / total_lcs ELSE 0 END as diversity
    """
    
    result = tx.run(query, entity_name=entity_name, lookback_days=lookback_days)
    record = result.single()
    diversity = record['diversity'] if record else 0.0
    
    # High-risk country exposure (placeholder - would check actual countries)
    # For now, simulate with random baseline
    high_risk_exposure = np.random.uniform(0, 0.3)  # 0-30% exposure
    
    # Sanctions exposure (degree-2 network check)
    sanctions_query = f"""
    MATCH (e:{entity_type} {{name: $entity_name}})-[]->(lc:LetterOfCredit)
          -[]-(counterparty)
          -[]-(lc2:LetterOfCredit)
          -[]-(sanctioned:Entity)
    WHERE sanctioned.sanctions_match = true
    RETURN count(DISTINCT sanctioned) as sanctions_count
    """
    
    sanctions_result = tx.run(sanctions_query, entity_name=entity_name)
    sanctions_record = sanctions_result.single()
    sanctions_count = sanctions_record['sanctions_count'] if sanctions_record else 0
    
    return {
        'counterparty_diversity': round(diversity, 3),
        'high_risk_country_exposure': round(high_risk_exposure, 3),
        'sanctions_exposure': int(sanctions_count)
    }


def _get_document_features(tx, entity_name: str, entity_type: str, lookback_days: int) -> Dict:
    """Extract document quality features."""
    
    query = f"""
    MATCH (e:{entity_type} {{name: $entity_name}})-[]->(lc:LetterOfCredit)
    WHERE lc.issue_date >= date() - duration({{days: $lookback_days}})
    OPTIONAL MATCH (lc)-[:REFERENCES]->(inv:CommercialInvoice)
    OPTIONAL MATCH (lc)-[:SHIPPED_VIA]->(bl:BillOfLading)
    OPTIONAL MATCH (lc)-[:PACKED_IN]->(pl:PackingList)
    WITH lc, 
         CASE WHEN inv IS NOT NULL THEN 1 ELSE 0 END as has_inv,
         CASE WHEN bl IS NOT NULL THEN 1 ELSE 0 END as has_bl,
         CASE WHEN pl IS NOT NULL THEN 1 ELSE 0 END as has_pl
    RETURN 
        count(lc) as total_lcs,
        sum(CASE WHEN has_inv + has_bl + has_pl = 3 THEN 1 ELSE 0 END) as complete_docs,
        sum(CASE WHEN lc.amendments > 0 THEN 1 ELSE 0 END) as amended_lcs,
        sum(CASE WHEN lc.fraud_flag = true THEN 1 ELSE 0 END) as fraud_count
    """
    
    result = tx.run(query, entity_name=entity_name, lookback_days=lookback_days)
    record = result.single()
    
    if not record or record['total_lcs'] == 0:
        return {
            'doc_completeness': 0.5,
            'amendment_rate': 0.3,
            'fraud_flags': 0
        }
    
    total = record['total_lcs']
    completeness = (record['complete_docs'] or 0) / total
    amendment_rate = (record['amended_lcs'] or 0) / total
    fraud_flags = record['fraud_count'] or 0
    
    return {
        'doc_completeness': round(completeness, 3),
        'amendment_rate': round(amendment_rate, 3),
        'fraud_flags': int(fraud_flags)
    }


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Test feature extraction
    features = extract_entity_features(
        entity_name="HSBC Hong Kong",
        entity_type="Buyer",
        lookback_days=90
    )
    
    print("\nExtracted Features:")
    for feature, value in features.items():
        print(f"  {feature:30s}: {value}")
