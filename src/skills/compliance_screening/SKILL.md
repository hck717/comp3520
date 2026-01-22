# Compliance Screening Skill

## Skill Purpose
Automated compliance screening for trade finance entities against OFAC, UN, and EU sanctions lists with exact and fuzzy matching capabilities.

## When to Use This Skill
- Screening new buyers, sellers, or banks before onboarding
- Real-time transaction monitoring for sanctions exposure
- Periodic re-screening of existing entities (quarterly compliance)
- Regulatory reporting (OFAC 314(a) requests)

## Capabilities
1. **Exact Name Matching**: Fast O(1) lookup against sanctions database
2. **Fuzzy Matching**: RapidFuzz >85% threshold for name variations
3. **Country Risk Scoring**: ISO 3166 country codes mapped to risk levels
4. **Network Traversal**: Check if entity transacts with sanctioned parties

## Performance Requirements
- **Latency**: <500ms per entity screening
- **Accuracy**: >95% precision (minimize false positives)
- **Throughput**: 100+ entities/second batch screening

---

## API Reference

### 1. Screen Entity (Single)
```python
from skills.compliance_screening.scripts.screen_entity import screen_entity

result = screen_entity(
    entity_name="Acme Trading Corp",
    entity_country="HK",
    entity_type="Buyer"
)

# Returns:
{
    "entity_name": "Acme Trading Corp",
    "sanctions_match": True,
    "match_type": "fuzzy",
    "matched_entity": "ACME TRADE CORPORATION",
    "match_score": 0.92,
    "sanctions_list": "OFAC_SDN",
    "country_risk": "low",
    "network_exposure": False,
    "recommendation": "BLOCK"
}
```

### 2. Batch Screen Entities
```python
from skills.compliance_screening.scripts.batch_screen import batch_screen

entities = [
    {"name": "Company A", "country": "US"},
    {"name": "Company B", "country": "IR"}
]

results = batch_screen(entities)
# Returns: List[Dict] with screening results
```

### 3. Country Risk Scoring
```python
from skills.compliance_screening.scripts.country_risk import get_country_risk

risk = get_country_risk("IR")  # Iran
# Returns: {"country": "IR", "risk_level": "high", "risk_score": 9}
```

---

## Available Scripts

### `screen_entity.py`
Primary screening function with exact + fuzzy matching.

**Usage:**
```python
result = screen_entity(
    entity_name: str,
    entity_country: str,
    entity_type: str = "Entity",
    fuzzy_threshold: float = 0.85
)
```

**Process:**
1. Normalize entity name (uppercase, remove punctuation)
2. Exact match against Neo4j sanctions nodes
3. If no match, fuzzy match with RapidFuzz
4. Apply country risk scoring
5. Check network exposure via Neo4j graph traversal

### `batch_screen.py`
Batch screening with parallel processing.

**Usage:**
```python
results = batch_screen(
    entities: List[Dict],
    max_workers: int = 10
)
```

### `country_risk.py`
Country risk scoring based on FATF, Transparency International, US State Dept.

**Risk Levels:**
- **High (8-10)**: Iran, North Korea, Syria, Venezuela, Russia
- **Medium (4-7)**: Afghanistan, Myanmar, Pakistan, Belarus
- **Low (1-3)**: US, UK, EU, HK, SG, JP

### `fuzzy_matcher.py`
Fuzzy matching utilities using RapidFuzz.

**Algorithms:**
- `fuzz.ratio()`: Standard Levenshtein
- `fuzz.partial_ratio()`: Substring matching
- `fuzz.token_sort_ratio()`: Word order invariant

---

## Integration with Neo4j

### Required Cypher Queries

**1. Exact Match:**
```cypher
MATCH (s:SanctionEntity {name: $normalized_name})
RETURN s.name, s.list_type, s.program
```

**2. Fuzzy Match (retrieve all for scoring):**
```cypher
MATCH (s:SanctionEntity)
WHERE s.list_type = $list_type
RETURN s.name, s.list_type, s.program, s.country
```

