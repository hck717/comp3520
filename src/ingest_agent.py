import os
import pandas as pd
from neo4j import GraphDatabase
import requests
from tqdm import tqdm
import json

# --- CONFIGURATION ---
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PWD = os.getenv("NEO4J_PASSWORD", "password")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2") 

class AgenticDataIngestor:
    """
    Autonomous CSV-to-Graph ingestion using local LLM (Ollama) to infer schema and generate Cypher.
    This is the "Agentic" approach - the LLM decides how to model the data.
    """
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PWD))

    def close(self):
        self.driver.close()

    def query_ollama(self, prompt):
        """Sends prompt to local Ollama instance and gets response."""
        try:
            response = requests.post(OLLAMA_URL, json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            })
            response.raise_for_status()
            return response.json()['response']
        except requests.exceptions.RequestException as e:
            print(f"❌ Error communicating with Ollama: {e}")
            print("   Make sure Ollama is running: 'ollama serve' or check URL.")
            return None

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
- Use existing column names exactly as they appear (even with spaces)
- Create meaningful relationship types in UPPERCASE
- If a column looks like an ID/Account/Entity, make it a node
- Transaction details become relationship properties
"""

        print(f"🤖 Asking local LLM ({OLLAMA_MODEL}) to infer schema...")
        response_text = self.query_ollama(prompt)
        
        if not response_text:
            raise Exception("Failed to get response from Ollama")

        # Clean response if needed
        response_text = response_text.strip()
        if response_text.startswith("```"):
             response_text = response_text.split("\n", 1)[1].rsplit("\n```", 1)[0]

        try:
            schema = json.loads(response_text)
            print("\n✅ Schema inferred:")
            print(json.dumps(schema, indent=2))
            return schema
        except json.JSONDecodeError:
            print("❌ Error parsing JSON from LLM. Raw output:")
            print(response_text)
            raise

    def _escape_key(self, key):
        """Helper to wrap keys with spaces in backticks for Cypher."""
        if " " in key or "." in key:
            return f"`{key}`"
        return key

    def generate_cypher(self, schema):
        """
        Step 2: Generate Cypher query from the inferred schema.
        Now handles column names with spaces by escaping them.
        """
        print("\n🔧 Generating Cypher query...")
        
        # Build MERGE statements for nodes
        node_merges = []
        for node in schema["nodes"]:
            # SAFE GET: Use .get("properties", []) to handle missing keys from LLM
            props_list = node.get("properties", [])
            node_alias = node['label'].lower()
            
            # FIX: Apply alias to EVERY property in the list (e.g. bank.`To Bank`, bank.`Amount Received`)
            props = ", ".join([f"{node_alias}.{self._escape_key(p)} = row.{self._escape_key(p)}" for p in props_list])
            
            # Construct MERGE
            merge = f"""MERGE ({node_alias}:{node['label']} {{id: toString(row.{self._escape_key(node['id_column'])})}})"""
            
            # Only add ON CREATE SET if there are properties to set
            if props:
                merge += f"\n            ON CREATE SET {props}"
                
            node_merges.append(merge)
        
        # Build CREATE statements for relationships
        rel_creates = []
        for rel in schema["relationships"]:
            from_label = rel["from_node"].lower()
            to_label = rel["to_node"].lower()
            props_list = rel.get("properties", [])
            # FIX: Use ':' for property map inside CREATE
            props = ", ".join([f"{self._escape_key(p)}: row.{self._escape_key(p)}" for p in props_list])
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
    DATA_FILE = "data/LI-Small_Trans.csv"
    
    if not os.path.exists(DATA_FILE):
        print(f"❌ Error: {DATA_FILE} not found.")
        exit(1)
    
    try:
        requests.get(OLLAMA_URL.replace("/api/generate", ""))
    except:
        print(f"❌ Error: Cannot connect to Ollama at {OLLAMA_URL}")
        print("   Please run: 'ollama serve' and 'ollama run llama3.2'")
        exit(1)

    agent = AgenticDataIngestor()
    
    # Step 1: Let the LLM analyze the CSV and propose a schema
    schema = agent.analyze_csv(DATA_FILE, sample_rows=10)
    
    # Step 2 & 3: Generate Cypher and ingest
    agent.ingest_with_schema(DATA_FILE, schema, limit=5000)
    
    agent.close()
    print("\n🎉 Agentic Ingestion Complete!")
