# Neo4j Setup Guide - COMP3520 Trade Finance Graph

## 🚀 Quick Start

### 1. Start Neo4j Docker Container

```bash
# Start Neo4j
docker run -d \
  --name neo4j-sentinel \
  -p 7474:7474 \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password123 \
  neo4j:5.26.0

# Check logs
docker logs neo4j-sentinel

# Wait ~30 seconds for startup
```

### 2. Access Neo4j Browser

Open: http://localhost:7474

**Login:**
- Username: `neo4j`
- Password: `password123`

---

## 📊 Sample Data for Testing

### Create Nodes

Paste these queries in Neo4j Browser:

```cypher
// Create Buyers
CREATE (b1:Buyer {name: 'Global Electronics Inc', country: 'US', credit_rating: 'AAA'})
CREATE (b2:Buyer {name: 'Euro Trading GmbH', country: 'DE', credit_rating: 'AA'})
CREATE (b3:Buyer {name: 'Asia Imports Ltd', country: 'CN', credit_rating: 'A'})
CREATE (b4:Buyer {name: 'Suspicious Buyer Corp', country: 'IR', credit_rating: 'C'})
RETURN b1, b2, b3, b4;
```

```cypher
// Create Sellers
CREATE (s1:Seller {name: 'Tech Manufacturing Co', country: 'TW', industry: 'Electronics'})
CREATE (s2:Seller {name: 'Global Exports LLC', country: 'US', industry: 'General Trade'})
CREATE (s3:Seller {name: 'Shady Shell Company', country: 'RU', industry: 'Unknown'})
CREATE (s4:Seller {name: 'Premium Goods Ltd', country: 'HK', industry: 'Luxury'})
RETURN s1, s2, s3, s4;
```

### Create Transactions

```cypher
// Normal transactions
MATCH (b:Buyer {name: 'Global Electronics Inc'}), (s:Seller {name: 'Tech Manufacturing Co'})
CREATE (b)-[:TRANSACTED {
  amount: 250000,
  date: date('2025-11-15'),
  lc_number: 'LC-2025-1001',
  status: 'completed',
  risk_score: 0.1
}]->(s);

MATCH (b:Buyer {name: 'Euro Trading GmbH'}), (s:Seller {name: 'Premium Goods Ltd'})
CREATE (b)-[:TRANSACTED {
  amount: 180000,
  date: date('2025-12-01'),
  lc_number: 'LC-2025-1002',
  status: 'completed',
  risk_score: 0.15
}]->(s);

MATCH (b:Buyer {name: 'Asia Imports Ltd'}), (s:Seller {name: 'Global Exports LLC'})
CREATE (b)-[:TRANSACTED {
  amount: 320000,
  date: date('2025-12-10'),
  lc_number: 'LC-2025-1003',
  status: 'pending',
  risk_score: 0.2
}]->(s);
```

```cypher
// Suspicious transactions (high-risk)
MATCH (b:Buyer {name: 'Suspicious Buyer Corp'}), (s:Seller {name: 'Shady Shell Company'})
CREATE (b)-[:TRANSACTED {
  amount: 950000,
  date: date('2026-01-05'),
  lc_number: 'LC-2026-1004',
  status: 'flagged',
  risk_score: 0.95,
  alert: 'High-risk parties'
}]->(s);

MATCH (b:Buyer {name: 'Asia Imports Ltd'}), (s:Seller {name: 'Shady Shell Company'})
CREATE (b)-[:TRANSACTED {
  amount: 450000,
  date: date('2026-01-10'),
  lc_number: 'LC-2026-1005',
  status: 'under_review',
  risk_score: 0.75
}]->(s);
```

### Create Circular Pattern (Fraud Detection)

```cypher
// Create entities for circular transaction pattern
CREATE (e1:Entity {name: 'Company A', country: 'US'})
CREATE (e2:Entity {name: 'Company B', country: 'CN'})
CREATE (e3:Entity {name: 'Company C', country: 'HK'})
CREATE (e4:Entity {name: 'Company D', country: 'SG'})

WITH e1, e2, e3, e4
CREATE (e1)-[:TRANSACTED {amount: 100000, date: date('2026-01-15')}]->(e2)
CREATE (e2)-[:TRANSACTED {amount: 95000, date: date('2026-01-16')}]->(e3)
CREATE (e3)-[:TRANSACTED {amount: 90000, date: date('2026-01-17')}]->(e4)
CREATE (e4)-[:TRANSACTED {amount: 85000, date: date('2026-01-18')}]->(e1)
RETURN e1, e2, e3, e4;
```

---

## 🔍 Query Examples for Agent Testing

### 1. Find All Transactions

```cypher
MATCH (b:Buyer)-[t:TRANSACTED]->(s:Seller)
RETURN b.name AS buyer, 
       s.name AS seller, 
       t.amount AS amount,
       t.date AS date,
       t.risk_score AS risk
ORDER BY t.date DESC
LIMIT 10;
```

