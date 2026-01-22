"""Compliance Screening Configuration"""
import os
from dataclasses import dataclass

@dataclass
class ComplianceConfig:
    """Configuration for compliance screening"""
    
    # Neo4j Connection
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "password")
    
    # Screening Thresholds
    FUZZY_THRESHOLD: float = float(os.getenv("FUZZY_THRESHOLD", "0.85"))
    HIGH_RISK_COUNTRY_SCORE: int = 7
    MEDIUM_RISK_COUNTRY_SCORE: int = 4
    
    # Performance
    BATCH_SIZE: int = 500
    MAX_WORKERS: int = 10
    CACHE_ENABLED: bool = True
    CACHE_TTL: int = 86400  # 24 hours
    TIMEOUT_MS: int = 500
    
    # Fuzzy Matching Algorithm
    FUZZY_ALGORITHM: str = "token_sort_ratio"  # or "ratio", "partial_ratio"

config = ComplianceConfig()
