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
