# Graph Query Skill

## Description
This skill allows the agent to query the Neo4j Graph Database to answer questions about banking transactions, account ownership, and potential money laundering activities.

## Tools (Scripts)
The agent can use the following python scripts located in the `scripts/` directory:

### 1. `query_neo4j.py`
Executes a Cypher query against the Neo4j database and returns the results.
- **Input**: A valid Cypher query string (e.g., `MATCH (n:Account) RETURN n LIMIT 5`).
- **Output**: A JSON string containing the query results.
- **Usage**: Use this for ANY question that requires retrieving specific data, counting nodes, finding patterns, or checking properties in the database.

## Usage Process
1. **Analyze the User's Request**: Determine if the question requires data from the database (e.g., "Find high-risk accounts", "How much money did X transfer?").
2. **Consult Reference**: Check `reference.md` for the correct Graph Schema (Nodes, Relationships, Properties) and example queries.
3. **Generate Cypher**: Construct a syntactically correct Cypher query based on the schema.
4. **Execute Script**: Call `query_neo4j.py` with the generated Cypher.
5. **Interpret Results**: Use the JSON output to answer the user's question in natural language.
