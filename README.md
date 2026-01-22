# Sentinel-Zero: AI-Powered Trade Finance Intelligence Platform

Sentinel-Zero is a self-improving, privacy-first trade finance intelligence platform that transforms fragmented trade documents (Letter of Credit, Bill of Lading, Commercial Invoice, Packing List) into an intelligent knowledge graph with real-time analytics, predictive insights, automated anomaly detection, compliance screening, and dynamic risk assessment.

## Core Capabilities

- **Real-time Transaction Monitoring**: Live LC processing with interactive graph visualization
- **Compliance & Sanctions Screening**: Automated screening against OFAC, UN, EU sanctions lists
- **Dynamic Risk Assessment**: AI-driven credit scoring using transaction behavior and market intelligence
- **Anomaly Detection**: Hybrid classical + quantum ML for detecting document discrepancies
- **Self-Improving AI Agent**: LangGraph-based assistant that learns from analyst feedback
- **Privacy-First Architecture**: Air-gapped design keeping sensitive data local

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

# Install all dependencies
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

⚠️  Clear existing Neo4j data? (y/N): n

📂 Loaded 1000 transactions from data/processed/transactions.csv

🔧 Creating constraints and indexes...
✅ Constraints and indexes created

📊 Ingesting entities (Buyers, Sellers, Banks)...
  ✅ 200 buyers
  ✅ 150 sellers
  ✅ 30 banks

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

⚠️  Creating risk flags...
  ✅ Flagged 47 potentially fraudulent transactions

============================================================
  INGESTION SUMMARY
============================================================
Entities (Total)............................ 380
  - Buyers................................... 200
  - Sellers.................................. 150
  - Banks.................................... 30
Letters of Credit........................... 1000
Commercial Invoices......................... 1000
  - With Discrepancies....................... 181
Bills of Lading............................. 1000
  - Late Shipments........................... 703
Packing Lists............................... 1000
Sanctions Entities.......................... 200
Sanctions Matches........................... 52
Fraud Flags................................. 47
============================================================

🎉 INGESTION COMPLETE!
```

**Verify in Neo4j Browser**:

Open [http://localhost:7474](http://localhost:7474) and run:

```cypher
// Count all nodes
MATCH (n) RETURN count(n) AS total_nodes;

// Visualize a complete trade finance chain
MATCH path = (buyer:Buyer)-[:ISSUED_LC]->(lc:LetterOfCredit)
             -[:REFERENCES]->(inv:CommercialInvoice)
             -[:BACKED_BY]->(bl:BillOfLading)
             -[:DESCRIBES]->(pl:PackingList)
RETURN path LIMIT 5;

// Find a sanctioned entity
MATCH (buyer:Buyer)-[r:SCREENED_AGAINST]->(s:SanctionEntity)
RETURN buyer.name, s.name, s.list_type, s.program
LIMIT 5;
```

---

## 🤖 Step 6: Start Ollama & Pull LLM Model

```bash
# Install Ollama from https://ollama.com
# Then pull the model:
ollama pull llama3.2

# Start Ollama server (in a separate terminal)
ollama serve

# Test it's working
curl http://localhost:11434/api/tags
```

---

## 🚀 Step 7: Run the AI Agent API

```bash
# Make sure Neo4j and Ollama are running
# Then start the FastAPI server:
python src/api.py
```

**Access the API**: [http://localhost:8000](http://localhost:8000)

**Example Query:**
```bash
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"query": "Show me all LCs where invoice amount exceeds LC amount by more than 10%"}'
```

**Response:**
```json
{
  "answer": "Found 181 LCs with significant amount discrepancies...",
  "generated_cypher": "MATCH (lc:LetterOfCredit)-[:REFERENCES]->(inv:CommercialInvoice)...",
  "risk_assessment": {...}
}
```

---

## 📊 Explore Your Graph - Sample Cypher Queries

### 1. Find Sanctions Matches
```cypher
MATCH (e:Entity)-[r:SCREENED_AGAINST]->(s:SanctionEntity)
WHERE s.list_type = 'OFAC_SDN'
RETURN e.name, s.name, s.program, s.country
LIMIT 10;
```

### 2. Detect Amount Discrepancies
```cypher
MATCH (lc:LetterOfCredit)-[:REFERENCES]->(inv:CommercialInvoice)
WHERE inv.discrepancy_flag = true
RETURN lc.lc_number, 
       lc.amount AS lc_amount, 
       inv.amount AS invoice_amount,
       inv.discrepancy_pct AS deviation_pct
ORDER BY inv.discrepancy_pct DESC
LIMIT 20;
```

### 3. Find Late Shipments
```cypher
MATCH (lc:LetterOfCredit)-[:REFERENCES]->(inv:CommercialInvoice)
      -[:BACKED_BY]->(bl:BillOfLading)
WHERE bl.late_shipment = true
RETURN lc.lc_number, 
       lc.latest_ship_date, 
       bl.shipment_date,
       bl.days_late
ORDER BY bl.days_late DESC
LIMIT 10;
```

### 4. Trace Complete Document Chain
```cypher
MATCH path = (buyer:Buyer)-[:ISSUED_LC]->(lc:LetterOfCredit)
             -[:REFERENCES]->(inv:CommercialInvoice)
             -[:BACKED_BY]->(bl:BillOfLading)
             -[:DESCRIBES]->(pl:PackingList)
