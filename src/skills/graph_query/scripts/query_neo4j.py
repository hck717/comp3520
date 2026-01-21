import os
from neo4j import GraphDatabase

# --- CONFIGURATION ---
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PWD = os.getenv("NEO4J_PASSWORD", "password")

def run_cypher(query: str):
    """
    Executes a read-only Cypher query against the Neo4j database.
    
    Args:
        query (str): The Cypher query string (e.g., "MATCH (n) RETURN n LIMIT 5")
        
    Returns:
        list: A list of dictionaries representing the result records.
    """
    if "CREATE" in query.upper() or "MERGE" in query.upper() or "DELETE" in query.upper() or "SET" in query.upper():
        return {"error": "Safety violation: Only READ operations (MATCH/RETURN) are allowed."}

    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PWD))
        with driver.session() as session:
            result = session.run(query)
            # Convert Neo4j records to a list of clean dictionaries
            data = [record.data() for record in result]
            return data
    except Exception as e:
        return {"error": str(e)}
    finally:
        driver.close()

if __name__ == "__main__":
    # Test query
    print(run_cypher("MATCH (n:Entity) RETURN n.name, n.type LIMIT 5"))
