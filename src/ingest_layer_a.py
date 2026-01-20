import os
import pandas as pd
from neo4j import GraphDatabase
from faker import Faker
from tqdm import tqdm
import random

# --- CONFIGURATION ---
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PWD = os.getenv("NEO4J_PASSWORD", "password")
DATA_FILE = "data/LI-Small_Trans.csv"

# Initialize Faker for KYC Context
fake = Faker()

class DataIngestor:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PWD))

    def close(self):
        self.driver.close()

    def create_constraints(self):
        """Create indexes for faster lookup."""
        with self.driver.session() as session:
            print("Creating Constraints & Indexes...")
            session.run("CREATE CONSTRAINT account_id IF NOT EXISTS FOR (a:Account) REQUIRE a.id IS UNIQUE")
            session.run("CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE")
            session.run("CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name)")

    def ingest_transactions(self, file_path, limit=100000):
        """
        Loads the IBM CSV and creates Account->Account relationships.
        Limit set to 100k rows for MVP speed. Set to None for full load.
        """
        print(f"Loading Transactions from {file_path}...")
        
        # Schema: Timestamp, From Bank, Account, To Bank, Account, Amount Received, Receiving Currency, Amount Paid, Payment Currency, Payment Format, Is Laundering
        df = pd.read_csv(file_path, nrows=limit)
        
        # Rename columns to standard keys
        df.columns = [
            "timestamp", "from_bank", "from_account", "to_bank", "to_account", 
            "amount_received", "receiving_currency", "amount_paid", "payment_currency", "payment_format", "is_laundering"
        ]

        query = """
        UNWIND $rows AS row
        MERGE (source:Account {id: toString(row.from_account)})
        ON CREATE SET source.bank_id = row.from_bank, source.risk_score = 0.0
        
        MERGE (target:Account {id: toString(row.to_account)})
        ON CREATE SET target.bank_id = row.to_bank, target.risk_score = 0.0
        
        CREATE (source)-[:TRANSFERRED {
            amount: toFloat(row.amount_paid),
            currency: row.payment_currency,
            format: row.payment_format,
            timestamp: row.timestamp,
            is_laundering: toInteger(row.is_laundering)
        }]->(target)
        """

        batch_size = 5000
        with self.driver.session() as session:
            for i in tqdm(range(0, len(df), batch_size), desc="Ingesting Batches"):
                batch = df.iloc[i:i+batch_size].to_dict('records')
                session.run(query, rows=batch)
        print(f"✅ Ingested {len(df)} transactions.")

    def enrich_with_context(self):
        """
        Iterates over all Accounts and creates synthetic 'Company' or 'Person' owners.
        This provides the 'Unstructured Context' for RAG.
        """
        print("Enriching Graph with Synthetic KYC Context (Faker)...")
        
        fetch_accounts_query = "MATCH (a:Account) WHERE NOT (a)<-[:OWNS]-(:Entity) RETURN a.id AS acc_id"
        
        # We process in batches to generate context
        with self.driver.session() as session:
            result = session.run(fetch_accounts_query)
            accounts = [record["acc_id"] for record in result]
            
            print(f"Found {len(accounts)} bare accounts to enrich.")
            
            batch = []
            batch_size = 1000
            
            for acc_id in tqdm(accounts, desc="Generating Entities"):
                # 70% chance Individual, 30% chance Company
                is_company = random.random() < 0.3
                
                if is_company:
                    name = fake.company()
                    entity_type = "Company"
                    jurisdiction = fake.country()
                    # Inject some 'High Risk' jurisdictions for the demo
                    if random.random() < 0.05: 
                        jurisdiction = "High Risk Jurisdiction (Simulated)"
                    doc_id = fake.ein()
                else:
                    name = fake.name()
                    entity_type = "Person"
                    jurisdiction = fake.country()
                    doc_id = fake.ssn()

                batch.append({
                    "acc_id": acc_id,
                    "name": name,
                    "type": entity_type,
                    "jurisdiction": jurisdiction,
                    "doc_id": doc_id,
                    "risk_flag": random.choice(["Low", "Medium", "High"])
                })
                
                if len(batch) >= batch_size:
                    self._push_enrichment_batch(session, batch)
                    batch = []
            
            if batch:
                self._push_enrichment_batch(session, batch)

    def _push_enrichment_batch(self, session, batch):
        query = """
        UNWIND $rows AS row
        MATCH (a:Account {id: row.acc_id})
        MERGE (e:Entity {name: row.name})
        ON CREATE SET 
            e.type = row.type,
            e.jurisdiction = row.jurisdiction,
            e.doc_id = row.doc_id,
            e.risk_flag = row.risk_flag
        MERGE (e)-[:OWNS]->(a)
        """
        session.run(query, rows=batch)

if __name__ == "__main__":
    if not os.path.exists(DATA_FILE):
        print(f"❌ Error: {DATA_FILE} not found. Please download LI-Small_Trans.csv from Kaggle.")
    else:
        ingestor = DataIngestor()
        ingestor.create_constraints()
        # Step 1: Structural Data (Skeleton)
        ingestor.ingest_transactions(DATA_FILE, limit=50000) # Start small with 50k
        # Step 2: Context Data (Flesh)
        ingestor.enrich_with_context()
        ingestor.close()
        print("🎉 Layer A Complete: Data Foundation Ready.")
