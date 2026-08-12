"""FastAPI wrapper around rag.answer_question — no reimplementation of
retrieval/anti-hallucination logic, just HTTP plumbing (public-endpoint spec).

Run: uvicorn serve:app --host 0.0.0.0 --port 8000
"""
from fastapi import FastAPI
from pydantic import BaseModel

from rag import answer_question

app = FastAPI(title="MyFinancialBot RAG API")


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str
    sources: list[dict]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    return answer_question(req.question)
