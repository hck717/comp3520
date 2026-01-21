from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os
import json
from src.skills.graph_query.scripts.query_neo4j import run_cypher

# --- CONFIGURATION ---
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
app = FastAPI(title="Banking Graph Agent", version="1.0")

# --- LOAD AGENT SKILLS ---
def load_skill():
    base_path = "src/skills/graph_query"
    with open(f"{base_path}/SKILL.md", "r") as f:
        skill_doc = f.read()
    with open(f"{base_path}/reference.md", "r") as f:
        reference_doc = f.read()
    return skill_doc, reference_doc

SKILL_DOC, REFERENCE_DOC = load_skill()

# --- LLM SETUP ---
llm = ChatOllama(model=OLLAMA_MODEL, temperature=0)

# Prompt 1: Generate Cypher
cypher_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an AI Agent with the 'Graph Query Skill'.
    
    SKILL INSTRUCTIONS:
    {skill_doc}
    
    REFERENCE & SCHEMA:
    {reference_doc}
    
    Your task is to translate the user's natural language question into a valid Cypher query for the Neo4j database.
    - Return ONLY the Cypher query. No markdown, no explanations.
    - Use the schema provided in the reference.
    - Always LIMIT your results to 20 unless specified.
    """),
    ("human", "{question}")
])

# Prompt 2: Answer Question
answer_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a Banking Assistant. You have queried the database to answer the user's question.
    
    USER QUESTION: {question}
    
    DATABASE RESULTS:
    {results}
    
    Answer the user's question clearly and professionally based ONLY on the results above.
    If the results are empty, state that no information was found.
    """),
    ("human", "Answer the question.")
])

# --- ENDPOINTS ---
class ChatRequest(BaseModel):
    query: str

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        # Step 1: Generate Cypher
        print(f"🤖 User Query: {request.query}")
        cypher_chain = cypher_prompt | llm | StrOutputParser()
        cypher_query = cypher_chain.invoke({
            "skill_doc": SKILL_DOC, 
            "reference_doc": REFERENCE_DOC, 
            "question": request.query
        })
        
        # Clean up potential markdown formatting from LLM
        cypher_query = cypher_query.strip().replace("```cypher", "").replace("```", "")
        print(f"🔧 Generated Cypher: {cypher_query}")
        
        # Step 2: Execute Cypher
        results = run_cypher(cypher_query)
        print(f"📊 Results Found: {len(results) if isinstance(results, list) else results}")
        
        if isinstance(results, dict) and "error" in results:
            return {"answer": f"I couldn't process that query. Database error: {results['error']}"}

        # Step 3: Generate Natural Language Answer
        answer_chain = answer_prompt | llm | StrOutputParser()
        final_answer = answer_chain.invoke({
            "question": request.query,
            "results": json.dumps(results)
        })
        
        return {"answer": final_answer, "generated_cypher": cypher_query}

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
