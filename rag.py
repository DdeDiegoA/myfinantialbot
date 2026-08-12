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

# Effectively "the whole corpus": at this scale (41 chunks, ~7.4K tokens
# total) there's no real cost to giving the LLM everything instead of
# gambling on ranking. Needed for compound questions ("si gano 3 salarios
# mínimos, ¿debo declarar renta?") that require combining facts from TWO
# unrelated-looking docs (SMMLV value + the UVT income threshold) -- observed
# empirically: the threshold doc can rank as low as #16 by any single
# ranking signal, well past any top_k small enough to matter for cost. The
# threshold gate below is unaffected (it scores the single best chunk over
# the WHOLE corpus regardless of top_k), so off-topic queries still refuse;
# this only widens what in-domain queries get to reason over. Revisit if the
# corpus grows enough that full-context cost/latency becomes real.
TOP_K = 999
REFUSAL = "I don't have that information."
NO_INFO_SENTINEL = "NO_INFO"

# Calibrated against tests/qa.json (23 real cases): this is a single-domain
# corpus (Colombian DIAN tax law only), so every question -- in-corpus or
# not -- scores topically similar (observed range 0.51-0.83 across BOTH
# answer and refusal cases, fully overlapping, and the overlap only widened
# as the corpus grew past ~4 topic categories: on-topic colloquial scores
# like 0.541 for a CIIU question started sitting right next to off-topic
# scores of 0.481/0.444). A similarity threshold alone cannot separate
# "topically related" from "factually covered" here -- verified directly
# (bypassing this gate entirely) that the LLM's own NO_INFO judgment reliably
# refuses off-topic questions even when handed the full corpus as context. So
# SOFT_FLOOR only needs to cheaply catch truly-nonsensical input before
# spending an LLM call on it; real fact-coverage judgment is the LLM's job
# via the NO_INFO_SENTINEL instruction in _build_messages either way.
SOFT_FLOOR = float(os.environ.get("RAG_SOFT_FLOOR", "0.35"))

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
        results.append({"score": faiss_score_by_idx.get(i, 0.0), **chunks[i]})
    return results


def _passes_threshold(retrieved: list[dict]) -> bool:
    """Cheap pre-filter, not the real gate: only blocks near-nonsensical
    input (SOFT_FLOOR) from reaching the LLM at all. Real fact-coverage
    judgment happens downstream via the LLM's own NO_INFO sentinel -- see
    SOFT_FLOOR comment for why this was simplified from a two-tier check.
    """
    return bool(retrieved) and retrieved[0]["score"] >= SOFT_FLOOR


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
        "Always answer in the same language the question was asked in (Spanish "
        "or English) — never translate or mix languages.\n\n"
        "The question may be COMPOUND: it may state a personal figure (income, "
        "salary in 'salarios mínimos', assets, etc.) and ask whether that figure "
        "crosses a threshold from the context. In that case, using ONLY numeric "
        "facts literally stated in the context: first write out each raw number "
        "you're using and where it comes from (one short line per number — e.g. "
        "'SMMLV 2025 = $1.423.500', 'umbral = 1.400 UVT', 'UVT 2025 = $49.799'), "
        "then write out the calculation as an explicit expression with the "
        "actual numbers substituted in (e.g. '3 × $1.423.500 × 12 = $51.246.000' "
        "then '$51.246.000 / $49.799 = 1029 UVT'), THEN state the comparison and "
        "final personalized yes/no answer. Never skip straight to a conclusion "
        "without showing this arithmetic — silently-wrong mental math is worse "
        "than showing the work. If the question mixes monthly and annual "
        "figures (e.g. a monthly salary vs an annual income threshold), "
        "annualize before comparing and say so explicitly. If any number the "
        "arithmetic needs is missing from the context, do not invent or "
        "estimate it — say which figure you'd need instead.\n\n"
        "IMPORTANT — check this BEFORE applying the NO_INFO rule below: the "
        "question may be ACCOUNT-SPECIFIC, asking about THIS taxpayer's own "
        "current state with DIAN — including blunt yes/no phrasing like "
        "'¿tengo X disponible?' or 'do I have X?' — such as their pending "
        "balance/saldo, whether they have a declaración sugerida available, "
        "their RUT status, refund eligibility, etc., rather than a general "
        "rule. Even phrased as yes/no, you cannot answer it as yes/no. You "
        "have no "
        "access to any taxpayer's account or portal session, so you can NEVER "
        "state or imply the actual figure/status. But this does NOT mean "
        "NO_INFO: if the context describes the PROCESS/portal path to check "
        "it (which section, which virtual service, what's required), that "
        "process description IS the fact this question needs — explain it, "
        "and say plainly that only the taxpayer's own portal login shows the "
        "real figure. Only fall through to NO_INFO if the context has no "
        "process description for it either.\n\n"
        f"For every other case: if the context does not contain the SPECIFIC "
        f"fact needed to answer, respond with exactly this token and nothing "
        f"else: {NO_INFO_SENTINEL}\n\n"
        "Otherwise: answer in 2-4 sentences maximum, no preamble, no boilerplate, "
        "no inline citations or source markers — the sources are listed "
        "separately after your answer. Exception: for a COMPOUND question, the "
        "required arithmetic lines above don't count against this limit — keep "
        "the final conclusion itself to 1-2 sentences after showing the work.\n\n"
        f"Context:\n{context_block}"
    )
    return system_context, question


