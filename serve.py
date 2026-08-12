"""FastAPI wrapper around rag.answer_question — no reimplementation of
retrieval/anti-hallucination logic, just HTTP plumbing (public-endpoint spec).

Run: uvicorn serve:app --host 0.0.0.0 --port 8000
"""
import json
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from rag import REFUSAL, answer_question, stream_answer_question

logger = logging.getLogger(__name__)

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
    try:
        return answer_question(req.question)
    except Exception:
        # Without this the client gets a bare 500 with no usable body for any
        # failure below (missing env var, unreachable LLM, malformed provider
        # response) -- indistinguishable from the server being down.
        logger.exception("answer_question failed")
        raise HTTPException(status_code=500, detail="Internal error, please try again.")


@app.post("/ask/stream")
def ask_stream(req: AskRequest):
    """Newline-delimited JSON events (see rag.stream_answer_question for the
    event shapes) so the frontend can render the answer as it's generated
    instead of waiting for the full response.
    """
    def event_source():
        try:
            for event in stream_answer_question(req.question):
                if event["type"] == "refusal":
                    # `replace`, not `delta`: a refusal can be decided after
                    # deltas already went out (leaked model reasoning that
                    # turned out to end in the NO_INFO sentinel). Appending
                    # would leave that reasoning above the refusal, so the
                    # client must drop what it rendered and show only this.
                    yield json.dumps({"type": "replace", "text": REFUSAL}) + "\n"
                    yield json.dumps({"type": "done", "sources": []}) + "\n"
                    return
                yield json.dumps(event) + "\n"
        except Exception:
            # StreamingResponse commits HTTP 200 + headers before this
            # generator is first advanced, so a raise here can't become an
            # error status -- it aborts the connection mid-body with no
            # `done` event, which the frontend can only see as a stream that
            # stopped for no reason (the "question gets no answer" report).
            # Degrade to the canonical refusal plus a well-formed terminator
            # the existing client parser already handles.
            logger.exception("stream_answer_question failed")
            yield json.dumps({"type": "replace", "text": REFUSAL}) + "\n"
            yield json.dumps({"type": "done", "sources": [], "error": True}) + "\n"

    return StreamingResponse(event_source(), media_type="application/x-ndjson")
