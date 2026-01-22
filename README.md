# Sentinel-Zero: AI-Powered Trade Finance Intelligence Platform

Sentinel-Zero is a self-improving, privacy-first trade finance intelligence platform that transforms fragmented trade documents (Letter of Credit, Bill of Lading, Commercial Invoice, Packing List) into an intelligent knowledge graph with real-time analytics, predictive insights, automated anomaly detection, compliance screening, and dynamic risk assessment.

## Core Capabilities

- **Real-time Transaction Monitoring**: Live LC processing with interactive graph visualization
- **Compliance & Sanctions Screening**: Automated screening against OFAC, UN, EU sanctions lists with fuzzy matching
- **Dynamic Risk Assessment**: XGBoost credit scoring using 12 behavioral + network features
- **Predictive Analytics**: Prophet LC forecasting + LSTM port delay prediction
- **Quantum Anomaly Detection**: 4-qubit VQC using PennyLane (3.9% better F1 than classical)
- **Self-Improving AI Agent**: LangGraph-based assistant with modular skills architecture
- **Privacy-First Architecture**: Air-gapped design keeping sensitive data local

---

## 🎯 Agent Skills Architecture

Following **Anthropic's Agent Skills framework**, Sentinel-Zero implements professional capabilities as self-contained skill modules. Each skill is a folder containing:
- `SKILL.md`: Documentation (when to use, API reference, examples)
- `scripts/`: Executable Python scripts for the skill
- `reference.md`: (Optional) Extended technical references

### Available Skills (Week 2 Complete ✅)

| Skill | Purpose | Key Metrics |
|-------|---------|-------------|
| **[Compliance Screening](src/skills/compliance_screening/SKILL.md)** | OFAC/UN/EU sanctions screening with fuzzy matching | <500ms latency, >95% precision |
| **[Risk Assessment](src/skills/risk_assessment/SKILL.md)** | XGBoost credit scoring using Neo4j features | >0.85 AUC-ROC, 12D feature space |
| **[Predictive Analytics](src/skills/predictive_analytics/SKILL.md)** | Prophet forecasting + LSTM delays + Isolation Forest | <15% MAE, <3 days RMSE |
| **[Quantum Anomaly](src/skills/quantum_anomaly/SKILL.md)** | 4-qubit VQC anomaly detection | F1=0.79 (+3.9% vs classical) |

---

## 🚀 Quick Start Setup

### Prerequisites

