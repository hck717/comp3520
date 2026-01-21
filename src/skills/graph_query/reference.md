# Reference: Banking Graph Schema & Query Logic

## 1. Graph Schema
The database models a banking system with Accounts, Entities (Owners), and Transactions.

### Nodes
- **`Account`**
  - `id`: (String, Unique) The account number (e.g., "12345").
  - `bank_id`: (String) The bank identifier.
  - `risk_score`: (Float) Internal risk score (0.0 - 1.0).

- **`Entity`** (The owner of an account)
  - `name`: (String, Indexed) Company or Person name (e.g., "Smith Corp").
  - `type`: (String) "Company" or "Person".
  - `jurisdiction`: (String) Country of registration (e.g., "United States", "High Risk Jurisdiction").
  - `doc_id`: (String) EIN or SSN.
  - `risk_flag`: (String) "Low", "Medium", "High".

### Relationships
- **`(:Entity)-[:OWNS]->(:Account)`**
  - Indicates ownership. One entity can own multiple accounts.
- **`(:Account)-[:TRANSFERRED {props}]->(:Account)`**
  - Represents a money transfer.
  - Properties:
    - `amount`: (Float) Transaction amount.
    - `currency`: (String) e.g., "USD", "EUR".
    - `timestamp`: (String/Int) Time of transaction.
    - `is_laundering`: (Integer) 1 if flagged as laundering, 0 otherwise.
    - `format`: (String) Transfer method (e.g., "Wire", "ACH").

---

## 2. Query Scenarios & Logic

### Scenario A: Investigating a Specific Entity
**User Input:** "What accounts does [Company Name] own?" or "Tell me about [Person Name]."
**Logic:** 
1. Search for the `Entity` node by `name` (use `CONTAINS` for fuzzy match).
2. Traverse `[:OWNS]` to find their `Account` nodes.
**Cypher:**
```cypher
MATCH (e:Entity)
WHERE toLower(e.name) CONTAINS toLower($name)
OPTIONAL MATCH (e)-[:OWNS]->(a:Account)
RETURN e.name, e.type, e.risk_flag, collect(a.id) as accounts
LIMIT 5
```

### Scenario B: Tracing Transaction Flows
**User Input:** "Show me transfers from account [ID]" or "Where did the money go?"
**Logic:**
1. Find the source `Account` by `id`.
2. Follow `[:TRANSFERRED]` relationships outwards.
**Cypher:**
```cypher
MATCH (source:Account {id: $account_id})-[t:TRANSFERRED]->(target:Account)
RETURN source.id, target.id, t.amount, t.currency, t.timestamp
ORDER BY t.amount DESC LIMIT 10
```

### Scenario C: Detecting Potential Fraud/Laundering
**User Input:** "Find suspicious transactions" or "Show money laundering."
**Logic:**
1. Filter `[:TRANSFERRED]` relationships where `is_laundering = 1`.
2. Return details of sender and receiver.
**Cypher:**
```cypher
MATCH (a:Account)-[t:TRANSFERRED]->(b:Account)
WHERE t.is_laundering = 1
RETURN a.id as Sender, b.id as Receiver, t.amount, t.format
LIMIT 10
```

### Scenario D: Jurisdiction Analysis
**User Input:** "List companies in High Risk Jurisdictions."
**Logic:**
1. Filter `Entity` nodes by `jurisdiction`.
2. (Optional) Check what accounts they own.
**Cypher:**
```cypher
MATCH (e:Entity)
WHERE e.jurisdiction CONTAINS "High Risk"
RETURN e.name, e.type, e.doc_id
LIMIT 20
```

---

## 3. Best Practices for the Agent
- **Always use `LIMIT`**: Never run a query without `LIMIT` (default to 10 or 20) to prevent crashing the viewer.
- **Case Insensitivity**: Always use `toLower()` when matching string names.
- **ID Lookup**: Account IDs are strings. If a user gives a number, treat it as a string.
- **No Mutations**: Do NOT generate `CREATE`, `MERGE`, `DELETE`, or `SET` queries. Read-only (`MATCH`) access only.
