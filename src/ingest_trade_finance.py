<<<<<<< HEAD
"""\nNeo4j Ingestion Script for Sentinel-Zero Trade Finance Platform\n\nIngests:\n- Letter of Credit (LC) transactions\n- Commercial Invoices\n- Bills of Lading (B/L)\n- Packing Lists\n- Entities (Buyers, Sellers, Banks)\n- Sanctions lists (OFAC, UN, EU)\n\nUsage:\n    python src/ingest_trade_finance.py\n    \nPrerequisites:\n- Neo4j running on localhost:7687 (or set NEO4J_URI env var)\n- Generated data in data/processed/\n"""\n\nimport os\nimport pandas as pd\nfrom neo4j import GraphDatabase\nfrom tqdm import tqdm\nfrom datetime import datetime\n\n# --- CONFIGURATION ---\nNEO4J_URI = os.getenv(\"NEO4J_URI\", \"bolt://localhost:7687\")\nNEO4J_USER = os.getenv(\"NEO4J_USER\", \"neo4j\")\nNEO4J_PASSWORD = os.getenv(\"NEO4J_PASSWORD\", \"password123\")  # Updated default\n\nTRANSACTIONS_FILE = \"data/processed/transactions.csv\"\nSANCTIONS_FILE = \"data/processed/sanctions_all.csv\"\n\n\nclass TradeFinanceIngestor:\n    def __init__(self):\n        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))\n        print(f\"✅ Connected to Neo4j at {NEO4J_URI}\")\n\n    def close(self):\n        self.driver.close()\n        print(\"\\n✅ Connection closed\")\n\n    def clear_database(self):\n        \"\"\"Clear all nodes and relationships (use with caution!)\"\"\"\n        print(\"\\n⚠️  Clearing existing data...\")\n        with self.driver.session() as session:\n            session.run(\"MATCH (n) DETACH DELETE n\")\n        print(\"✅ Database cleared\")\n\n    def create_constraints(self):\n        \"\"\"Create uniqueness constraints and indexes for performance\"\"\"\n        print(\"\\n🔧 Creating constraints and indexes...\")\n        \n        constraints = [\n            \"CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE\",\n            \"CREATE CONSTRAINT lc_number IF NOT EXISTS FOR (lc:LetterOfCredit) REQUIRE lc.lc_number IS UNIQUE\",\n            \"CREATE CONSTRAINT invoice_number IF NOT EXISTS FOR (inv:CommercialInvoice) REQUIRE inv.invoice_number IS UNIQUE\",\n            \"CREATE CONSTRAINT bl_number IF NOT EXISTS FOR (bl:BillOfLading) REQUIRE bl.bl_number IS UNIQUE\",\n            \"CREATE CONSTRAINT pl_number IF NOT EXISTS FOR (pl:PackingList) REQUIRE pl.packing_list_number IS UNIQUE\",\n            \"CREATE CONSTRAINT sanction_id IF NOT EXISTS FOR (s:SanctionEntity) REQUIRE s.sanction_id IS UNIQUE\",\n        ]\n        \n        indexes = [\n            \"CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name)\",\n            \"CREATE INDEX lc_date IF NOT EXISTS FOR (lc:LetterOfCredit) ON (lc.issue_date)\",\n            \"CREATE INDEX sanction_name IF NOT EXISTS FOR (s:SanctionEntity) ON (s.name)\",\n        ]\n        \n        with self.driver.session() as session:\n            for constraint in constraints:\n                try:\n                    session.run(constraint)\n                except Exception as e:\n                    print(f\"  ⚠️  {e}\")\n            \n            for index in indexes:\n                try:\n                    session.run(index)\n                except Exception as e:\n                    print(f\"  ⚠️  {e}\")\n        \n        print(\"✅ Constraints and indexes created\")\n\n    def ingest_entities(self, df):\n        \"\"\"Create Entity nodes (Buyers, Sellers, Banks) - deduplicated\"\"\"\n        print(\"\\n📊 Ingesting entities (Buyers, Sellers, Banks)...\")\n        \n        # Extract unique entities\n        buyers = df[['buyer_id', 'buyer_name', 'buyer_country']].drop_duplicates()\n        sellers = df[['seller_id', 'seller_name', 'seller_country']].drop_duplicates()\n        banks = df[['bank_id', 'bank_name']].drop_duplicates()\n        \n        # Ingest buyers\n        buyer_query = \"\"\"\n        UNWIND $rows AS row\n        MERGE (e:Entity:Buyer {id: row.buyer_id})\n        ON CREATE SET \n            e.name = row.buyer_name,\n            e.country = row.buyer_country,\n            e.type = 'Buyer',\n            e.created_at = datetime()\n        \"\"\"\n        \n        # Ingest sellers\n        seller_query = \"\"\"\n        UNWIND $rows AS row\n        MERGE (e:Entity:Seller {id: row.seller_id})\n        ON CREATE SET \n            e.name = row.seller_name,\n            e.country = row.seller_country,\n            e.type = 'Seller',\n            e.created_at = datetime()\n        \"\"\"\n        \n        # Ingest banks\n        bank_query = \"\"\"\n        UNWIND $rows AS row\n        MERGE (e:Entity:Bank {id: row.bank_id})\n        ON CREATE SET \n            e.name = row.bank_name,\n            e.type = 'Bank',\n            e.created_at = datetime()\n        \"\"\"\n        \n        with self.driver.session() as session:\n            session.run(buyer_query, rows=buyers.to_dict('records'))\n            session.run(seller_query, rows=sellers.to_dict('records'))\n            session.run(bank_query, rows=banks.to_dict('records'))\n        \n        print(f\"  ✅ {len(buyers)} buyers\")\n        print(f\"  ✅ {len(sellers)} sellers\")\n        print(f\"  ✅ {len(banks)} banks\")\n\n    def ingest_letter_of_credits(self, df):\n        \"\"\"Create Letter of Credit nodes\"\"\"\n        print(\"\\n📄 Ingesting Letters of Credit...\")\n        \n        lc_query = \"\"\"\n        UNWIND $rows AS row\n        \n        // Create LC node\n        CREATE (lc:LetterOfCredit {\n            lc_number: row.lc_number,\n            issue_date: date(row.lc_issue_date),\n            expiry_date: date(row.lc_expiry_date),\n            amount: toFloat(row.lc_amount),\n            currency: row.lc_currency,\n            commodity: row.commodity,\n            incoterms: row.incoterms,\n            latest_ship_date: date(row.latest_ship_date),\n            transaction_id: row.transaction_id\n        })\n        \n        // Link to entities\n        WITH lc, row\n        MATCH (buyer:Buyer {id: row.buyer_id})\n        MATCH (seller:Seller {id: row.seller_id})\n        MATCH (bank:Bank {id: row.bank_id})\n        \n        CREATE (buyer)-[:ISSUED_LC]->(lc)\n        CREATE (lc)-[:BENEFITS]->(seller)\n        CREATE (bank)-[:ADVISING_BANK]->(lc)\n        \"\"\"\n        \n        batch_size = 500\n        with self.driver.session() as session:\n            for i in tqdm(range(0, len(df), batch_size), desc=\"LC Batches\"):\n                batch = df.iloc[i:i+batch_size].to_dict('records')\n                session.run(lc_query, rows=batch)\n        \n        print(f\"  ✅ {len(df)} LCs ingested\")\n\n    def ingest_commercial_invoices(self, df):\n        \"\"\"Create Commercial Invoice nodes and link to LCs\"\"\"\n        print(\"\\n🧾 Ingesting Commercial Invoices...\")\n        \n        invoice_query = \"\"\"\n        UNWIND $rows AS row\n        \n        // Create invoice\n        CREATE (inv:CommercialInvoice {\n            invoice_number: row.invoice_number,\n            amount: toFloat(row.invoice_amount),\n            currency: row.lc_currency,\n            issue_date: date(row.invoice_date),\n            transaction_id: row.transaction_id\n        })\n        \n        // Link to LC\n        WITH inv, row\n        MATCH (lc:LetterOfCredit {lc_number: row.lc_number})\n        CREATE (lc)-[:REFERENCES]->(inv)\n        \n        // Flag discrepancies\n        WITH inv, lc, row\n        WHERE row.amount_discrepancy = true\n        SET inv.discrepancy_flag = true,\n            inv.discrepancy_amount = abs(toFloat(row.invoice_amount) - toFloat(row.lc_amount)),\n            inv.discrepancy_pct = abs(toFloat(row.invoice_amount) - toFloat(row.lc_amount)) / toFloat(row.lc_amount) * 100\n        \"\"\"\n        \n        batch_size = 500\n        with self.driver.session() as session:\n            for i in tqdm(range(0, len(df), batch_size), desc=\"Invoice Batches\"):\n                batch = df.iloc[i:i+batch_size].to_dict('records')\n                session.run(invoice_query, rows=batch)\n        \n        discrepancies = df['amount_discrepancy'].sum()\n        print(f\"  ✅ {len(df)} invoices ingested ({discrepancies} with discrepancies)\")\n\n    def ingest_bills_of_lading(self, df):\n        \"\"\"Create Bill of Lading nodes\"\"\"\n        print(\"\\n🚢 Ingesting Bills of Lading...\")\n        \n        bl_query = \"\"\"\n        UNWIND $rows AS row\n        \n        // Create B/L\n        CREATE (bl:BillOfLading {\n            bl_number: row.bl_number,\n            shipment_date: date(row.shipment_date),\n            port_of_loading: row.port_of_loading,\n            port_of_discharge: row.port_of_discharge,\n            vessel_name: row.vessel_name,\n            transaction_id: row.transaction_id\n        })\n        \n        // Link to Invoice\n        WITH bl, row\n        MATCH (inv:CommercialInvoice {invoice_number: row.invoice_number})\n        CREATE (inv)-[:BACKED_BY]->(bl)\n        \n        // Flag late shipments\n        WITH bl, row\n        MATCH (lc:LetterOfCredit {lc_number: row.lc_number})\n        WHERE row.late_shipment = true\n        SET bl.late_shipment = true,\n            bl.days_late = duration.inDays(lc.latest_ship_date, bl.shipment_date).days\n        \"\"\"\n        \n        batch_size = 500\n        with self.driver.session() as session:\n            for i in tqdm(range(0, len(df), batch_size), desc=\"B/L Batches\"):\n                batch = df.iloc[i:i+batch_size].to_dict('records')\n                session.run(bl_query, rows=batch)\n        \n        late_shipments = df['late_shipment'].sum()\n        print(f\"  ✅ {len(df)} B/Ls ingested ({late_shipments} late shipments)\")\n\n    def ingest_packing_lists(self, df):\n        \"\"\"Create Packing List nodes\"\"\"\n        print(\"\\n📦 Ingesting Packing Lists...\")\n        \n        pl_query = \"\"\"\n        UNWIND $rows AS row\n        \n        // Create packing list\n        CREATE (pl:PackingList {\n            packing_list_number: row.packing_list_number,\n            total_packages: toInteger(row.total_packages),\n            gross_weight_kg: toInteger(row.gross_weight_kg),\n            transaction_id: row.transaction_id\n        })\n        \n        // Link to B/L\n        WITH pl, row\n        MATCH (bl:BillOfLading {bl_number: row.bl_number})\n        CREATE (bl)-[:DESCRIBES]->(pl)\n        \"\"\"\n        \n        batch_size = 500\n        with self.driver.session() as session:\n            for i in tqdm(range(0, len(df), batch_size), desc=\"Packing List Batches\"):\n                batch = df.iloc[i:i+batch_size].to_dict('records')\n                session.run(pl_query, rows=batch)\n        \n        print(f\"  ✅ {len(df)} packing lists ingested\")\n\n    def ingest_sanctions(self):\n        \"\"\"Load sanctions lists and create screening relationships\"\"\"\n        print(\"\\n🚫 Ingesting sanctions lists...\")\n        \n        if not os.path.exists(SANCTIONS_FILE):\n            print(f\"  ⚠️  {SANCTIONS_FILE} not found, skipping sanctions\")\n            return\n        \n        df_sanctions = pd.read_csv(SANCTIONS_FILE)\n        \n        sanction_query = \"\"\"\n        UNWIND $rows AS row\n        CREATE (s:SanctionEntity {\n            sanction_id: row.sanction_id,\n            name: row.name,\n            aliases: row.aliases,\n            list_type: row.list_type,\n            country: row.country,\n            program: row.program,\n            entity_type: row.entity_type,\n            added_date: date(row.added_date),\n            id_number: row.id_number,\n            remarks: row.remarks\n        })\n        \"\"\"\n        \n        with self.driver.session() as session:\n            session.run(sanction_query, rows=df_sanctions.to_dict('records'))\n        \n        print(f\"  ✅ {len(df_sanctions)} sanctions entities loaded\")\n        \n        # Match entities to sanctions by name\n        print(\"  🔍 Screening entities against sanctions...\")\n        \n        screening_query = \"\"\"\n        MATCH (e:Entity)\n        MATCH (s:SanctionEntity)\n        WHERE e.name = s.name OR e.name IN split(s.aliases, '|')\n        MERGE (e)-[r:SCREENED_AGAINST]->(s)\n        ON CREATE SET r.matched_date = datetime(), r.match_type = 'exact'\n        RETURN count(r) AS matches\n        \"\"\"\n        \n        with self.driver.session() as session:\n            result = session.run(screening_query)\n            matches = result.single()['matches']\n        \n        print(f\"  ✅ Found {matches} sanctions matches\")\n\n    def create_risk_flags(self):\n        \"\"\"Add fraud flags and calculate risk scores\"\"\"\n        print(\"\\n⚠️  Creating risk flags...\")\n        \n        # Flag fraud transactions\n        fraud_query = \"\"\"\n        MATCH (lc:LetterOfCredit)\n        WHERE lc.transaction_id IN $fraud_ids\n        SET lc.fraud_flag = true\n        RETURN count(lc) AS flagged\n        \"\"\"\n        \n        # Load transaction data to get fraud flags\n        df = pd.read_csv(TRANSACTIONS_FILE)\n        fraud_ids = df[df['fraud_flag'] == True]['transaction_id'].tolist()\n        \n        with self.driver.session() as session:\n            result = session.run(fraud_query, fraud_ids=fraud_ids)\n            flagged = result.single()['flagged']\n        \n        print(f\"  ✅ Flagged {flagged} potentially fraudulent transactions\")\n\n    def verify_ingestion(self):\n        \"\"\"Print summary statistics\"\"\"\n        print(\"\\n\" + \"=\"*60)\n        print(\"  INGESTION SUMMARY\")\n        print(\"=\"*60)\n        \n        queries = {\n            \"Entities (Total)\": \"MATCH (e:Entity) RETURN count(e) AS count\",\n            \"  - Buyers\": \"MATCH (e:Buyer) RETURN count(e) AS count\",\n            \"  - Sellers\": \"MATCH (e:Seller) RETURN count(e) AS count\",\n            \"  - Banks\": \"MATCH (e:Bank) RETURN count(e) AS count\",\n            \"Letters of Credit\": \"MATCH (lc:LetterOfCredit) RETURN count(lc) AS count\",\n            \"Commercial Invoices\": \"MATCH (inv:CommercialInvoice) RETURN count(inv) AS count\",\n            \"  - With Discrepancies\": \"MATCH (inv:CommercialInvoice) WHERE inv.discrepancy_flag = true RETURN count(inv) AS count\",\n            \"Bills of Lading\": \"MATCH (bl:BillOfLading) RETURN count(bl) AS count\",\n            \"  - Late Shipments\": \"MATCH (bl:BillOfLading) WHERE bl.late_shipment = true RETURN count(bl) AS count\",\n            \"Packing Lists\": \"MATCH (pl:PackingList) RETURN count(pl) AS count\",\n            \"Sanctions Entities\": \"MATCH (s:SanctionEntity) RETURN count(s) AS count\",\n            \"Sanctions Matches\": \"MATCH ()-[r:SCREENED_AGAINST]->() RETURN count(r) AS count\",\n            \"Fraud Flags\": \"MATCH (lc:LetterOfCredit) WHERE lc.fraud_flag = true RETURN count(lc) AS count\",\n        }\n        \n        with self.driver.session() as session:\n            for label, query in queries.items():\n                result = session.run(query)\n                count = result.single()['count']\n                print(f\"{label:.<40} {count}\")\n        \n        print(\"=\"*60)\n\n\ndef main():\n    # Check if data files exist\n    if not os.path.exists(TRANSACTIONS_FILE):\n        print(f\"❌ Error: {TRANSACTIONS_FILE} not found!\")\n        print(\"   Please run the data generation scripts first:\")\n        print(\"   1. python -m src.data_generation.generate_sanctions_list\")\n        print(\"   2. python -m src.data_generation.enrich_transactions\")\n        return\n    \n    print(\"\\n\" + \"=\"*60)\n    print(\"  SENTINEL-ZERO TRADE FINANCE INGESTION\")\n    print(\"=\"*60)\n    \n    ingestor = TradeFinanceIngestor()\n    \n    try:\n        # Optional: Clear existing data\n        response = input(\"\\n⚠️  Clear existing Neo4j data? (y/N): \")\n        if response.lower() == 'y':\n            ingestor.clear_database()\n        \n        # Load transaction data\n        df = pd.read_csv(TRANSACTIONS_FILE)\n        print(f\"\\n📂 Loaded {len(df)} transactions from {TRANSACTIONS_FILE}\")\n        \n        # Step 1: Create schema\n        ingestor.create_constraints()\n        \n        # Step 2: Ingest entities\n        ingestor.ingest_entities(df)\n        \n        # Step 3: Ingest documents\n        ingestor.ingest_letter_of_credits(df)\n        ingestor.ingest_commercial_invoices(df)\n        ingestor.ingest_bills_of_lading(df)\n        ingestor.ingest_packing_lists(df)\n        \n        # Step 4: Load sanctions and screen\n        ingestor.ingest_sanctions()\n        \n        # Step 5: Add risk flags\n        ingestor.create_risk_flags()\n        \n        # Step 6: Verify\n        ingestor.verify_ingestion()\n        \n        print(\"\\n🎉 INGESTION COMPLETE!\")\n        print(f\"\\n🌐 Open Neo4j Browser: http://localhost:7474\")\n        print(f\"   Username: {NEO4J_USER}\")\n        print(f\"   Password: {NEO4J_PASSWORD}\")\n        \n    except Exception as e:\n        print(f\"\\n❌ Error during ingestion: {e}\")\n        import traceback\n        traceback.print_exc()\n    \n    finally:\n        ingestor.close()\n\n\nif __name__ == \"__main__\":\n    main()\n
=======
"""
Neo4j Ingestion Script for Sentinel-Zero Trade Finance Platform

Ingests:
- Letter of Credit (LC) transactions
- Commercial Invoices
- Bills of Lading (B/L)
- Packing Lists
- Entities (Buyers, Sellers, Banks)
- Sanctions lists (OFAC, UN, EU)

Usage:
    python src/ingest_trade_finance.py
    
Prerequisites:
- Neo4j running on localhost:7687 (or set NEO4J_URI env var)
- Generated data in data/processed/
"""

