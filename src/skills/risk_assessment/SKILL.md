# Risk Assessment Skill

## Skill Purpose
Dynamic credit scoring and risk assessment for trade finance entities using behavioral and network features extracted from Neo4j transaction history.

## When to Use This Skill
- Credit limit decisions for new buyers/sellers
- Quarterly credit review for existing clients
- LC issuance approval workflows
- Portfolio risk monitoring and stress testing

## Capabilities
1. **Feature Engineering**: Extract 12+ features from Neo4j graph
2. **XGBoost Scoring**: ML-based credit risk prediction
3. **Behavioral Analysis**: 90-day transaction history patterns
4. **Network Risk**: Exposure to high-risk counterparties

## Performance Requirements
- **Model AUC-ROC**: >0.85 on validation set
- **Inference Latency**: <100ms per entity
- **Feature Extraction**: <500ms from Neo4j
- **Training Time**: <5 minutes on 1,000 samples

---

## Feature Set (12 Dimensions)

### Behavioral Features (6)
1. **transaction_count**: Number of LCs in last 90 days
2. **total_exposure**: Sum of LC amounts (normalized by median)
3. **avg_lc_amount**: Average LC value
4. **discrepancy_rate**: % of LCs with invoice/LC amount mismatch >10%
5. **late_shipment_rate**: % of B/Ls shipped late
6. **payment_delay_avg**: Average days between B/L date and payment

### Network Features (3)
7. **counterparty_diversity**: Unique sellers/buyers ratio
8. **high_risk_country_exposure**: % of transactions with risk score ≥7
9. **sanctions_exposure**: Degree-2 network distance to sanctioned entities

### Document Quality Features (3)
10. **doc_completeness**: % of LCs with full doc chain (Invoice+B/L+PL)
11. **amendment_rate**: % of LCs requiring amendments
12. **fraud_flags**: Count of manual fraud flags

---

## API Reference

### 1. Train Model
```python
from skills.risk_assessment.scripts.train_model import train_xgboost_model

metrics = train_xgboost_model(
    training_data_path="data/processed/training_data.csv",
    model_output_path="models/risk_model.pkl",
    test_size=0.2
)

# Returns:
{
    "auc_roc": 0.89,
    "precision": 0.85,
    "recall": 0.82,
    "f1_score": 0.83,
    "train_samples": 800,
    "test_samples": 200
}
```

### 2. Score Single Entity
```python
from skills.risk_assessment.scripts.score_entity import score_entity

score = score_entity(
    entity_name="Acme Trading Corp",
    entity_type="Buyer",
    model_path="models/risk_model.pkl"
)

# Returns:
{
    "entity_name": "Acme Trading Corp",
    "risk_score": 0.72,  # 0-1, higher = riskier
    "risk_category": "medium",
    "credit_limit_usd": 500000,
    "features": {
        "transaction_count": 15,
        "discrepancy_rate": 0.13,
        "high_risk_country_exposure": 0.20,
        ...
    },
    "recommendation": "APPROVE_WITH_CONDITIONS"
}
```

### 3. Batch Scoring
```python
from skills.risk_assessment.scripts.batch_score import batch_score_entities

entities = ["Company A", "Company B", "Company C"]
scores = batch_score_entities(entities, entity_type="Buyer")

# Returns: List[Dict] with scores for each entity
```

---

## Available Scripts

### `extract_features.py`
Extract features from Neo4j for model training or inference.

**Usage:**
```python
from skills.risk_assessment.scripts.extract_features import extract_entity_features

features = extract_entity_features(
    entity_name="Acme Corp",
    entity_type="Buyer",
    lookback_days=90
)
```

**Cypher Queries Used:**
```cypher
// Get transaction history
MATCH (e:Buyer {name: $entity_name})-[:ISSUED_LC]->(lc:LetterOfCredit)
WHERE lc.issue_date >= date() - duration({days: 90})
RETURN lc

// Get discrepancy rate
MATCH (e:Buyer {name: $entity_name})-[:ISSUED_LC]->(lc:LetterOfCredit)
      -[:REFERENCES]->(inv:CommercialInvoice)
WHERE inv.discrepancy_flag = true
RETURN count(inv) * 1.0 / count(lc) AS discrepancy_rate

// Get network exposure to high-risk countries
MATCH (e:Buyer {name: $entity_name})-[:ISSUED_LC]->(lc:LetterOfCredit)
      -[:BENEFICIARY]->(seller:Seller)
WHERE seller.country IN ['IR', 'KP', 'SY', 'VE', 'RU']
RETURN count(lc) * 1.0 / count(DISTINCT lc) AS high_risk_exposure
```

### `train_model.py`
Train XGBoost credit risk model.

**Training Process:**
1. Load labeled dataset (800 clean + 200 high-risk)
2. Extract features for all entities
3. Train XGBoost classifier with hyperparameter tuning
4. Validate on 20% holdout set
5. Save model as `risk_model.pkl`

**Hyperparameters:**
```python
xgb_params = {
    'max_depth': 6,
    'learning_rate': 0.1,
    'n_estimators': 100,
    'objective': 'binary:logistic',
    'eval_metric': 'auc',
    'scale_pos_weight': 4  # Handle class imbalance
}
```

### `score_entity.py`
Score single entity using trained model.

**Risk Categories:**
- **Low Risk (0.0-0.3)**: Credit limit = $2M+
- **Medium Risk (0.3-0.7)**: Credit limit = $500K-$2M
- **High Risk (0.7-1.0)**: Credit limit = $0-$500K, require collateral

