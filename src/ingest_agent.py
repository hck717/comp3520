import os
import pandas as pd
from neo4j import GraphDatabase
import anthropic
from tqdm import tqdm
import json

# --- CONFIGURATION ---
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PWD = os.getenv("NEO4J_PASSWORD", "password")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")  # Get from https://console.anthropic.com/

class AgenticDataIngestor:
    """
    Autonomous CSV-to-Graph ingestion using an LLM to infer schema and generate Cypher.
    This is the "Agentic" approach - the LLM decides how to model the data.
    """
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PWD))
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    def close(self):
        self.driver.close()

    def analyze_csv(self, file_path, sample_rows=5):
        """
        Step 1: Read CSV and use LLM to infer the graph schema.
        Returns: A schema dict with nodes, relationships, and column mappings.
        """
        print(f"\n📊 Analyzing CSV: {file_path}")
        df = pd.read_csv(file_path, nrows=sample_rows)
        
        # Build prompt for LLM
        columns_info = "\n".join([f"- {col}: {df[col].dtype} (sample: {df[col].iloc[0]})" for col in df.columns])
        sample_data = df.head(3).to_string()
        
        prompt = f"""You are a graph database expert. Analyze this CSV and propose a Neo4j schema.

CSV Columns:
{columns_info}

Sample Data:
{sample_data}

Return ONLY a JSON object (no markdown, no explanation) with this structure:
{{
  "nodes": [
    {{"label": "NodeType1", "id_column": "column_name", "properties": ["col1", "col2"]}},
    {{"label": "NodeType2", "id_column": "column_name", "properties": ["col3"]}}
  ],
  "relationships": [
    {{
      "type": "RELATIONSHIP_NAME",
      "from_node": "NodeType1",
      "to_node": "NodeType2",
      "properties": ["amount", "timestamp"]
    }}
  ]
}}

Rules:
- Use existing column names exactly as they appear
- Create meaningful relationship types in UPPERCASE
- If a column looks like an ID/Account/Entity, make it a node
- Transaction details become relationship properties
"""

        print("🤖 Asking LLM to infer schema...")
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        schema_text = response.content[0].text.strip()
        # Remove potential markdown code fences
        if schema_text.startswith("```"):
            schema_text = schema_text.split("\n", 1)[1].rsplit("\n```", 1)[0]
        
        schema = json.loads(schema_text)
        print("\n✅ Schema inferred:")
        print(json.dumps(schema, indent=2))
        return schema

    def generate_cypher(self, schema):
        """
        Step 2: Generate Cypher query from the inferred schema.
        """
        print("\n🔧 Generating Cypher query...")
        
        # Build MERGE statements for nodes
        node_merges = []
        for node in schema["nodes"]:
            props = ", ".join([f"{p}: row.{p}" for p in node["properties"]])
            merge = f"""MERGE ({node['label'].lower()}:{node['label']} {{id: toString(row.{node['id_column']})}})
            ON CREATE SET {node['label'].lower()}.{props}"""
            node_merges.append(merge)
        
        # Build CREATE statements for relationships
        rel_creates = []
        for rel in schema["relationships"]:
            from_label = rel["from_node"].lower()
            to_label = rel["to_node"].lower()
            props = ", ".join([f"{p}: row.{p}" for p in rel.get("properties", [])])
            props_clause = f" {{{props}}}" if props else ""
            create = f"CREATE ({from_label})-[:{rel['type']}{props_clause}]->({to_label})"
            rel_creates.append(create)
        
        cypher = f"""UNWIND $rows AS row
{chr(10).join(node_merges)}
{chr(10).join(rel_creates)}
"""
        print(cypher)
        return cypher

    def ingest_with_schema(self, file_path, schema, limit=10000):
        """
        Step 3: Load CSV using the generated Cypher.
        """
        print(f"\n📥 Ingesting data with inferred schema (limit: {limit})...")
        df = pd.read_csv(file_path, nrows=limit)
        
        cypher = self.generate_cypher(schema)
        
        batch_size = 1000
        with self.driver.session() as session:
            for i in tqdm(range(0, len(df), batch_size), desc="Agentic Ingestion"):
                batch = df.iloc[i:i+batch_size].to_dict('records')
                session.run(cypher, rows=batch)
        
        print(f"✅ Agentic ingestion complete: {len(df)} rows")

if __name__ == "__main__":
    if not ANTHROPIC_API_KEY:
        print("❌ Error: Set ANTHROPIC_API_KEY environment variable.")
        print("   Get your key from: https://console.anthropic.com/")
        exit(1)
    
    DATA_FILE = "data/LI-Small_Trans.csv"
    
    if not os.path.exists(DATA_FILE):
        print(f"❌ Error: {DATA_FILE} not found.")
        exit(1)
    
    agent = AgenticDataIngestor()
    
    # Step 1: Let the LLM analyze the CSV and propose a schema
    schema = agent.analyze_csv(DATA_FILE, sample_rows=10)
    
    # Step 2 & 3: Generate Cypher and ingest (use a small sample for demo)
    agent.ingest_with_schema(DATA_FILE, schema, limit=5000)
    
    agent.close()
    print("\n🎉 Agentic Ingestion Complete!")
