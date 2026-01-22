# COMP3520 - Trade Finance Fraud Detection with Agentic AI

## Overview
An advanced fraud detection system combining:
- **Graph Neural Networks (GNN)** for transaction network analysis
- **Quantum Machine Learning (VQC)** for anomaly detection
- **XGBoost Risk Assessment** for credit/compliance scoring
- **Graph RAG** for intelligent document retrieval
- **Agentic AI** orchestration via Model Context Protocol (MCP)

## Project Structure
```
comp3520/
├── src/
│   ├── agent/              # Agentic AI orchestration
│   │   ├── mcp_agent.py    # Main MCP agent
│   │   └── tools/          # Agent tools
│   ├── data_generation/    # Balanced data generation
│   │   └── generate_balanced_data.py
│   ├── graph/              # Neo4j graph operations
│   │   └── operations/
│   └── skills/             # Individual ML skills
│       ├── quantum_anomaly/    # VQC fraud detection
│       │   └── scripts/
│       │       ├── train_vqc.py
│       │       ├── detect_quantum.py
│       │       └── benchmark.py
│       └── risk_assessment/    # XGBoost risk model
│           └── scripts/
│               ├── train_model.py
│               ├── score_entity.py
│               └── extract_features.py
├── data/
│   ├── raw/                # Kaggle datasets (optional)
│   └── processed/          # Generated training data
├── models/                 # Trained model artifacts
├── test_improvements.py    # Comprehensive test suite
└── docs/
    ├── IMPLEMENTATION_COMPLETE.md
    ├── TESTING_GUIDE.md
    └── WEEK2_SUMMARY.md
```

## Quick Start

### 1. Environment Setup
```bash
# Clone and navigate
git clone https://github.com/hck717/comp3520.git
cd comp3520

# Create virtual environment (Python 3.9+)
python -m venv venv
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Neo4j Setup (Optional)
Required for Graph RAG and entity scoring:
```bash
# Pull Neo4j Docker image
docker pull neo4j:5.26.0

# Run Neo4j container
docker run -d \
  --name neo4j-sentinel \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password123 \
  -v $PWD/data/neo4j_data:/data \
  neo4j:5.26.0

# Access Neo4j Browser at http://localhost:7474
```

### 3. Run Complete Test Suite
```bash
python test_improvements.py
```

This runs all 4 test components:
1. **Data Generation** - Creates balanced training dataset (70% normal, 30% anomalies)
2. **Risk Assessment** - Trains XGBoost credit risk model
3. **Quantum Training** - Trains VQC anomaly detector
4. **Benchmark** - Compares Quantum VQC vs Classical Isolation Forest

**Expected Output:**
```
============================================================
TEST SUMMARY
============================================================
   ✅ PASS  Data Generation
   ✅ PASS  Risk Assessment
   ✅ PASS  Quantum Training
   ✅ PASS  Quantum Benchmark

============================================================
RESULTS: 4/4 tests passed
============================================================

🎉 ALL TESTS PASSED! 🎉
```

## Individual Skill Usage

### 1. Generate Balanced Training Data
```bash
python -m src.data_generation.generate_balanced_data \
  --samples 1000 \
  --anomaly-ratio 0.30 \
  --output data/processed/training_data_balanced.csv
```

### 2. Train Risk Assessment Model (XGBoost)
```bash
python -m src.skills.risk_assessment.scripts.train_model \
  --data data/processed/training_data_balanced.csv \
  --output models/risk_model.pkl
```

**Metrics Achieved:**
- AUC-ROC: 1.000
- Precision: 1.000
- Recall: 1.000
- F1-Score: 1.000

### 3. Train Quantum VQC Anomaly Detector
```bash
python -m src.skills.quantum_anomaly.scripts.train_vqc \
  --data data/processed/training_data_balanced.csv \
  --output models/quantum_vqc_balanced.pkl \
  --epochs 30
```

**Metrics Achieved:**
- Precision: 1.000 (100% of detected anomalies are correct)
- Recall: 0.773 (77.3% of all anomalies detected)
- F1-Score: 0.872 (excellent balanced performance)

### 4. Run Quantum vs Classical Benchmark
```bash
python -m src.skills.quantum_anomaly.scripts.benchmark
```

**Comparison Results:**

| Metric | Quantum VQC | Classical IF |
|--------|-------------|-------------|
| Training Time | 264s | 0.05s |
| Inference Time | 3.14ms | 0.07ms |
| Accuracy | 100% | 88% |
| Anomaly Detection | 30% | 34% |

**Conclusion:**
- ✅ **Quantum VQC**: Better accuracy, potentially superior feature representation
- ✅ **Classical IF**: Faster inference, better for production at scale

### 5. Score Entity Risk (Requires Neo4j)
```bash
python -m src.skills.risk_assessment.scripts.score_entity \
  --entity-name "ACME Corp" \
  --entity-type buyer \
  --model models/risk_model.pkl