import os
import pandas as pd
from neo4j import GraphDatabase
from tqdm import tqdm
from datetime import datetime

# --- CONFIGURATION ---
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")  # Updated default

TRANSACTIONS_FILE = "data/processed/transactions.csv"
SANCTIONS_FILE = "data/processed/sanctions_all.csv"


class TradeFinanceIngestor:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        print(f"✅ Connected to Neo4j at {NEO4J_URI}")

    def close(self):
        self.driver.close()
        print("\n✅ Connection closed")

    def clear_database(self):
        """Clear all nodes and relationships (use with caution!)"""
        print("\n⚠️  Clearing existing data...")
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        print("✅ Database cleared")

    def create_constraints(self):
        """Create uniqueness constraints and indexes for performance"""
        print("\n🔧 Creating constraints and indexes...")
        
        constraints = [
            "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
            "CREATE CONSTRAINT lc_number IF NOT EXISTS FOR (lc:LetterOfCredit) REQUIRE lc.lc_number IS UNIQUE",
            "CREATE CONSTRAINT invoice_number IF NOT EXISTS FOR (inv:CommercialInvoice) REQUIRE inv.invoice_number IS UNIQUE",
            "CREATE CONSTRAINT bl_number IF NOT EXISTS FOR (bl:BillOfLading) REQUIRE bl.bl_number IS UNIQUE",
            "CREATE CONSTRAINT pl_number IF NOT EXISTS FOR (pl:PackingList) REQUIRE pl.packing_list_number IS UNIQUE",
            "CREATE CONSTRAINT sanction_id IF NOT EXISTS FOR (s:SanctionEntity) REQUIRE s.sanction_id IS UNIQUE",
        ]
        
        indexes = [
            "CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name)",
            "CREATE INDEX lc_date IF NOT EXISTS FOR (lc:LetterOfCredit) ON (lc.issue_date)",
            "CREATE INDEX sanction_name IF NOT EXISTS FOR (s:SanctionEntity) ON (s.name)",
        ]
        
        with self.driver.session() as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    print(f"  ⚠️  {e}")
            
            for index in indexes:
                try:
                    session.run(index)
                except Exception as e:
                    print(f"  ⚠️  {e}")
        
        print("✅ Constraints and indexes created")

    def ingest_entities(self, df):
        """Create Entity nodes (Buyers, Sellers, Banks) - deduplicated"""
        print("\n📊 Ingesting entities (Buyers, Sellers, Banks)...")
        
        # Extract unique entities
        buyers = df[['buyer_id', 'buyer_name', 'buyer_country']].drop_duplicates()
        sellers = df[['seller_id', 'seller_name', 'seller_country']].drop_duplicates()
        banks = df[['bank_id', 'bank_name']].drop_duplicates()
        
        # Ingest buyers
        buyer_query = """
        UNWIND $rows AS row
        MERGE (e:Entity:Buyer {id: row.buyer_id})
        ON CREATE SET 
            e.name = row.buyer_name,
            e.country = row.buyer_country,
            e.type = 'Buyer',
            e.created_at = datetime()
        """
        
        # Ingest sellers
        seller_query = """
        UNWIND $rows AS row
        MERGE (e:Entity:Seller {id: row.seller_id})
        ON CREATE SET 
            e.name = row.seller_name,
            e.country = row.seller_country,
            e.type = 'Seller',
            e.created_at = datetime()
        """
        
        # Ingest banks
        bank_query = """
        UNWIND $rows AS row
        MERGE (e:Entity:Bank {id: row.bank_id})
        ON CREATE SET 
            e.name = row.bank_name,
            e.type = 'Bank',
            e.created_at = datetime()
        """
        
        with self.driver.session() as session:
            session.run(buyer_query, rows=buyers.to_dict('records'))
            session.run(seller_query, rows=sellers.to_dict('records'))
            session.run(bank_query, rows=banks.to_dict('records'))
        
        print(f"  ✅ {len(buyers)} buyers")
        print(f"  ✅ {len(sellers)} sellers")
        print(f"  ✅ {len(banks)} banks")

    def ingest_letter_of_credits(self, df):
        """Create Letter of Credit nodes"""
        print("\n📄 Ingesting Letters of Credit...")
        
        lc_query = """
        UNWIND $rows AS row
        
        // Create LC node
        CREATE (lc:LetterOfCredit {
            lc_number: row.lc_number,
            issue_date: date(row.lc_issue_date),
            expiry_date: date(row.lc_expiry_date),
            amount: toFloat(row.lc_amount),
            currency: row.lc_currency,
            commodity: row.commodity,
            incoterms: row.incoterms,
            latest_ship_date: date(row.latest_ship_date),
            transaction_id: row.transaction_id
        })
        
        // Link to entities
        WITH lc, row
        MATCH (buyer:Buyer {id: row.buyer_id})
        MATCH (seller:Seller {id: row.seller_id})
        MATCH (bank:Bank {id: row.bank_id})
        
        CREATE (buyer)-[:ISSUED_LC]->(lc)
        CREATE (lc)-[:BENEFITS]->(seller)
        CREATE (bank)-[:ADVISING_BANK]->(lc)
        """
        
        batch_size = 500
        with self.driver.session() as session:
            for i in tqdm(range(0, len(df), batch_size), desc="LC Batches"):
                batch = df.iloc[i:i+batch_size].to_dict('records')
                session.run(lc_query, rows=batch)
        
        print(f"  ✅ {len(df)} LCs ingested")

    def ingest_commercial_invoices(self, df):
        """Create Commercial Invoice nodes and link to LCs"""
        print("\n🧾 Ingesting Commercial Invoices...")
        
        invoice_query = """
        UNWIND $rows AS row
        
        // Create invoice
        CREATE (inv:CommercialInvoice {
            invoice_number: row.invoice_number,
            amount: toFloat(row.invoice_amount),
            currency: row.lc_currency,
            issue_date: date(row.invoice_date),
            transaction_id: row.transaction_id
        })
        
        // Link to LC
        WITH inv, row
        MATCH (lc:LetterOfCredit {lc_number: row.lc_number})
        CREATE (lc)-[:REFERENCES]->(inv)
        
        // Flag discrepancies
        WITH inv, lc, row
        WHERE row.amount_discrepancy = true
        SET inv.discrepancy_flag = true,
            inv.discrepancy_amount = abs(toFloat(row.invoice_amount) - toFloat(row.lc_amount)),
            inv.discrepancy_pct = abs(toFloat(row.invoice_amount) - toFloat(row.lc_amount)) / toFloat(row.lc_amount) * 100
        """
        
        batch_size = 500
        with self.driver.session() as session:
            for i in tqdm(range(0, len(df), batch_size), desc="Invoice Batches"):
                batch = df.iloc[i:i+batch_size].to_dict('records')
                session.run(invoice_query, rows=batch)
        
        discrepancies = df['amount_discrepancy'].sum()
        print(f"  ✅ {len(df)} invoices ingested ({discrepancies} with discrepancies)")

    def ingest_bills_of_lading(self, df):
        """Create Bill of Lading nodes"""
        print("\n🚢 Ingesting Bills of Lading...")
        
        bl_query = """
        UNWIND $rows AS row
        
        // Create B/L
        CREATE (bl:BillOfLading {
            bl_number: row.bl_number,
            shipment_date: date(row.shipment_date),
            port_of_loading: row.port_of_loading,
            port_of_discharge: row.port_of_discharge,
            vessel_name: row.vessel_name,
            transaction_id: row.transaction_id
        })
        
        // Link to Invoice
        WITH bl, row
        MATCH (inv:CommercialInvoice {invoice_number: row.invoice_number})
        CREATE (inv)-[:BACKED_BY]->(bl)
        
        // Flag late shipments - FIXED: Use duration.inDays() instead of duration.between()
        WITH bl, row
        MATCH (lc:LetterOfCredit {lc_number: row.lc_number})
        WHERE row.late_shipment = true
        SET bl.late_shipment = true,
            bl.days_late = duration.inDays(lc.latest_ship_date, bl.shipment_date).days
        """
        
        batch_size = 500
        with self.driver.session() as session:
            for i in tqdm(range(0, len(df), batch_size), desc="B/L Batches"):
                batch = df.iloc[i:i+batch_size].to_dict('records')
                session.run(bl_query, rows=batch)
        
        late_shipments = df['late_shipment'].sum()
        print(f"  ✅ {len(df)} B/Ls ingested ({late_shipments} late shipments)")

    def ingest_packing_lists(self, df):
        """Create Packing List nodes"""
        print("\n📦 Ingesting Packing Lists...")
        
        pl_query = """
        UNWIND $rows AS row
        
        // Create packing list
        CREATE (pl:PackingList {
            packing_list_number: row.packing_list_number,
            total_packages: toInteger(row.total_packages),
            gross_weight_kg: toInteger(row.gross_weight_kg),
            transaction_id: row.transaction_id
        })
        
        // Link to B/L
        WITH pl, row
        MATCH (bl:BillOfLading {bl_number: row.bl_number})
        CREATE (bl)-[:DESCRIBES]->(pl)
        """
        
        batch_size = 500
        with self.driver.session() as session:
            for i in tqdm(range(0, len(df), batch_size), desc="Packing List Batches"):
                batch = df.iloc[i:i+batch_size].to_dict('records')
                session.run(pl_query, rows=batch)
        
        print(f"  ✅ {len(df)} packing lists ingested")

    def ingest_sanctions(self):
        """Load sanctions lists and create screening relationships"""
        print("\n🚫 Ingesting sanctions lists...")
        
        if not os.path.exists(SANCTIONS_FILE):
            print(f"  ⚠️  {SANCTIONS_FILE} not found, skipping sanctions")
            return
        
        df_sanctions = pd.read_csv(SANCTIONS_FILE)
        
        sanction_query = """
        UNWIND $rows AS row
        CREATE (s:SanctionEntity {
            sanction_id: row.sanction_id,
            name: row.name,
            aliases: row.aliases,
            list_type: row.list_type,
            country: row.country,
            program: row.program,
            entity_type: row.entity_type,
            added_date: date(row.added_date),
            id_number: row.id_number,
            remarks: row.remarks
        })
        """
        
        with self.driver.session() as session:
            session.run(sanction_query, rows=df_sanctions.to_dict('records'))
        
        print(f"  ✅ {len(df_sanctions)} sanctions entities loaded")
        
        # Match entities to sanctions by name
        print("  🔍 Screening entities against sanctions...")
        
        screening_query = """
        MATCH (e:Entity)
        MATCH (s:SanctionEntity)
        WHERE e.name = s.name OR e.name IN split(s.aliases, '|')
        MERGE (e)-[r:SCREENED_AGAINST]->(s)
        ON CREATE SET r.matched_date = datetime(), r.match_type = 'exact'
        RETURN count(r) AS matches
        """
        
        with self.driver.session() as session:
            result = session.run(screening_query)
            matches = result.single()['matches']
        
        print(f"  ✅ Found {matches} sanctions matches")

    def create_risk_flags(self):
        """Add fraud flags and calculate risk scores"""
        print("\n⚠️  Creating risk flags...")
        
        # Flag fraud transactions
        fraud_query = """
        MATCH (lc:LetterOfCredit)
        WHERE lc.transaction_id IN $fraud_ids
        SET lc.fraud_flag = true
        RETURN count(lc) AS flagged
        """
        
        # Load transaction data to get fraud flags
        df = pd.read_csv(TRANSACTIONS_FILE)
        fraud_ids = df[df['fraud_flag'] == True]['transaction_id'].tolist()
        
        with self.driver.session() as session:
            result = session.run(fraud_query, fraud_ids=fraud_ids)
            flagged = result.single()['flagged']
        
        print(f"  ✅ Flagged {flagged} potentially fraudulent transactions")

    def verify_ingestion(self):
        """Print summary statistics"""
        print("\n" + "="*60)
        print("  INGESTION SUMMARY")
        print("="*60)
        
        queries = {
            "Entities (Total)": "MATCH (e:Entity) RETURN count(e) AS count",
            "  - Buyers": "MATCH (e:Buyer) RETURN count(e) AS count",
            "  - Sellers": "MATCH (e:Seller) RETURN count(e) AS count",
            "  - Banks": "MATCH (e:Bank) RETURN count(e) AS count",
            "Letters of Credit": "MATCH (lc:LetterOfCredit) RETURN count(lc) AS count",
            "Commercial Invoices": "MATCH (inv:CommercialInvoice) RETURN count(inv) AS count",
            "  - With Discrepancies": "MATCH (inv:CommercialInvoice) WHERE inv.discrepancy_flag = true RETURN count(inv) AS count",
            "Bills of Lading": "MATCH (bl:BillOfLading) RETURN count(bl) AS count",
            "  - Late Shipments": "MATCH (bl:BillOfLading) WHERE bl.late_shipment = true RETURN count(bl) AS count",
            "Packing Lists": "MATCH (pl:PackingList) RETURN count(pl) AS count",
            "Sanctions Entities": "MATCH (s:SanctionEntity) RETURN count(s) AS count",
            "Sanctions Matches": "MATCH ()-[r:SCREENED_AGAINST]->() RETURN count(r) AS count",
            "Fraud Flags": "MATCH (lc:LetterOfCredit) WHERE lc.fraud_flag = true RETURN count(lc) AS count",
        }
        
        with self.driver.session() as session:
            for label, query in queries.items():
                result = session.run(query)
                count = result.single()['count']
                print(f"{label:.<40} {count}")
        
        print("="*60)