_GREETING_RE = re.compile(
    r"^\s*(hola|buen[oa]s?\s*(d[ií]as?|tardes?|noches?)?|hey|hi|hello|"
    r"qu[eé]\s*tal|saludos)\W*$",
    re.IGNORECASE,
)
_CAPABILITY_RE = re.compile(
    r"\b(qu[eé]\s+puedes?\s+hacer|qu[eé]\s+(cosas?|preguntas?)\s+(puedo|se\s+puede)|"
    r"c[oó]mo\s+funcionas\b|qui[eé]n\s+eres|ay[uú]da|help|what\s+can\s+you\s+do|"
    r"what\s+do\s+you\s+do|who\s+are\s+you|how\s+do\s+you\s+work)\W*$",
    re.IGNORECASE,
)


def _is_small_talk(question: str) -> bool:
    """Greetings and meta/capability questions ('hola', 'qué puedes hacer',
    'what can you do') don't need retrieval -- there's no DIAN fact to look
    up, and running them through the threshold gate just produces a refusal
    for something that isn't actually a factual question. Cheap regex check,
    no extra LLM call, so it doesn't add latency to real questions.
    """
    return bool(_GREETING_RE.match(question) or _CAPABILITY_RE.search(question))


def _small_talk_answer(question: str) -> str:
    from llm import get_completion  # deferred: same reason as the RAG path

    system_context = (
        "You are MyFinancialBot, an assistant that answers questions about "
        "Colombian tax law (DIAN): UVT value, who must file income tax "
        "returns (declarar renta), wealth tax (impuesto al patrimonio), "
        "gross income/assets thresholds, and related SMMLV (minimum wage) "
        "figures used in those calculations. Respond in the same language "
        "the message was written in (Spanish or English). If greeted, greet "
        "back briefly and mention in one sentence what you can help with. If "
        "asked what you can do, briefly list the topics above. Do not answer "
        "any actual tax question here — you have no factual context loaded; "
        "if the message contains a real question, say you'll look it up "
        "instead of answering it. Keep the whole reply to 1-3 sentences."
    )
    return get_completion(question, system_context)


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