### 2. High-Risk Transactions

```cypher
MATCH (b:Buyer)-[t:TRANSACTED]->(s:Seller)
WHERE t.risk_score > 0.7
RETURN b.name AS buyer,
       b.country AS buyer_country,
       s.name AS seller,
       s.country AS seller_country,
       t.amount AS amount,
       t.risk_score AS risk,
       t.alert AS alert_reason
ORDER BY t.risk_score DESC;
```

### 3. Circular Transaction Detection (Money Laundering)

```cypher
MATCH path = (a:Entity)-[:TRANSACTED*3..5]->(a)
RETURN path,
       length(path) AS cycle_length,
       [n IN nodes(path) | n.name] AS entities,
       [r IN relationships(path) | r.amount] AS amounts
LIMIT 10;
```

### 4. Top Entities by Transaction Volume

```cypher
MATCH (e)-[t:TRANSACTED]->()
WITH e, 
     count(t) AS transaction_count,
     sum(t.amount) AS total_volume
RETURN e.name AS entity,
       e.country AS country,
       transaction_count,
       total_volume
ORDER BY total_volume DESC
LIMIT 10;
```

### 5. Country Risk Analysis

```cypher
MATCH (b:Buyer)-[t:TRANSACTED]->(s:Seller)
WITH b.country AS country,
     count(t) AS txn_count,
     sum(t.amount) AS volume,
     avg(t.risk_score) AS avg_risk
RETURN country,
       txn_count,
       volume,
       round(avg_risk * 100) / 100 AS avg_risk_score
ORDER BY avg_risk_score DESC;
```

### 6. Network Analysis - Find Connections

```cypher
MATCH (b:Buyer {name: 'Suspicious Buyer Corp'})-[t1:TRANSACTED]->(s:Seller)
MATCH (s)-[t2:TRANSACTED*0..2]-(connected)
RETURN b, t1, s, connected
LIMIT 50;
```

### 7. Time-Series Analysis

```cypher
MATCH (b:Buyer)-[t:TRANSACTED]->(s:Seller)
WITH date(t.date) AS txn_date,
     count(*) AS daily_count,
     sum(t.amount) AS daily_volume
RETURN txn_date,
       daily_count,
       daily_volume
ORDER BY txn_date DESC
LIMIT 30;
```

### 8. Suspicious Pattern: Multiple High-Value Transactions

```cypher
MATCH (b:Buyer)-[t:TRANSACTED]->(s:Seller)
WHERE t.amount > 500000
WITH b, count(t) AS high_value_count, sum(t.amount) AS total
WHERE high_value_count >= 2
RETURN b.name AS buyer,
       b.country AS country,
       high_value_count,
       total
ORDER BY total DESC;
```

---

## 🧹 Clear Database

```cypher
// Delete all nodes and relationships
MATCH (n)
DETACH DELETE n;
```

```cypher
// Verify empty
MATCH (n)
RETURN count(n) AS node_count;
```

---

## 📈 Visualize Graph

### Full Graph View

```cypher
MATCH (n)
RETURN n
LIMIT 100;
```

### Transaction Network

```cypher
MATCH path = (b:Buyer)-[t:TRANSACTED]->(s:Seller)
RETURN path
LIMIT 50;
```

---

## 🐳 Docker Management

```bash
# Stop Neo4j
docker stop neo4j-sentinel

# Start Neo4j
docker start neo4j-sentinel

# Restart Neo4j
docker restart neo4j-sentinel

# Remove Neo4j (deletes all data)
docker rm -f neo4j-sentinel

# View logs
docker logs -f neo4j-sentinel

# Check container status
docker ps | grep neo4j
```

---

## 🔗 Connection Details

**For Applications:**
- Bolt URI: `bolt://localhost:7687`
- HTTP URI: `http://localhost:7474`
- Username: `neo4j`
- Password: `password123`

**Python Example:**
```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "password123")
)

with driver.session() as session:
    result = session.run("""
        MATCH (b:Buyer)-[t:TRANSACTED]->(s:Seller)
        RETURN b.name, s.name, t.amount
        LIMIT 10
    """)
    
    for record in result:
        print(record)

driver.close()
```

---

## ✅ Verify Setup

Run the agent test suite:

```bash
python test_agent_skills.py
```

Look for:
```
[3a] Testing Neo4j connection...
  ✅ Neo4j connected successfully

[3b] Querying transaction network...
  Found X transactions
```

---

## 📚 Resources

- [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/current/)
- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/current/)
- [Graph Data Science](https://neo4j.com/docs/graph-data-science/current/)

---

**Created:** January 22, 2026  
**Author:** Brian Ho (@hck717)  
**Course:** COMP3520 - Advanced AI Systems
