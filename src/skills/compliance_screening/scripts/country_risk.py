"""Country Risk Scoring Module"""
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)

# Country Risk Scores (1-10, 10 = highest risk)
# Based on FATF, Transparency International, US State Dept
COUNTRY_RISK_SCORES = {
    # High Risk (8-10)
    "IR": (10, "high"),  # Iran
    "KP": (10, "high"),  # North Korea
    "SY": (10, "high"),  # Syria
    "VE": (9, "high"),   # Venezuela
    "RU": (9, "high"),   # Russia
    "BY": (8, "high"),   # Belarus
    "MM": (8, "high"),   # Myanmar
    "AF": (8, "high"),   # Afghanistan
    
    # Medium-High Risk (6-7)
    "PK": (7, "medium"), # Pakistan
    "YE": (7, "medium"), # Yemen
    "IQ": (7, "medium"), # Iraq
    "LY": (7, "medium"), # Libya
    "SO": (7, "medium"), # Somalia
    "SD": (6, "medium"), # Sudan
    "CD": (6, "medium"), # Congo (DRC)
    
    # Medium Risk (4-5)
    "TH": (5, "medium"), # Thailand
    "PH": (5, "medium"), # Philippines
    "BD": (5, "medium"), # Bangladesh
    "NG": (5, "medium"), # Nigeria
    "KE": (4, "medium"), # Kenya
    "IN": (4, "medium"), # India
    "TR": (4, "medium"), # Turkey
    "BR": (4, "medium"), # Brazil
    "ZA": (4, "medium"), # South Africa
    
    # Low-Medium Risk (3)
    "CN": (3, "low"),    # China
    "MX": (3, "low"),    # Mexico
    "ID": (3, "low"),    # Indonesia
    "AE": (3, "low"),    # UAE
    "SA": (3, "low"),    # Saudi Arabia
    
    # Low Risk (1-2)
    "US": (1, "low"),    # United States
    "GB": (1, "low"),    # United Kingdom
    "DE": (1, "low"),    # Germany
    "FR": (1, "low"),    # France
    "JP": (1, "low"),    # Japan
    "SG": (1, "low"),    # Singapore
    "HK": (1, "low"),    # Hong Kong
    "AU": (1, "low"),    # Australia
    "CA": (1, "low"),    # Canada
    "CH": (1, "low"),    # Switzerland
    "NL": (1, "low"),    # Netherlands
    "SE": (1, "low"),    # Sweden
    "NO": (1, "low"),    # Norway
    "DK": (1, "low"),    # Denmark
    "NZ": (1, "low"),    # New Zealand
    "KR": (2, "low"),    # South Korea
    "TW": (2, "low"),    # Taiwan
    "MY": (2, "low"),    # Malaysia
}

def get_country_risk(country_code: str) -> Dict[str, any]:
    """
    Get risk score and level for a country.
    
    Args:
        country_code: ISO 3166-1 alpha-2 country code (e.g., "US", "HK")
    
    Returns:
        Dict with country, risk_score (1-10), and risk_level (low/medium/high)
    """
    country_code = country_code.upper()
    
    if country_code not in COUNTRY_RISK_SCORES:
        # Unknown country defaults to medium risk
        logger.warning(f"Unknown country code: {country_code}, defaulting to medium risk")
        return {
            "country": country_code,
            "risk_score": 5,
            "risk_level": "medium",
            "known": False
        }
    
    score, level = COUNTRY_RISK_SCORES[country_code]
    return {
        "country": country_code,
        "risk_score": score,
        "risk_level": level,
        "known": True
    }

def is_high_risk_country(country_code: str) -> bool:
    """Check if country is high risk (score >= 8)"""
    risk = get_country_risk(country_code)
    return risk["risk_score"] >= 8

def get_country_risk_batch(country_codes: list) -> Dict[str, Dict]:
    """Batch country risk lookup"""
    return {code: get_country_risk(code) for code in country_codes}
