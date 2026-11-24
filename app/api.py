from fastapi import FastAPI
from pydantic import BaseModel
from .agents import run_agent

app = FastAPI(title="Biomedical Agentic RAG System for Vaccine & Drug Discovery Intelligence")

class QueryRequest(BaseModel):
    question: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/ask")
def ask(req: QueryRequest):
    return run_agent(req.question)
