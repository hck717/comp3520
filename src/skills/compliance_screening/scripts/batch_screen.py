"""Batch Entity Screening with Parallel Processing"""
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from tqdm import tqdm

from .screen_entity import screen_entity
from .config import config

logger = logging.getLogger(__name__)

def batch_screen(
    entities: List[Dict],
    max_workers: int = None,
    show_progress: bool = True
) -> List[Dict]:
    """
    Screen multiple entities in parallel.
    
    Args:
        entities: List of dicts with 'name', 'country', and optionally 'type'
        max_workers: Number of parallel workers (defaults to config)
        show_progress: Whether to show progress bar
    
    Returns:
        List of screening results
    """
    if max_workers is None:
        max_workers = config.MAX_WORKERS
    
    results = []
    
    # Prepare screening tasks
    def screen_task(entity):
        return screen_entity(
            entity_name=entity["name"],
            entity_country=entity["country"],
            entity_type=entity.get("type", "Entity")
        )
    
    # Execute in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(screen_task, entity): entity for entity in entities}
        
        iterator = as_completed(futures)
        if show_progress:
            iterator = tqdm(iterator, total=len(entities), desc="Screening entities")
        
        for future in iterator:
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                entity = futures[future]
                logger.error(f"Failed to screen {entity['name']}: {e}")
                results.append({
                    "entity_name": entity["name"],
                    "error": str(e),
                    "recommendation": "ERROR"
                })
    
    # Generate summary
    total = len(results)
    blocked = sum(1 for r in results if r.get("recommendation") == "BLOCK")
    review = sum(1 for r in results if r.get("recommendation") == "REVIEW")
    approved = sum(1 for r in results if r.get("recommendation") == "APPROVE")
    
    logger.info(f"Batch screening complete: {total} entities")
    logger.info(f"  BLOCKED: {blocked} ({blocked/total*100:.1f}%)")
    logger.info(f"  REVIEW: {review} ({review/total*100:.1f}%)")
    logger.info(f"  APPROVED: {approved} ({approved/total*100:.1f}%)")
    
    return results