### `batch_score.py`
Batch scoring with parallel processing.

---

## Training Data Generation

### `generate_training_labels.py`
Create synthetic labels for model training.

**Labeling Rules:**
```python
# High Risk = 1 if:
- discrepancy_rate > 0.20 OR
- late_shipment_rate > 0.30 OR
- sanctions_exposure > 0 OR
- fraud_flags > 2 OR
- high_risk_country_exposure > 0.50

# Clean = 0 otherwise
```

**Usage:**
```bash
python src/skills/risk_assessment/scripts/generate_training_labels.py
# Output: data/processed/training_data.csv (1,000 rows, 13 columns)
```

---

## Model Training Workflow

```bash
# Step 1: Extract features and generate labels
python src/skills/risk_assessment/scripts/generate_training_labels.py

# Step 2: Train XGBoost model
python src/skills/risk_assessment/scripts/train_model.py

# Step 3: Validate model
python src/skills/risk_assessment/scripts/validate_model.py

# Expected output:
# ✅ Model trained: AUC-ROC = 0.89
# ✅ Saved to: models/risk_model.pkl
```

---

## Feature Importance (Expected)

```python
# Top 5 features by SHAP values:
1. discrepancy_rate          (0.18)
2. high_risk_country_exposure (0.16)
3. late_shipment_rate        (0.14)
4. sanctions_exposure        (0.12)
5. transaction_count         (0.10)
```

---

## Integration Example

```python
from skills.compliance_screening.scripts.screen_entity import screen_entity
from skills.risk_assessment.scripts.score_entity import score_entity

# Step 1: Compliance screening
screening = screen_entity("Acme Corp", "HK", "Buyer")

if screening["recommendation"] != "BLOCK":
    # Step 2: Risk scoring
    risk = score_entity("Acme Corp", "Buyer")
    
    # Step 3: Make decision
    if risk["risk_score"] < 0.3:
        print(f"APPROVED: Credit limit ${risk['credit_limit_usd']:,}")
    elif risk["risk_score"] < 0.7:
        print(f"APPROVED WITH CONDITIONS: Require 50% collateral")
    else:
        print(f"DECLINED: Risk score too high ({risk['risk_score']:.2f})")
```

---

## Configuration

### Environment Variables
```bash
RISK_MODEL_PATH=models/risk_model.pkl
FEATURE_LOOKBACK_DAYS=90
MODEL_CONFIDENCE_THRESHOLD=0.7
CREDIT_LIMIT_LOW_RISK=2000000
CREDIT_LIMIT_MEDIUM_RISK=500000
```

### Model Retraining Schedule
- **Frequency**: Monthly
- **Trigger**: >500 new transactions since last training
- **Validation**: AUC-ROC must stay >0.85

---

## Testing

```bash
# Unit tests
pytest src/skills/risk_assessment/scripts/test_extract_features.py
pytest src/skills/risk_assessment/scripts/test_score_entity.py

# Integration test
pytest src/skills/risk_assessment/scripts/test_integration.py

# Model performance test
python src/skills/risk_assessment/scripts/validate_model.py
```

---

## Expected Outputs

### Training Output
```
============================================================
  XGBOOST RISK MODEL TRAINING
============================================================

📂 Loading training data...
  ✅ 1,000 entities loaded (800 clean, 200 high-risk)

🔧 Extracting features from Neo4j...
  [████████████████████] 1000/1000 entities (90s)

🤖 Training XGBoost model...
  Epoch 100/100: AUC-ROC = 0.89, loss = 0.23

📊 Validation Results:
  AUC-ROC:   0.89
  Precision: 0.85
  Recall:    0.82
  F1 Score:  0.83

💾 Model saved: models/risk_model.pkl

🎉 TRAINING COMPLETE!
```

### Scoring Output
```json
{
  "entity_name": "Hong Kong Trading Co Ltd",
  "entity_type": "Buyer",
  "risk_score": 0.18,
  "risk_category": "low",
  "credit_limit_usd": 2500000,
  "recommendation": "APPROVE",
  "features": {
    "transaction_count": 45,
    "total_exposure": 12500000,
    "avg_lc_amount": 277778,
    "discrepancy_rate": 0.02,
    "late_shipment_rate": 0.04,
    "payment_delay_avg": 2.1,
    "counterparty_diversity": 0.82,
    "high_risk_country_exposure": 0.00,
    "sanctions_exposure": 0,
    "doc_completeness": 0.98,
    "amendment_rate": 0.07,
    "fraud_flags": 0
  },
  "model_version": "v1.0",
  "scored_at": "2026-01-22T14:15:30Z"
}
```

---

## Dependencies

```python
# requirements.txt additions
xgboost>=2.0.0
scikit-learn>=1.3.0
shap>=0.44.0  # For feature importance
imbalanced-learn>=0.12.0  # For SMOTE
```

---

## Future Enhancements
- [ ] LSTM for time-series risk forecasting
- [ ] Explainable AI with SHAP force plots
- [ ] Real-time model retraining (online learning)
- [ ] Ensemble models (XGBoost + Random Forest + Neural Net)
- [ ] Regulatory stress testing scenarios

---

## References
- [XGBoost Documentation](https://xgboost.readthedocs.io/)
- [SHAP for Model Explainability](https://shap.readthedocs.io/)
- [Basel III Credit Risk Framework](https://www.bis.org/bcbs/publ/d424.pdf)
