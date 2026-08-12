"""Retrieval + anti-hallucination core: embed query, FAISS top-k retrieval,
threshold-gate before ever calling the LLM.

Runnable as: python rag.py "<question>"

Importable by serve.py (Bonus B) as `from rag import answer_question` so the
CLI and the public endpoint share identical retrieval/refusal behavior.
"""
import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

INDEX_PATH = Path("index.faiss")
CHUNKS_PATH = Path("chunks.json")
MODEL_NAME = "all-MiniLM-L6-v2"

# 6, not 3: this corpus has overlapping content across docs (e.g. the
# "six conditions" overview doc restates every threshold briefly, competing
# in the ranking with each threshold's own dedicated doc that has the
# actual number) -- observed empirically: the correct doc for a specific
# threshold question can rank as low as #5. A wider top_k costs nothing at
# this corpus size (31 chunks) and gives the LLM's own NO_INFO judgment
# call the actual answer to work with instead of two near-miss chunks.
TOP_K = 6
REFUSAL = "I don't have that information."
NO_INFO_SENTINEL = "NO_INFO"

# Calibrated against tests/qa.json (23 real cases): this is a single-domain
# corpus (Colombian DIAN tax law only), so every question -- in-corpus or
# not -- scores topically similar (observed range 0.51-0.83 across BOTH
# answer and refusal cases, fully overlapping). A similarity threshold alone
# cannot separate "topically related" from "factually covered" here.
# FLOOR is a cheap deterministic backstop for the clearly-unrelated tail
# (blocks the observed refusal-case low of 0.513 without touching the
# observed answer-case low of 0.650); everything above it is judged by the
# LLM itself via the NO_INFO_SENTINEL instruction in _build_messages, which
# is the layer that actually does the fact-coverage judgment.
RELEVANCE_THRESHOLD = float(os.environ.get("RAG_THRESHOLD", "0.55"))

# Secondary, lower floor for colloquial phrasing ("cuanto vale un uvt" vs the
# calibration set's formal "¿Cuál es el valor de la UVT para 2025?"): observed
# scoring ~0.30-0.35 points lower than the formal phrasing of the SAME
# in-corpus question, below RELEVANCE_THRESHOLD entirely. Only trusted when
# the chunk is ALSO the single best semantic match across the whole corpus
# (faiss_rank 0) -- i.e. nothing else scores better, so a soft floor is safe:
# a truly unrelated query won't rank any corpus chunk this way. The LLM's own
# NO_INFO judgment remains the real fact-coverage gate either way.
SOFT_FLOOR = float(os.environ.get("RAG_SOFT_FLOOR", "0.40"))

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


_WORD_RE = re.compile(r"[a-záéíóúñ0-9]+", re.IGNORECASE)
RRF_K = 60  # standard Reciprocal Rank Fusion constant

# Spanish function/interrogative words: present in nearly every chunk and in
# nearly every question, so left unfiltered they pad every doc's keyword-
# overlap count roughly equally and drown out the one or two content words
# that actually distinguish a match (e.g. "un" tied "impuesto al patrimonio"
# with "valor de la UVT" on overlap count for the query "cuanto vale un uvt",
# letting a coincidental tie beat FAISS's correctly-ranked #1 semantic match
# in RRF fusion).
_STOPWORDS = {
    "a", "al", "algo", "como", "con", "cual", "cuál", "cuales", "cuáles",
    "cuanto", "cuánto", "cuanta", "cuánta", "de", "del", "el", "en", "es",
    "esta", "está", "este", "esto", "la", "las", "lo", "los", "para", "por",
    "que", "qué", "se", "son", "su", "sus", "un", "una", "unos", "unas",
    "y", "o",
}


def _tokens(text: str) -> set[str]:
    return set(_WORD_RE.findall(text.lower()))


def _content_tokens(text: str) -> set[str]:
    return _tokens(text) - _STOPWORDS


def retrieve(question: str, top_k: int = TOP_K) -> list[dict]:
    """Return top_k chunks as [{score, chunk_text, source_file, source_url}], best first.

    Hybrid FAISS (semantic) + keyword-overlap (lexical) ranking, fused via
    Reciprocal Rank Fusion. Pure semantic ranking alone was observed to bury
    the exact-answer chunk as low as rank #12/33 for on-topic questions: this
    corpus repeats generic framing ("declarar renta AG 2025") across nearly
    every doc, which dilutes cosine similarity for the specific doc whose
    *title* lexically matches the question but whose prose doesn't dominate
    the embedding. Keyword overlap catches exactly that case; FAISS still
    catches paraphrased questions with no shared vocabulary. Both signals are
    computed over the WHOLE corpus (33 chunks -- trivial at this scale, no
    top_k pre-filtering needed on either side before fusing).
    """
    model, index, chunks = _load()
    n = len(chunks)
    query_vec = model.encode([question], convert_to_numpy=True, normalize_embeddings=True)
    faiss_scores, faiss_idxs = index.search(query_vec, n)
    faiss_rank = {int(i): rank for rank, i in enumerate(faiss_idxs[0]) if i != -1}
    faiss_score_by_idx = {int(i): float(s) for s, i in zip(faiss_scores[0], faiss_idxs[0]) if i != -1}

    q_content = _content_tokens(question)
    kw_overlap = sorted(
        range(n),
        # Ties (common: many chunks share exactly one content word) broke by
        # raw array position before this fix -- i.e. by chunks.json's
        # processing order, not relevance. Breaking ties by FAISS rank
        # instead lets the semantic signal decide among equally-keyword-
        # matched chunks, which is the whole point of fusing the two.
        key=lambda i: (
            -len(q_content & _content_tokens(chunks[i]["chunk_text"])),
            faiss_rank.get(i, n),
        ),
    )
    kw_rank = {i: rank for rank, i in enumerate(kw_overlap)}

    fused_order = sorted(
        range(n),
        key=lambda i: -(1 / (RRF_K + faiss_rank.get(i, n)) + 1 / (RRF_K + kw_rank.get(i, n))),
    )

    results = []
    for i in fused_order[:top_k]:
        results.append({
            "score": faiss_score_by_idx.get(i, 0.0),
            "is_best_semantic_match": faiss_rank.get(i) == 0,
            **chunks[i],
        })
    return results


