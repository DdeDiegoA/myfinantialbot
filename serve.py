"""FastAPI wrapper around rag.answer_question — no reimplementation of
retrieval/anti-hallucination logic, just HTTP plumbing (public-endpoint spec).

Run: uvicorn serve:app --host 0.0.0.0 --port 8000
"""
import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from rag import REFUSAL, answer_question, stream_answer_question

app = FastAPI(title="MyFinancialBot RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


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


@app.post("/ask/stream")
def ask_stream(req: AskRequest):
    """Newline-delimited JSON events (see rag.stream_answer_question for the
    event shapes) so the frontend can render the answer as it's generated
    instead of waiting for the full response.
    """
    def event_source():
        for event in stream_answer_question(req.question):
            if event["type"] == "refusal":
                yield json.dumps({"type": "delta", "text": REFUSAL}) + "\n"
                yield json.dumps({"type": "done", "sources": []}) + "\n"
                return
            yield json.dumps(event) + "\n"

    return StreamingResponse(event_source(), media_type="application/x-ndjson")
