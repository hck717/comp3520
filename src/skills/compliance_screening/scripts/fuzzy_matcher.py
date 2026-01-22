"""Fuzzy Matching Utilities using RapidFuzz"""
from typing import List, Tuple, Optional
from rapidfuzz import fuzz, process
import logging

from .config import config

logger = logging.getLogger(__name__)

def normalize_name(name: str) -> str:
    """
    Normalize entity name for matching.
    
    Args:
        name: Raw entity name
    
    Returns:
        Normalized name (uppercase, alphanumeric + spaces)
    """
    if not name:
        return ""
    
    # Uppercase
    name = name.upper()
    
    # Remove common suffixes
    suffixes = [" LTD", " LIMITED", " INC", " CORP", " CORPORATION", 
                " LLC", " CO", " COMPANY", " PTE", " GMBH"]
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)]
    
    # Remove special characters (keep alphanumeric + spaces)
    name = ''.join(c if c.isalnum() or c.isspace() else ' ' for c in name)
    
    # Collapse multiple spaces
    name = ' '.join(name.split())
    
    return name.strip()

def fuzzy_match_sanctions(
    query_name: str,
    sanctions_list: List[dict],
    threshold: float = None
) -> Optional[Tuple[dict, float]]:
    """
    Fuzzy match query name against sanctions list.
    
    Args:
        query_name: Name to screen
        sanctions_list: List of dicts with 'name' field
        threshold: Match score threshold (0-100), defaults to config
    
    Returns:
        (matched_entity_dict, score) or None if no match
    """
    if threshold is None:
        threshold = config.FUZZY_THRESHOLD * 100  # Convert 0.85 -> 85
    
    # Normalize query name
    normalized_query = normalize_name(query_name)
    
    if not normalized_query:
        return None
    
    # Prepare sanctions names
    sanctions_names = [normalize_name(s.get("name", "")) for s in sanctions_list]
    
    # Choose algorithm
    if config.FUZZY_ALGORITHM == "ratio":
        scorer = fuzz.ratio
    elif config.FUZZY_ALGORITHM == "partial_ratio":
        scorer = fuzz.partial_ratio
    else:  # token_sort_ratio
        scorer = fuzz.token_sort_ratio
    
    # Find best match
    result = process.extractOne(
        normalized_query,
        sanctions_names,
        scorer=scorer,
        score_cutoff=threshold
    )
    
    if result is None:
        return None
    
    matched_name, score, index = result
    matched_entity = sanctions_list[index]
    
    logger.info(f"Fuzzy match: '{query_name}' -> '{matched_entity['name']}' (score: {score:.1f})")
    
    return matched_entity, score / 100.0  # Return score as 0-1

def batch_fuzzy_match(
    query_names: List[str],
    sanctions_list: List[dict],
    threshold: float = None
) -> List[Optional[Tuple[dict, float]]]:
    """
    Batch fuzzy matching.
    
    Args:
        query_names: List of names to screen
        sanctions_list: List of sanctions entities
        threshold: Match threshold
    
    Returns:
        List of (matched_entity, score) or None for each query
    """
    return [fuzzy_match_sanctions(name, sanctions_list, threshold) for name in query_names]
