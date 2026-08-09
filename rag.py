"""Retrieval + anti-hallucination core: embed query, FAISS top-k retrieval,
threshold-gate before ever calling the LLM.

Runnable as: python rag.py "<question>"

Importable by serve.py (Bonus B) as `from rag import answer_question` so the
CLI and the public endpoint share identical retrieval/refusal behavior.
"""
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

INDEX_PATH = Path("index.faiss")
CHUNKS_PATH = Path("chunks.json")
MODEL_NAME = "all-MiniLM-L6-v2"
TOP_K = 3
REFUSAL = "I don't have that information."

# ponytail: cosine-similarity cutoff on normalized MiniLM embeddings, not a
# trained/calibrated value. Tune via RAG_THRESHOLD env var once eval.py
# (eval-harness) has real pass/fail numbers to calibrate against.
RELEVANCE_THRESHOLD = float(os.environ.get("RAG_THRESHOLD", "0.35"))

_state = {}  # lazy-loaded {"model": ..., "index": ..., "chunks": [...]}


def _load():
    """Load model/index/chunks once per process."""
    if _state:
        return _state["model"], _state["index"], _state["chunks"]

    # ponytail: sentence-transformers (torch) must import before faiss on
    # this platform, else the two libraries' bundled OpenMP runtimes clash
    # and segfault on first encode() call (see ingest.py).
    from sentence_transformers import SentenceTransformer
    import faiss

    if not INDEX_PATH.exists() or not CHUNKS_PATH.exists():
        raise FileNotFoundError("index.faiss / chunks.json not found — run `python ingest.py` first.")

    model = SentenceTransformer(MODEL_NAME, device="cpu")
    index = faiss.read_index(str(INDEX_PATH))
    chunks = json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))

    _state["model"], _state["index"], _state["chunks"] = model, index, chunks
    return model, index, chunks


def retrieve(question: str, top_k: int = TOP_K) -> list[dict]:
    """Embed the question and return top_k chunks as [{score, chunk_text, source_file}], best first."""
    model, index, chunks = _load()
    query_vec = model.encode([question], convert_to_numpy=True, normalize_embeddings=True)
    scores, idxs = index.search(query_vec, top_k)
    results = []
    for score, i in zip(scores[0], idxs[0]):
        if i == -1:  # fewer than top_k chunks in the index
            continue
        results.append({"score": float(score), **chunks[i]})
    return results


def _passes_threshold(retrieved: list[dict], threshold: float = RELEVANCE_THRESHOLD) -> bool:
    """The anti-hallucination gate: True only if the best match clears the bar."""
    return bool(retrieved) and retrieved[0]["score"] >= threshold


def _build_messages(question: str, retrieved: list[dict]) -> tuple[str, str]:
    """Build (system_context, user_prompt) for llm.get_completion(prompt, context)."""
    context_block = "\n\n".join(f"[{r['source_file']}]\n{r['chunk_text']}" for r in retrieved)
    system_context = (
        "You are a Colombian tax (DIAN) assistant. Answer using ONLY the context "
        "below — do not use outside knowledge. Cite every claim inline with its "
        "source file in brackets, e.g. [source.md]. If the context only partially "
        "answers the question, say so explicitly instead of filling the gap.\n\n"
        f"Context:\n{context_block}"
    )
    return system_context, question


def answer_question(question: str, top_k: int = TOP_K, threshold: float = RELEVANCE_THRESHOLD) -> dict:
    """Core entry point shared by rag.py CLI and serve.py. Always returns {answer, sources}."""
    retrieved = retrieve(question, top_k=top_k)

    if not _passes_threshold(retrieved, threshold):
        return {"answer": REFUSAL, "sources": []}

    from llm import get_completion  # deferred: only needed on the above-threshold path

    system_context, user_prompt = _build_messages(question, retrieved)
    answer = get_completion(user_prompt, system_context)
    sources = [{"doc": r["source_file"], "snippet": r["chunk_text"][:200]} for r in retrieved]
    return {"answer": answer, "sources": sources}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print('Usage: python rag.py "<question>"')
        sys.exit(1)

    result = answer_question(sys.argv[1])
    print(result["answer"])
    if result["sources"]:
        print("\nSources:")
        for s in result["sources"]:
            print(f"- [{s['doc']}] {s['snippet']}")