def answer_question(question: str, top_k: int = TOP_K) -> dict:
    """Core entry point shared by rag.py CLI and serve.py. Always returns {answer, sources}."""
    if _is_small_talk(question):
        return {"answer": _small_talk_answer(question), "sources": []}

    retrieved = retrieve(question, top_k=top_k)

    if not _passes_threshold(retrieved):
        return {"answer": REFUSAL, "sources": []}

    from llm import get_completion  # deferred: only needed on the above-threshold path

    system_context, user_prompt = _build_messages(question, retrieved)
    answer = get_completion(user_prompt, system_context)

    # Second gate layer: the embedding floor only catches clearly-unrelated
    # queries (see SOFT_FLOOR comment). For topically-similar but
    # factually-uncovered questions, the LLM itself judges coverage and
    # signals it via this sentinel instead of freeform refusal prose --
    # normalized here to the same canonical REFUSAL the floor path returns,
    # so callers (eval.py, serve.py) see one deterministic refusal shape.
    if answer.strip() == NO_INFO_SENTINEL:
        return {"answer": REFUSAL, "sources": []}

    # `retrieved` is the WHOLE corpus (TOP_K=999) so the LLM can combine
    # facts from anywhere for compound questions -- but citing all 16 docs
    # regardless of relevance would be noise. Sources are display-only, so
    # trim to what's actually plausibly relevant (SOFT_FLOOR, the same bar
    # the gate itself trusts as a real relevance signal).
    cited = [r for r in retrieved if r["score"] >= SOFT_FLOOR] or retrieved[:1]
    sources = [{"source_url": r["source_url"], "snippet": r["chunk_text"][:200]} for r in cited]
    full_answer = f"{answer.strip()}\n\n{_format_sources_block(cited)}"
    return {"answer": full_answer, "sources": sources}


def stream_answer_question(question: str, top_k: int = TOP_K):
    """Streaming twin of answer_question: yields dict events instead of one
    blob, so serve.py can forward text as it's generated. Same retrieval and
    anti-hallucination logic (small-talk shortcut, threshold gate, NO_INFO
    sentinel) -- only the LLM call and response delivery are incremental.

    Events: {"type": "delta", "text": str} (append to the message being
    built), {"type": "refusal"} (render REFUSAL, no further deltas follow),
    {"type": "done", "sources": [...]} (stream finished; sources array for
    the UI's expandable source list).
    """
    if _is_small_talk(question):
        yield {"type": "delta", "text": _small_talk_answer(question)}
        yield {"type": "done", "sources": []}
        return

    retrieved = retrieve(question, top_k=top_k)

    if not _passes_threshold(retrieved):
        yield {"type": "refusal"}
        return

    from llm import stream_completion  # deferred: only needed on the above-threshold path

    system_context, user_prompt = _build_messages(question, retrieved)

    # Can't know if this is a real answer or the NO_INFO sentinel until
    # enough of the stream has arrived to rule one out -- buffer just long
    # enough to disambiguate (sentinel is 7 chars), then flush. Case-
    # sensitive prefix check: a real answer starting differently in case or
    # content diverges within the first character or two.
    buf = ""
    decided_real = False
    for delta in stream_completion(user_prompt, system_context):
        if decided_real:
            yield {"type": "delta", "text": delta}
            continue
        buf += delta
        stripped = buf.strip()
        if stripped and not NO_INFO_SENTINEL.startswith(stripped):
            decided_real = True
            yield {"type": "delta", "text": buf}
            buf = ""

    if not decided_real:
        if buf.strip() == NO_INFO_SENTINEL:
            yield {"type": "refusal"}
            return
        if buf:
            yield {"type": "delta", "text": buf}

    cited = [r for r in retrieved if r["score"] >= SOFT_FLOOR] or retrieved[:1]
    sources = [{"source_url": r["source_url"], "snippet": r["chunk_text"][:200]} for r in cited]
    yield {"type": "delta", "text": f"\n\n{_format_sources_block(cited)}"}
    yield {"type": "done", "sources": sources}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print('Usage: python rag.py "<question>"')
        sys.exit(1)

    result = answer_question(sys.argv[1])
    print(result["answer"])
