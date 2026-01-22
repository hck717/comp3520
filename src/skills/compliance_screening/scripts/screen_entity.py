"""Main Entity Screening Function"""
import time
from typing import Dict, Optional
import logging
from neo4j import GraphDatabase

from .config import config
from .country_risk import get_country_risk
from .fuzzy_matcher import normalize_name, fuzzy_match_sanctions

logger = logging.getLogger(__name__)

def screen_entity(
    entity_name: str,
    entity_country: str,
    entity_type: str = "Entity",
    fuzzy_threshold: float = None,
    check_network: bool = True
) -> Dict:
    """
    Screen an entity against sanctions lists and country risk.
    
    Args:
        entity_name: Name of entity to screen
        entity_country: ISO 3166 country code
        entity_type: "Buyer", "Seller", "Bank", or "Entity"
        fuzzy_threshold: Custom threshold (defaults to config)
        check_network: Whether to check network exposure
    
    Returns:
        Screening result dict
    """
    start_time = time.time()
    
    if fuzzy_threshold is None:
        fuzzy_threshold = config.FUZZY_THRESHOLD
    
    # Initialize result
    result = {
        "entity_name": entity_name,
        "entity_country": entity_country,
        "entity_type": entity_type,
        "sanctions_match": False,
        "match_type": None,
        "matched_entity": None,
        "match_score": None,
        "sanctions_list": None,
        "program": None,
        "country_risk": None,
        "country_risk_score": None,
        "network_exposure": False,
        "recommendation": "APPROVE",
        "screening_time_ms": None
    }
    
    # Connect to Neo4j
    driver = GraphDatabase.driver(
        config.NEO4J_URI,
        auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
    )
    
    try:
        with driver.session() as session:
            # Step 1: Exact match
            normalized_name = normalize_name(entity_name)
            exact_match = session.run("""
                MATCH (s:SanctionEntity)
                WHERE toUpper(s.name) = $name
                RETURN s.name AS name, s.list_type AS list_type, 
                       s.program AS program
                LIMIT 1
            """, name=normalized_name).single()
            
            if exact_match:
                result.update({
                    "sanctions_match": True,
                    "match_type": "exact",
                    "matched_entity": exact_match["name"],
                    "match_score": 1.0,
                    "sanctions_list": exact_match["list_type"],
                    "program": exact_match["program"],
                    "recommendation": "BLOCK"
                })
            else:
                # Step 2: Fuzzy match
                sanctions_records = session.run("""
                    MATCH (s:SanctionEntity)
                    RETURN s.name AS name, s.list_type AS list_type,
                           s.program AS program, s.country AS country
                """).data()
                
                fuzzy_result = fuzzy_match_sanctions(
                    entity_name,
                    sanctions_records,
                    fuzzy_threshold
                )
                
                if fuzzy_result:
                    matched_entity, score = fuzzy_result
                    result.update({
                        "sanctions_match": True,
                        "match_type": "fuzzy",
                        "matched_entity": matched_entity["name"],
                        "match_score": score,
                        "sanctions_list": matched_entity["list_type"],
                        "program": matched_entity.get("program"),
                        "recommendation": "REVIEW" if score < 0.95 else "BLOCK"
                    })
            
            # Step 3: Network exposure (if entity exists in graph)
            if check_network and not result["sanctions_match"]:
                network_match = session.run("""
                    MATCH (e:Entity {name: $entity_name})
                          -[:ISSUED_LC|BENEFICIARY*1..2]-(connected)
                          -[:SCREENED_AGAINST]->(s:SanctionEntity)
                    RETURN DISTINCT s.name AS name, s.list_type AS list_type
                    LIMIT 1
                """, entity_name=entity_name).single()
                
                if network_match:
                    result["network_exposure"] = True
                    result["recommendation"] = "REVIEW"
            
            # Step 4: Country risk
            country_risk_info = get_country_risk(entity_country)
            result["country_risk"] = country_risk_info["risk_level"]
            result["country_risk_score"] = country_risk_info["risk_score"]
            
            # Upgrade recommendation if high-risk country
            if country_risk_info["risk_score"] >= 8 and result["recommendation"] == "APPROVE":
                result["recommendation"] = "REVIEW"
    
    finally:
        driver.close()
    
    # Calculate screening time
    end_time = time.time()
    result["screening_time_ms"] = int((end_time - start_time) * 1000)
    
    return result