def _passes_threshold(retrieved: list[dict], threshold: float = RELEVANCE_THRESHOLD) -> bool:
    """The anti-hallucination gate: the best match must either clear the
    formal-phrasing-calibrated bar outright, or be the single best semantic
    match anywhere in the corpus while still clearing a lower soft floor
    (catches colloquial phrasings scoring below calibration -- see SOFT_FLOOR).
    """
    if not retrieved:
        return False
    top = retrieved[0]
    if top["score"] >= threshold:
        return True
    return top.get("is_best_semantic_match", False) and top["score"] >= SOFT_FLOOR


def _build_messages(question: str, retrieved: list[dict]) -> tuple[str, str]:
    """Build (system_context, user_prompt) for llm.get_completion(prompt, context)."""
    context_block = "\n\n".join(
        f"[{r['source_url']}]\n{r['chunk_text']}" for r in retrieved
    )
    system_context = (
        "You are a Colombian tax (DIAN) assistant. Answer using ONLY the context "
        "below — do not use outside knowledge, and do not infer or extrapolate "
        "facts the context does not literally state, even if a related topic is "
        "covered. Watch specifically for different taxes/concepts that share a "
        "word (e.g. \"patrimonio bruto\" — a renta-filing threshold — is NOT "
        "\"impuesto al patrimonio\", a separate wealth tax): a shared word does "
        "not mean the context answers the question.\n\n"
        f"If the context does not contain the SPECIFIC fact needed to answer, "
        f"respond with exactly this token and nothing else: {NO_INFO_SENTINEL}\n\n"
        "Otherwise: answer in 2-3 sentences maximum, no preamble, no boilerplate, "
        "no inline citations or source markers — the sources are listed "
        "separately after your answer.\n\n"
        f"Context:\n{context_block}"
    )
    return system_context, question


def _apa_citation(source_file: str, source_url: str) -> str:
    """Best-effort APA-style web reference: no per-doc author/date metadata
    exists in the corpus, so author defaults to DIAN (issuer of nearly every
    doc here) and date to "s.f." (sin fecha) per APA's own rule for undated
    web sources, rather than inventing a date.
    """
    title = Path(source_file).stem.replace("-", " ").replace("_", " ").strip().capitalize()
    return f"DIAN. (s.f.). {title}. {source_url}"


def _format_sources_block(retrieved: list[dict]) -> str:
    """Aggregate distinct docs used, APA-style, dedup by source_file (one doc = one citation)."""
    seen = {}
    for r in retrieved:
        seen.setdefault(r["source_file"], r["source_url"])
    citations = [_apa_citation(f, u) for f, u in seen.items()]
    return "Fuentes:\n" + "\n".join(f"- {c}" for c in citations)


def answer_question(question: str, top_k: int = TOP_K, threshold: float = RELEVANCE_THRESHOLD) -> dict:
    """Core entry point shared by rag.py CLI and serve.py. Always returns {answer, sources}."""
    retrieved = retrieve(question, top_k=top_k)

    if not _passes_threshold(retrieved, threshold):
        return {"answer": REFUSAL, "sources": []}

    from llm import get_completion  # deferred: only needed on the above-threshold path

    system_context, user_prompt = _build_messages(question, retrieved)
    answer = get_completion(user_prompt, system_context)

    # Second gate layer: the embedding floor only catches clearly-unrelated
    # queries (see RELEVANCE_THRESHOLD comment). For topically-similar but
    # factually-uncovered questions, the LLM itself judges coverage and
    # signals it via this sentinel instead of freeform refusal prose --
    # normalized here to the same canonical REFUSAL the floor path returns,
    # so callers (eval.py, serve.py) see one deterministic refusal shape.
    if answer.strip() == NO_INFO_SENTINEL:
        return {"answer": REFUSAL, "sources": []}

    sources = [{"source_url": r["source_url"], "snippet": r["chunk_text"][:200]} for r in retrieved]
    full_answer = f"{answer.strip()}\n\n{_format_sources_block(retrieved)}"
    return {"answer": full_answer, "sources": sources}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print('Usage: python rag.py "<question>"')
        sys.exit(1)

    result = answer_question(sys.argv[1])
    print(result["answer"])