RETURN path LIMIT 5;
```

### 5. High-Risk Country Exposure
```cypher
MATCH (buyer:Buyer)-[:ISSUED_LC]->(lc:LetterOfCredit)
WHERE buyer.country IN ['Iran', 'North Korea', 'Syria', 'Russia', 'Venezuela']
RETURN buyer.country, 
       count(lc) AS lc_count, 
       sum(lc.amount) AS total_exposure,
       lc.currency
ORDER BY total_exposure DESC;
```

### 6. Multi-Factor Risk Detection
```cypher
// Find LCs with amount discrepancy + late shipment + high-risk country
MATCH (buyer:Buyer)-[:ISSUED_LC]->(lc:LetterOfCredit)
      -[:REFERENCES]->(inv:CommercialInvoice)
      -[:BACKED_BY]->(bl:BillOfLading)
WHERE inv.discrepancy_flag = true
  AND bl.late_shipment = true
  AND buyer.country IN ['Iran', 'North Korea', 'Syria', 'Venezuela']
RETURN buyer.name, buyer.country, lc.lc_number, 
       inv.discrepancy_pct, bl.days_late
ORDER BY inv.discrepancy_pct DESC;
```

### 7. Fraud Pattern Detection
```cypher
// Find buyers with multiple fraud flags
MATCH (buyer:Buyer)-[:ISSUED_LC]->(lc:LetterOfCredit)
WHERE lc.fraud_flag = true
WITH buyer, count(lc) AS fraud_count
WHERE fraud_count > 1
RETURN buyer.name, buyer.country, fraud_count
ORDER BY fraud_count DESC;
```

---

## 🏗️ Project Structure

```
comp3520/
├── data/
│   ├── raw/                          # Kaggle datasets (not in git)
│   ├── processed/                    # Generated data (not in git)
│   │   ├── transactions.csv         # 1,000 trade finance records
│   │   ├── sanctions_all.csv        # 200 sanctions entities
│   │   ├── sanctions_ofac.csv
│   │   ├── sanctions_un.csv
│   │   └── sanctions_eu.csv
│   └── neo4j_import/                # Neo4j-ready CSVs
│
├── src/
│   ├── data_generation/
│   │   ├── __init__.py
│   │   ├── generate_sanctions_list.py    # Create OFAC/UN/EU lists
│   │   └── enrich_transactions.py        # Generate LC/Invoice/B/L/PL
│   ├── ingest_trade_finance.py           # ✨ NEW: Neo4j ingestion
│   ├── ingest_layer_a.py                 # Old AML ingestion (reference)
│   ├── api.py                            # FastAPI server
│   └── skills/                           # Agent skills
│
├── venv/                                 # Virtual environment (not in git)
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
curl http://localhost:11434/api/tags  # Ollama should respond

# 4. Work on your code
python src/api.py

# 5. When done, deactivate
deactivate
```

**Update dependencies:**
```bash
source venv/bin/activate
pip install <new-package>
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Add <new-package> dependency"
```

---

## 📚 Next Steps

### Week 2: ML Models
- [ ] Train XGBoost risk scoring model
- [ ] Implement quantum anomaly detector (PennyLane)
- [ ] Build predictive analytics (Prophet, LSTM)

### Week 3: Self-Improving Agent
- [ ] Implement LangGraph state machine
- [ ] Add ChromaDB memory system
- [ ] Build privacy gateway for external APIs

### Week 4: Dashboard
- [ ] Create Streamlit multi-page app
- [ ] Add real-time visualizations (Plotly)
- [ ] Implement role-based views

### Week 5: Demo
- [ ] Prepare golden demo scenarios
- [ ] Record screen demos
- [ ] Write FYP documentation

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

### Ollama not responding
```bash
# Start Ollama server
ollama serve

# In another terminal, verify
curl http://localhost:11434/api/tags
```

### Data generation issues
```bash
# If you see "file not found" for Kaggle datasets, that's OK!
# The scripts will automatically create synthetic data

# Regenerate all data
python src/data_generation/generate_sanctions_list.py
python src/data_generation/enrich_transactions.py
```

---

## 📖 Documentation

- **Data Sources**: See `data/raw/README.md`
- **Generated Data Schema**: See `data/processed/README.md`
- **Neo4j Import Guide**: See `data/neo4j_import/README.md`

---

## 🎯 Project Goals

**For FYP:**
- Demonstrate full-stack AI system design
- Combine graph databases + LLMs + quantum ML
- Address real-world trade finance challenges

**For HSBC Internship:**
- Showcase transaction banking domain knowledge
- Highlight privacy-first architecture
- Prove ability to build production-grade systems

---

## 📝 License

MIT License - See LICENSE file for details

---

## 👤 Author

Brian Ho - HKU Data Science Student
- GitHub: [@hck717](https://github.com/hck717)
- Project: Sentinel-Zero Trade Finance Intelligence Platform
- Course: COMP3520 Final Year Project

---

**Last Updated**: January 22, 2026