**3. Network Exposure:**
```cypher
MATCH (e:Entity {name: $entity_name})-[:ISSUED_LC|BENEFICIARY*1..2]-(connected)
      -[:SCREENED_AGAINST]->(s:SanctionEntity)
RETURN DISTINCT s.name, s.list_type
```

---

## Configuration

### Environment Variables
```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
FUZZY_THRESHOLD=0.85
COUNTRY_RISK_CACHE_TTL=86400  # 24 hours
```

### Performance Tuning
```python
# In scripts/config.py
BATCH_SIZE = 500
MAX_WORKERS = 10
CACHE_ENABLED = True
FUZZY_ALGORITHM = "token_sort_ratio"  # vs ratio, partial_ratio
```

---

## Testing

### Unit Tests
```bash
pytest src/skills/compliance_screening/scripts/test_screen_entity.py
pytest src/skills/compliance_screening/scripts/test_fuzzy_matcher.py
```

### Integration Tests
```bash
# Test against live Neo4j
pytest src/skills/compliance_screening/scripts/test_integration.py
```

### Load Testing
```bash
# Screen 1,000 entities in <5 seconds
python src/skills/compliance_screening/scripts/benchmark.py
```

---

## Expected Output Examples

### Clean Entity (PASS)
```json
{
  "entity_name": "Hong Kong Trading Co Ltd",
  "sanctions_match": false,
  "country_risk": "low",
  "country_risk_score": 2,
  "network_exposure": false,
  "recommendation": "APPROVE",
  "screening_time_ms": 87
}
```

### Sanctioned Entity (BLOCK)
```json
{
  "entity_name": "Iran Petrochemical Company",
  "sanctions_match": true,
  "match_type": "exact",
  "matched_entity": "IRAN PETROCHEMICAL COMPANY",
  "match_score": 1.0,
  "sanctions_list": "OFAC_SDN",
  "program": "IRAN",
  "country_risk": "high",
  "country_risk_score": 10,
  "recommendation": "BLOCK",
  "screening_time_ms": 123
}
```

### Fuzzy Match (REVIEW)
```json
{
  "entity_name": "Acme Trade Corp",
  "sanctions_match": true,
  "match_type": "fuzzy",
  "matched_entity": "ACME TRADING CORPORATION",
  "match_score": 0.89,
  "sanctions_list": "EU_FSF",
  "country_risk": "medium",
  "country_risk_score": 5,
  "recommendation": "REVIEW",
  "screening_time_ms": 234
}
```

---

## Error Handling

```python
try:
    result = screen_entity("Test Corp", "US")
except Neo4jConnectionError:
    # Fallback to cached sanctions list
    logger.error("Neo4j unavailable, using cached list")
except FuzzyMatchTimeout:
    # Skip fuzzy matching if >500ms
    logger.warning("Fuzzy match timeout, exact match only")
```

---

## Maintenance

### Update Sanctions Lists
```bash
# Download latest OFAC SDN
python src/data_generation/download_ofac_sdn.py

# Refresh Neo4j sanctions nodes
python src/skills/compliance_screening/scripts/refresh_sanctions.py
```

### Audit Logs
All screening results logged to `logs/compliance_screening.jsonl`:
```json
{"timestamp": "2026-01-22T14:05:23Z", "entity": "Test Corp", "result": "PASS", "latency_ms": 98}
```

---

## Dependencies

```python
# requirements.txt additions
rapidfuzz>=3.6.0
neo4j>=5.16.0
pytest>=7.4.0
```

---

## Future Enhancements
- [ ] SWIFT BIC code validation
- [ ] LEI (Legal Entity Identifier) screening
- [ ] Real-time OFAC API integration
- [ ] ML-based false positive reduction
- [ ] Multi-language name matching (Arabic, Cyrillic)

---

## References
- [OFAC SDN List](https://sanctionssearch.ofac.treas.gov/)
- [UN Security Council Sanctions](https://www.un.org/securitycouncil/sanctions/information)
- [EU Financial Sanctions](https://webgate.ec.europa.eu/fsd/fsf)
- [RapidFuzz Documentation](https://maxbachmann.github.io/RapidFuzz/)