```

## Data Sources

### Option 1: Synthetic Data (Default)
The system automatically generates synthetic trade finance data if Kaggle datasets are not available.

### Option 2: Real Kaggle Datasets
Download these datasets to `data/raw/`:

1. **Global Trade Settlement Network**
   - URL: https://www.kaggle.com/datasets/sujan97/global-trade-settlement-network
   - File: `globaltradesettlenet.csv`

2. **Cross-Border Trade & Customs Data**
   - URL: https://www.kaggle.com/datasets/daiearth22/cross-border-trade-and-customs-data
   - File: `cross_border_customs.csv`

```bash
# After downloading to data/raw/, regenerate data
python -m src.data_generation.generate_balanced_data
```

## Model Artifacts

Trained models are saved to `models/`:
- `risk_model.pkl` - XGBoost credit risk classifier with metadata
- `quantum_vqc_balanced.pkl` - Trained VQC with quantum weights
- `quantum_vqc_benchmark.pkl` - Benchmark VQC for comparison

## Key Features

### 1. Balanced Data Generation
- Configurable anomaly ratio (default 30%)
- Realistic trade finance features (11 dimensions)
- Port risk scores, document completeness, fraud flags
- Handles both Kaggle data and pure synthetic generation

### 2. Graph Neural Networks
- Fraud detection via transaction network analysis
- Node embeddings for buyer/seller/bank entities
- Temporal pattern detection across linked transactions

### 3. Quantum Machine Learning
- Variational Quantum Circuit (VQC) classifier
- 4-qubit architecture with angle encoding
- Trained on PennyLane with JAX optimizer
- Perfect precision (100%) with high recall (77%)

### 4. Classical ML Baseline
- XGBoost for risk assessment
- Perfect F1-Score on balanced data
- Feature importance analysis for explainability
- Isolation Forest for benchmark comparison

### 5. Graph RAG
- Retrieval-Augmented Generation over Neo4j knowledge graph
- Query trade finance documents and regulations
- Context-aware Q&A for compliance checks

## Development

### Run Individual Tests
```python
# Test only risk assessment
python -c "from test_improvements import test_risk_assessment; test_risk_assessment()"

# Test only quantum training
python -c "from test_improvements import test_quantum_training; test_quantum_training()"
```

### Add New Skills
1. Create skill folder in `src/skills/your_skill/`
2. Implement `scripts/train.py` and `scripts/predict.py`
3. Add skill to `test_improvements.py`
4. Update agent tools in `src/agent/tools/`

## Troubleshooting

### Neo4j Connection Issues
```bash
# Check if container is running
docker ps

# Restart Neo4j
docker restart neo4j-sentinel

# View logs
docker logs neo4j-sentinel
```

### Import Errors
```bash
# Ensure you're in project root
cd ~/comp3520

# Activate virtual environment
source venv/bin/activate

# Add src to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

### NumPy Version Warning (PennyLane)
```bash
# Upgrade NumPy if needed
pip install numpy --upgrade
```

## Performance Metrics Summary

### Risk Assessment (XGBoost)
- ✅ AUC-ROC: 1.000
- ✅ Precision: 1.000
- ✅ Recall: 1.000
- ✅ F1-Score: 1.000
- ✅ Training: 800 samples (70/30 split)
- ✅ Perfect confusion matrix (TN=140, TP=60, FP=0, FN=0)

### Quantum Anomaly Detection (VQC)
- ✅ Precision: 1.000 (no false positives)
- ✅ Recall: 0.773 (catches 77% of anomalies)
- ✅ F1-Score: 0.872 (excellent balance)
- ✅ Training: 30 epochs, converged loss = 0.404
- ✅ 4-qubit architecture, angle encoding

### Benchmark: Quantum vs Classical
- ✅ Quantum: 100% accuracy, 264s training, 3.14ms inference
- ✅ Classical: 88% accuracy, 0.05s training, 0.07ms inference
- 🎯 **Quantum advantage:** Better accuracy and feature representation
- ⚡ **Classical advantage:** Faster training and inference for production

## Documentation

- **[IMPLEMENTATION_COMPLETE.md](docs/IMPLEMENTATION_COMPLETE.md)** - Full implementation details
- **[TESTING_GUIDE.md](docs/TESTING_GUIDE.md)** - Comprehensive testing guide
- **[WEEK2_SUMMARY.md](docs/WEEK2_SUMMARY.md)** - Week 2 progress summary

## Tech Stack

- **ML/DL:** PyTorch, XGBoost, scikit-learn, PennyLane
- **Quantum:** PennyLane, JAX optimizer, qiskit-compatible
- **Graph DB:** Neo4j 5.26.0
- **Agent:** LangChain, MCP (Model Context Protocol)
- **Data:** Pandas, NumPy
- **Testing:** pytest (via test_improvements.py)

## License

MIT License - Academic project for COMP3520

## Author

Brian Ho (@hck717)
HKU Data Science Student