def main():
    # Check if data files exist
    if not os.path.exists(TRANSACTIONS_FILE):
        print(f"❌ Error: {TRANSACTIONS_FILE} not found!")
        print("   Please run the data generation scripts first:")
        print("   1. python -m src.data_generation.generate_sanctions_list")
        print("   2. python -m src.data_generation.enrich_transactions")
        return
    
    print("\n" + "="*60)
    print("  SENTINEL-ZERO TRADE FINANCE INGESTION")
    print("="*60)
    
    ingestor = TradeFinanceIngestor()
    
    try:
        # Optional: Clear existing data
        response = input("\n⚠️  Clear existing Neo4j data? (y/N): ")
        if response.lower() == 'y':
            ingestor.clear_database()
        
        # Load transaction data
        df = pd.read_csv(TRANSACTIONS_FILE)
        print(f"\n📂 Loaded {len(df)} transactions from {TRANSACTIONS_FILE}")
        
        # Step 1: Create schema
        ingestor.create_constraints()
        
        # Step 2: Ingest entities
        ingestor.ingest_entities(df)
        
        # Step 3: Ingest documents
        ingestor.ingest_letter_of_credits(df)
        ingestor.ingest_commercial_invoices(df)
        ingestor.ingest_bills_of_lading(df)
        ingestor.ingest_packing_lists(df)
        
        # Step 4: Load sanctions and screen
        ingestor.ingest_sanctions()
        
        # Step 5: Add risk flags
        ingestor.create_risk_flags()
        
        # Step 6: Verify
        ingestor.verify_ingestion()
        
        print("\n🎉 INGESTION COMPLETE!")
        print(f"\n🌐 Open Neo4j Browser: http://localhost:7474")
        print(f"   Username: {NEO4J_USER}")
        print(f"   Password: {NEO4J_PASSWORD}")
        
    except Exception as e:
        print(f"\n❌ Error during ingestion: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        ingestor.close()


if __name__ == "__main__":
    main()
>>>>>>> origin/main
