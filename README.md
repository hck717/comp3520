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
- **Kaggle Account** (for downloading datasets)

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

## 📊 Step 2: Download Trade Finance Datasets

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
python src/data_generation/enrich_transactions.py
# Output: 1,000 complete trade finance records in data/processed/transactions.csv
```

**Expected Output:**
```
✅ Generated 200 sanctions entities
   - OFAC SDN: 67 entities
   - UN SC: 68 entities
   - EU FSF: 65 entities

✅ Generated 1,000 complete trade finance records
   - Amount discrepancies: 103 (10.3%)
   - Late shipments: 147 (14.7%)
   - Fraud flags: 52 (5.2%)
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
# Run the ingestion script
python src/ingest_realtime.py
```

**What this does:**
- Creates graph schema (Buyer, Seller, Bank, LC, Invoice, B/L, Packing List nodes)
- Ingests 1,000 trade finance transactions
- Links documents to entities
- Loads sanctions lists for compliance screening

**Verify in Neo4j Browser:**
```cypher
// Count all nodes
MATCH (n) RETURN count(n);

// Visualize a trade finance chain
MATCH path = (buyer:Entity)-[:ISSUED_LC]->(lc:LetterOfCredit)
             -[:REFERENCES]->(inv:CommercialInvoice)
             -[:BACKED_BY]->(bl:BillOfLading)
RETURN path LIMIT 5;
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
  "answer": "Found 12 LCs with significant amount discrepancies...",
  "generated_cypher": "MATCH (lc:LetterOfCredit)-[:REFERENCES]->(inv:CommercialInvoice)...",
  "risk_assessment": {...}
}
```

---

## 📊 Explore Your Graph

### Sample Cypher Queries

**1. Find Sanctions Matches**
```cypher
MATCH (e:Entity)-[:SCREENED_AGAINST]->(s:SanctionEntity)
WHERE s.list_type = 'OFAC_SDN'
RETURN e.name, s.name, s.program
LIMIT 10;
```

**2. Detect Amount Discrepancies**
```cypher
MATCH (lc:LetterOfCredit)-[:REFERENCES]->(inv:CommercialInvoice)
WHERE abs(inv.amount - lc.amount) > lc.amount * 0.1
RETURN lc.lc_number, lc.amount, inv.amount,
       (inv.amount - lc.amount) / lc.amount * 100 AS deviation_pct
ORDER BY deviation_pct DESC;
```

**3. Find Late Shipments**
```cypher
MATCH (lc:LetterOfCredit)-[:COVERS]->(ship:Shipment)
WHERE ship.actual_ship_date > lc.latest_ship_date
RETURN lc.lc_number, lc.latest_ship_date, ship.actual_ship_date,
       duration.between(lc.latest_ship_date, ship.actual_ship_date).days AS days_late
ORDER BY days_late DESC;
```

**4. Trace Document Chain**
```cypher
MATCH path = (lc:LetterOfCredit)-[:REFERENCES]->(inv:CommercialInvoice)
             -[:BACKED_BY]->(bl:BillOfLading)-[:DESCRIBES]->(pl:PackingList)
RETURN path LIMIT 5;
```

**5. High-Risk Country Exposure**
```cypher
MATCH (e:Entity)-[:ISSUED_LC|BENEFICIARY]->(lc:LetterOfCredit)
WHERE e.country IN ['Iran', 'North Korea', 'Syria', 'Venezuela']
RETURN e.country, count(lc) AS lc_count, sum(lc.amount) AS total_exposure
ORDER BY total_exposure DESC;
```

---

## 🏗️ Project Structure

```
comp3520/
├── data/
│   ├── raw/                    # Kaggle datasets (not in git)
│   ├── processed/              # Generated data (not in git)
│   └── neo4j_import/          # Neo4j-ready CSVs
│
├── src/
│   ├── data_generation/
│   │   ├── generate_sanctions_list.py
│   │   └── enrich_transactions.py
│   ├── ingest_realtime.py     # Neo4j ingestion
│   ├── api.py                 # FastAPI server
│   └── skills/                # Agent skills
│
├── venv/                      # Virtual environment (not in git)
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