- **Python 3.10+** (macOS/Linux/Windows)
- **Docker Desktop** (for Neo4j database)
- **Ollama** (for local LLM) - [Download here](https://ollama.com)
- **Kaggle Account** (for downloading datasets - optional)

---

## 📦 Step 1: Clone Repository & Setup Environment

```bash
# Clone the repository
git clone https://github.com/hck717/comp3520.git
cd comp3520

# Create virtual environment (IMPORTANT for Mac users)
python3 -m venv venv

# Activate virtual environment
# On Mac/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# You should see (venv) in your terminal prompt

# Upgrade pip
pip install --upgrade pip

# Install all dependencies (including ML libraries)
pip install -r requirements.txt
```

### Troubleshooting Virtual Environment

If you see `externally-managed-environment` error on Mac, **you must use a virtual environment**:
```bash
python3 -m venv venv
source venv/bin/activate
# Now pip install will work
```

**Every time you work on the project:**
```bash
cd ~/comp3520
source venv/bin/activate  # Don't forget this!
```

---

## 📊 Step 2: Download Trade Finance Datasets (Optional)

**Note**: The data generation scripts can create synthetic data if you don't have Kaggle datasets.

### Option A: Download from Kaggle Web UI

1. **GlobalTradeSettleNet**:
   - Visit: [https://www.kaggle.com/datasets/ziya07/globaltradesettlenet](https://www.kaggle.com/datasets/ziya07/globaltradesettlenet)
   - Click "Download" and save to `data/raw/`

2. **Cross-Border Trade & Customs Delay**:
   - Visit: [https://www.kaggle.com/datasets/ziya07/cross-border-trade-and-customs-delay-dataset](https://www.kaggle.com/datasets/ziya07/cross-border-trade-and-customs-delay-dataset)
   - Click "Download" and save to `data/raw/`

### Option B: Use Kaggle CLI (Faster)

```bash
# Install Kaggle CLI
pip install kaggle

# Setup API credentials (one-time)
# 1. Go to https://www.kaggle.com/settings
# 2. Click "Create New API Token"
# 3. Save kaggle.json to ~/.kaggle/
mkdir -p ~/.kaggle
mv ~/Downloads/kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json

# Download datasets
kaggle datasets download -d ziya07/globaltradesettlenet -p data/raw/ --unzip
kaggle datasets download -d ziya07/cross-border-trade-and-customs-delay-dataset -p data/raw/ --unzip
```

---

## 🔧 Step 3: Generate Trade Finance Data

```bash
# Make sure virtual environment is activated!
source venv/bin/activate

# Step 1: Generate synthetic sanctions lists (OFAC, UN, EU)
python src/data_generation/generate_sanctions_list.py
# Output: 200 sanctions entities in data/processed/

# Step 2: Enrich Kaggle data with LC/Invoice/B/L/Packing List structure
# If you don't have Kaggle datasets, this will create synthetic data automatically
python src/data_generation/enrich_transactions.py
# Output: 1,000 complete trade finance records in data/processed/transactions.csv
```

**Expected Output:**
```
✅ Generated 200 sanctions entities
   - OFAC SDN: 66 entities
   - UN SC: 68 entities
   - EU FSF: 66 entities

✅ Generated 1,000 complete trade finance records
   - Amount discrepancies: 181 (18.1%)
   - Late shipments: 703 (70.3%)
   - Fraud flags: 47 (4.7%)
```

---

## 🐳 Step 4: Start Neo4j Database

```bash
# Start Neo4j in Docker
docker run -d --name neo4j-sentinel \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  -e NEO4J_PLUGINS='["apoc", "graph-data-science"]' \
  neo4j:5.18.0

# Check if running
docker ps | grep neo4j-sentinel

# If container already exists (stopped), restart it:
docker start neo4j-sentinel
```

**Access Neo4j Browser**: [http://localhost:7474](http://localhost:7474)
- **Username**: `neo4j`
- **Password**: `password`

---

## 📥 Step 5: Ingest Data into Neo4j

```bash
# Run the trade finance ingestion script
python src/ingest_trade_finance.py
```

**Expected Output:**
```
============================================================
  SENTINEL-ZERO TRADE FINANCE INGESTION
============================================================

✅ Connected to Neo4j at bolt://localhost:7687

📂 Loaded 1000 transactions from data/processed/transactions.csv

🔧 Creating constraints and indexes...
✅ Constraints and indexes created

📊 Ingesting entities (Buyers, Sellers, Banks)...
  ✅ 200 buyers | ✅ 150 sellers | ✅ 30 banks

📄 Ingesting Letters of Credit...
  ✅ 1000 LCs ingested

🧾 Ingesting Commercial Invoices...
  ✅ 1000 invoices ingested (181 with discrepancies)

🚢 Ingesting Bills of Lading...
  ✅ 1000 B/Ls ingested (703 late shipments)

📦 Ingesting Packing Lists...
  ✅ 1000 packing lists ingested

🚫 Ingesting sanctions lists...
  ✅ 200 sanctions entities loaded
  🔍 Screening entities against sanctions...
  ✅ Found 52 sanctions matches

============================================================
  INGESTION SUMMARY
============================================================
Total Nodes: 4,580
  - Entities: 380 (Buyers: 200, Sellers: 150, Banks: 30)
  - LCs: 1,000 | Invoices: 1,000 | B/Ls: 1,000 | PLs: 1,000
  - Sanctions: 200

Risk Flags:
  - Sanctions Matches: 52
  - Amount Discrepancies: 181
  - Late Shipments: 703
  - Fraud Flags: 47
============================================================

🎉 INGESTION COMPLETE!
```

**Verify in Neo4j Browser**: [http://localhost:7474](http://localhost:7474)

```cypher
// Count all nodes
MATCH (n) RETURN count(n) AS total_nodes;

// Visualize a complete trade finance chain
MATCH path = (buyer:Buyer)-[:ISSUED_LC]->(lc:LetterOfCredit)
             -[:REFERENCES]->(inv:CommercialInvoice)
             -[:BACKED_BY]->(bl:BillOfLading)
             -[:DESCRIBES]->(pl:PackingList)
RETURN path LIMIT 3;
```

---

## 🤖 Step 6: Use Agent Skills

### Skill 1: Compliance Screening

```python
from skills.compliance_screening.scripts import screen_entity

# Screen a buyer against sanctions lists
result = screen_entity(
    entity_name="Acme Trading Corp",
    entity_country="HK",
    entity_type="Buyer"
)

print(f"Sanctions Match: {result['sanctions_match']}")
print(f"Country Risk: {result['country_risk']} ({result['country_risk_score']}/10)")
print(f"Recommendation: {result['recommendation']}")
```

### Skill 2: Risk Assessment

```python
from skills.risk_assessment.scripts import score_entity

# Score an entity's credit risk
score = score_entity(
    entity_name="Acme Trading Corp",
    entity_type="Buyer"
)

print(f"Risk Score: {score['risk_score']:.2f} ({score['risk_category']})")
print(f"Credit Limit: ${score['credit_limit_usd']:,}")
print(f"Recommendation: {score['recommendation']}")
```

### Skill 3: Predictive Analytics

```python
from skills.predictive_analytics.scripts import forecast_lc_volume, predict_port_delay

# Forecast LC volume for next 30 days
forecast = forecast_lc_volume(forecast_days=30)
print(f"Expected LCs next week: {sum([d['lc_count'] for d in forecast['predictions'][:7]])}")

# Predict port delay
delay = predict_port_delay(
    port_of_loading="CNSHA",
    port_of_discharge="USNYC",
    cargo_type="Electronics",
    cargo_volume_cbm=500,
    shipment_date="2026-02-15"
)
print(f"Predicted Delay: {delay['predicted_delay_days']:.1f} days ({delay['risk_level']})")
```

### Skill 4: Quantum Anomaly Detection

```python
from skills.quantum_anomaly.scripts import detect_anomaly_quantum

# Detect anomalies using quantum ML
result = detect_anomaly_quantum(
    entity_name="Acme Trading Corp",
    transaction_id="LC2026-HK-00482"
)

print(f"Anomaly Detected: {result['is_anomaly']}")
print(f"Quantum Score: {result['quantum_score']:.2f}")
print(f"Confidence: {result['anomaly_confidence']:.0%}")
```

---

## 📊 Sample Cypher Queries

### 1. Find Sanctions Matches
```cypher
MATCH (e:Entity)-[r:SCREENED_AGAINST]->(s:SanctionEntity)
WHERE s.list_type = 'OFAC_SDN'
RETURN e.name, s.name, s.program, s.country
LIMIT 10;
```

### 2. Multi-Factor Risk Detection
```cypher
// Find LCs with amount discrepancy + late shipment + high-risk country
MATCH (buyer:Buyer)-[:ISSUED_LC]->(lc:LetterOfCredit)
      -[:REFERENCES]->(inv:CommercialInvoice)
      -[:BACKED_BY]->(bl:BillOfLading)
WHERE inv.discrepancy_flag = true
  AND bl.late_shipment = true
  AND buyer.country IN ['Iran', 'North Korea', 'Syria', 'Russia']
RETURN buyer.name, lc.lc_number, inv.discrepancy_pct, bl.days_late
ORDER BY inv.discrepancy_pct DESC;
```

---

## 🏗️ Project Structure

```
comp3520/
├── data/
│   ├── raw/                          # Kaggle datasets (gitignored)
│   ├── processed/                    # Generated data (gitignored)
│   │   ├── transactions.csv         # 1,000 trade finance records
│   │   ├── sanctions_all.csv        # 200 sanctions entities
│   │   └── training_data.csv        # ML training data
│   └── neo4j_import/                # Neo4j CSVs
│
├── models/                           # Trained ML models (gitignored)
│   ├── risk_model.pkl               # XGBoost credit scorer
│   ├── prophet_lc_volume.pkl        # Prophet forecaster
│   ├── lstm_port_delay.h5           # LSTM predictor
│   ├── isolation_forest.pkl         # Classical anomaly detector
│   └── quantum_vqc.pkl              # Quantum VQC weights
│
├── src/
│   ├── data_generation/
│   │   ├── generate_sanctions_list.py    # Create OFAC/UN/EU lists
│   │   └── enrich_transactions.py        # Generate LC/Invoice/B/L/PL
│   │
│   ├── skills/                           # 🎯 Agent Skills (Anthropic Framework)
│   │   ├── compliance_screening/
│   │   │   ├── SKILL.md                 # Skill documentation
│   │   │   └── scripts/
│   │   │       ├── screen_entity.py     # Main screening function
│   │   │       ├── batch_screen.py      # Batch processing
│   │   │       ├── country_risk.py      # Country risk scoring
│   │   │       └── fuzzy_matcher.py     # RapidFuzz utilities
│   │   │
│   │   ├── risk_assessment/
│   │   │   ├── SKILL.md
│   │   │   └── scripts/
│   │   │       ├── extract_features.py  # Neo4j feature extraction
│   │   │       ├── train_model.py       # XGBoost training
│   │   │       ├── score_entity.py      # Credit scoring
│   │   │       └── batch_score.py       # Batch scoring
│   │   │
│   │   ├── predictive_analytics/
│   │   │   ├── SKILL.md
│   │   │   └── scripts/
│   │   │       ├── train_prophet.py     # Prophet training
│   │   │       ├── train_lstm.py        # LSTM training
│   │   │       ├── prophet_forecaster.py
│   │   │       ├── lstm_predictor.py
│   │   │       └── isolation_forest.py
│   │   │
│   │   └── quantum_anomaly/
│   │       ├── SKILL.md
│   │       └── scripts/
│   │           ├── train_vqc.py         # Train 4-qubit VQC
│   │           ├── detect_quantum.py    # Quantum inference
│   │           ├── benchmark.py         # Quantum vs classical
│   │           └── extract_quantum_features.py
│   │
│   ├── ingest_trade_finance.py           # Neo4j ingestion
│   └── api.py                            # FastAPI server (Week 3)
│
├── venv/                                 # Virtual environment (gitignored)
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 🛠️ Development Workflow

**Daily routine:**
```bash
# 1. Navigate to project
cd ~/comp3520

# 2. Activate virtual environment
source venv/bin/activate

# 3. Make sure services are running
docker ps | grep neo4j-sentinel  # Neo4j should be running

# 4. Work on skills
python src/skills/compliance_screening/scripts/screen_entity.py

# 5. When done, deactivate
deactivate
```

---

## 📚 Development Roadmap

### ✅ Week 1: Foundation (COMPLETE)
- [x] Neo4j graph database setup
- [x] Trade finance data generation (1,000 transactions)
- [x] Sanctions list integration (OFAC, UN, EU)
- [x] Graph ingestion pipeline

### ✅ Week 2: ML Agent Skills (COMPLETE)
- [x] **Compliance Screening Skill**: Exact + fuzzy matching, <500ms latency
- [x] **Risk Assessment Skill**: XGBoost model, 12D features, AUC-ROC >0.85
- [x] **Predictive Analytics Skill**: Prophet + LSTM + Isolation Forest
- [x] **Quantum Anomaly Skill**: 4-qubit VQC, +3.9% F1 vs classical

### 🚧 Week 3: Self-Improving Agent (IN PROGRESS)
- [ ] LangGraph state machine for agentic workflows
- [ ] ChromaDB memory system for agent learning
- [ ] Privacy gateway for external API calls
- [ ] Agent skill orchestration layer

### 📅 Week 4: Dashboard & Visualization
- [ ] Streamlit multi-page application
- [ ] Real-time graph visualizations (Plotly)
- [ ] Role-based views (Analyst, Compliance, Risk)
- [ ] Interactive skill playground

### 📅 Week 5: Demo & Documentation
- [ ] Golden demo scenarios
- [ ] Screen recording & presentation
- [ ] FYP report documentation
- [ ] GitHub Pages deployment

---

## 🐛 Troubleshooting

### "Module not found" errors
```bash
# Make sure virtual environment is activated
source venv/bin/activate
# Reinstall dependencies
pip install -r requirements.txt
```

### Neo4j connection errors
```bash
# Check if Neo4j is running
docker ps | grep neo4j-sentinel

# Restart Neo4j
docker restart neo4j-sentinel

# Check logs
docker logs neo4j-sentinel
```

### Skill import errors
```bash
# Make sure you're in project root
cd ~/comp3520
source venv/bin/activate

# Add src to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

---

## 📖 Documentation

- **Agent Skills**:
  - [Compliance Screening](src/skills/compliance_screening/SKILL.md)
  - [Risk Assessment](src/skills/risk_assessment/SKILL.md)
  - [Predictive Analytics](src/skills/predictive_analytics/SKILL.md)
  - [Quantum Anomaly Detection](src/skills/quantum_anomaly/SKILL.md)

- **Data Generation**:
  - [Sanctions Lists](data/processed/README.md)
  - [Transaction Data](data/processed/README.md)

---

## 🎯 Project Goals

**For FYP (COMP3520):**
- Demonstrate full-stack AI system design with modular architecture
- Combine graph databases + LLMs + quantum ML + classical ML
- Address real-world trade finance challenges (compliance, risk, fraud)
- Showcase Anthropic's Agent Skills framework in production

**For HSBC Internship:**
- Deep transaction banking domain knowledge
- Privacy-first architecture (air-gapped, no external APIs)
- Production-grade ML pipelines (training, validation, deployment)
- Research mindset (quantum advantage benchmarking)

---

## 📝 License

MIT License - See LICENSE file for details

---

## 👤 Author

**Brian Ho** - HKU Data Science Student
- GitHub: [@hck717](https://github.com/hck717)

---

**Last Updated**: January 22, 2026
