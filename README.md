# Layer A: Data Foundation for GraphRAG

This project sets up a realistic banking data foundation for an Anti-Money Laundering (AML) GraphRAG system. It combines structural transaction data (IBM AML Dataset) with synthetic KYC context (Faker) in a Neo4j Knowledge Graph.

## 1. Prerequisites
- **Python 3.10+**
- **Docker Desktop** (for running Neo4j)
- **Dataset**: Download `LI-Small_Trans.csv` from [Kaggle](https://www.kaggle.com/datasets/ealtman2019/ibm-transactions-for-anti-money-laundering-aml?select=LI-Small_Trans.csv) and place it in the `data/` folder.
- **Optional (for Agentic Ingestion)**: [Ollama](https://ollama.com) installed with Llama 3.2.

## 2. Setup & Installation

### Step 1: Start Neo4j Database
Run Neo4j in a Docker container. This exposes the database on port 7687 and the UI on port 7474.
```bash
docker run -d --name neo4j-mvp \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  -e NEO4J_PLUGINS='["apoc", "graph-data-science"]' \
  neo4j:5.18.0
```
*Note: If the container already exists (and is stopped), restart it with `docker start neo4j-mvp`.*

### Step 2: Install Python Dependencies
```bash
pip install -r requirements.txt
```

## 3. Data Ingestion (Choose Your Approach)

You have **two options** for ingesting data into Neo4j:

### Option A: Hardcoded Ingestion (Recommended for Production)
This is the **fast, deterministic** approach with explicit schema control. Best for high-volume financial data.

```bash
python src/ingest_layer_a.py
```

**What it does:**
- Loads 50k transactions from the IBM AML dataset
- Creates `Account` nodes and `TRANSFERRED` relationships
- Generates synthetic `Entity` (Company/Person) nodes using Faker
- Links entities to accounts via `OWNS` relationships

---

### Option B: Agentic Ingestion (Experimental - Local LLM)
This is the **autonomous** approach where a local LLM (Llama 3.2 via Ollama) analyzes your CSV and decides the schema for you.

**Setup:**
1. Install [Ollama](https://ollama.com).
2. Pull the model (Llama 3.2 is recommended for speed/quality balance):
   ```bash
   ollama pull llama3.2
   ```
3. Start the Ollama server:
   ```bash
   ollama serve
   ```

**Run the agent:**
```bash
# Optional: Set model if different from llama3.2
export OLLAMA_MODEL="llama3.2"

python src/ingest_agent.py
```

**What it does:**
1. 📊 **Analyzes CSV**: The script reads the first 10 rows and sends a prompt to your local Ollama.
2. 🤖 **Infers Schema**: Llama 3.2 proposes nodes (e.g., `Account`, `Bank`) and relationships (e.g., `SENT_MONEY`) in JSON format.
3. 🔧 **Generates Cypher**: Automatically writes the `MERGE` and `CREATE` statements.
4. 📥 **Executes Import**: Loads 5k rows as a proof-of-concept.

**Example LLM Output:**
```json
{
  "nodes": [
    {"label": "Account", "id_column": "from_account", "properties": ["from_bank"]},
    {"label": "Account", "id_column": "to_account", "properties": ["to_bank"]}
  ],
  "relationships": [
    {
      "type": "TRANSFERRED",
      "from_node": "Account",
      "to_node": "Account",
      "properties": ["amount_paid", "payment_currency", "timestamp"]
    }
  ]
}
```

**Why use this?**
- ✅ **Privacy**: Your data never leaves your machine.
- ✅ **Zero Cost**: No API fees.
- ✅ **Zero schema design**: Just point it at a CSV.
- ❌ **Slower**: Dependent on your local hardware.

---

## 4. Verify & Explore the Graph
Once ingestion is complete, open the **Neo4j Browser** at:
👉 **[http://localhost:7474](http://localhost:7474)**
*   **Username**: `neo4j`
*   **Password**: `password`

### Useful Cypher Queries
Run these queries in the Neo4j Browser to inspect your graph foundation.

**1. Basic Visualization (See the "Flesh" and "Skeleton")**
*Visualize a Company owning an Account that sent money.*
```cypher
MATCH (c:Entity)-[:OWNS]->(a:Account)-[t:TRANSFERRED]->(b:Account)
WHERE c.type = 'Company'
RETURN c, a, t, b LIMIT 25
```

**2. Find "High Risk" Entities**
*Show me accounts owned by people/companies in simulated High Risk Jurisdictions.*
```cypher
MATCH (e:Entity)-[:OWNS]->(a:Account)
WHERE e.jurisdiction CONTAINS 'High Risk'
RETURN e, a LIMIT 20
```

**3. Trace Money Flow from a Specific Account**
*Follow the money trail for 3 hops starting from a specific account.*
```cypher
MATCH path = (start:Account)-[:TRANSFERRED*1..3]->(end:Account)
WHERE start.id = '1'  // Replace with a real ID from your results
RETURN path LIMIT 10
```

**4. Spot "Smurfing" Patterns (Fan-out)**
*Find accounts that sent money to 5+ different recipients.*
```cypher
MATCH (sender:Account)-[:TRANSFERRED]->(receiver:Account)
WITH sender, count(DISTINCT receiver) as degree
WHERE degree > 5
RETURN sender.id, degree 
ORDER BY degree DESC LIMIT 10
```

**5. Find Large Transactions by Foreign Companies**
*Find transactions > 10,000 sent by companies not in 'United States'.*
```cypher
MATCH (e:Entity)-[:OWNS]->(sender:Account)-[t:TRANSFERRED]->(receiver:Account)
WHERE e.type = 'Company' 
  AND e.jurisdiction <> 'United States' 
  AND t.amount > 10000
RETURN e.name, e.jurisdiction, t.amount, receiver.id 
ORDER BY t.amount DESC LIMIT 10
```

**6. Count Total Nodes & Edges**
*Verify how big your graph is.*
```cypher
CALL apoc.meta.stats() YIELD labels, relTypes
RETURN labels, relTypes
```

**7. Compare Hardcoded vs Agentic Results** (If you ran both)
*See what schema the LLM chose vs your hardcoded version.*
```cypher
CALL db.schema.visualization()
```

---

## 5. Architecture: Hardcoded vs Agentic

| Aspect | Hardcoded (`ingest_layer_a.py`) | Agentic (`ingest_agent.py`) |
|--------|----------------------------------|------------------------------|
| **Speed** | ⚡ Fast (5k rows/sec) | 🐢 Slower (Local inference) |
| **Control** | 🎯 Explicit schema | 🤖 LLM decides |
| **Privacy** | 🔒 Local | 🔒 Local (Ollama) |
| **Setup** | Zero config | Requires Ollama installed |

**Recommendation**: Use **hardcoded** for your FYP's transaction data. Use **agentic** when you add unstructured news/documents in Layer B/C.
