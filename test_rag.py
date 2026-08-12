"""Self-check for the anti-hallucination gate. Run: python test_rag.py

Pure-function tests only — no model/index loading, no network.
"""
import rag
from rag import (
    NO_INFO_SENTINEL,
    REFUSAL,
    SOFT_FLOOR,
    _build_messages,
    _is_small_talk,
    _passes_threshold,
    stream_answer_question,
)


def _stream_events(deltas):
    """Drive stream_answer_question with a canned LLM stream (no network).

    Stubs retrieval + the LLM so only the buffering/sentinel logic is under
    test -- that logic decides whether a user sees an answer, a refusal, or
    leaked model reasoning, and it can't be covered without faking the stream.
    """
    import llm
    chunk = {"source_file": "a.md", "source_url": "https://dian.gov.co/a",
             "chunk_text": "UVT 2025 = $49.799", "score": 0.9}
    orig_retrieve, orig_stream = rag.retrieve, llm.stream_completion
    rag.retrieve = lambda q, top_k=None: [chunk]
    llm.stream_completion = lambda p, c: iter(deltas)
    try:
        return list(stream_answer_question("¿cuánto vale la UVT?"))
    finally:
        rag.retrieve, llm.stream_completion = orig_retrieve, orig_stream


def demo():
    # below threshold -> gate refuses, no LLM call is even reachable
    assert _passes_threshold([{"score": SOFT_FLOOR - 0.1}]) is False
    # above threshold -> gate opens
    assert _passes_threshold([{"score": SOFT_FLOOR + 0.1}]) is True
    # empty retrieval (empty/corrupt index) -> refuse, never crash
    assert _passes_threshold([]) is False
    # boundary is inclusive
    assert _passes_threshold([{"score": SOFT_FLOOR}]) is True

    # a real question must never be mistaken for a greeting/capability probe:
    # "cómo funciona X" once matched the capability regex and got a stub reply
    assert _is_small_talk("¿cómo funciona la declaración de renta?") is False
    assert _is_small_talk("¿cómo funcionas?") is True
    assert _is_small_talk("hola") is True

    # --- streaming: what the user actually ends up seeing ---
    def types(evs):
        return [e["type"] for e in evs]

    def text(evs):
        return "".join(e["text"] for e in evs if e["type"] == "delta")

    # clean sentinel -> refusal, and the token never reaches the user
    assert types(_stream_events([NO_INFO_SENTINEL])) == ["refusal"]

    # Sentinel wrapped in leaked chain-of-thought. The preamble is longer
    # than the sentinel, so it necessarily streams before the sentinel is
    # visible -- streaming can't un-send it. The guarantee is that the stream
    # ENDS in a refusal (which serve.py sends as `replace`, so the client
    # discards the leaked text) and never emits a `done` presenting the
    # reasoning as a real answer. Regression guard: the old prefix-check
    # ended with `done`, leaving reasoning + literal NO_INFO in the chat.
    evs = _stream_events(["We need ", "to answer. ", NO_INFO_SENTINEL])
    assert evs[-1]["type"] == "refusal", types(evs)
    assert "done" not in types(evs), types(evs)
    assert NO_INFO_SENTINEL not in "".join(
        e.get("text", "") for e in evs
    ), "sentinel token must never be emitted to the client"

    # empty stream (all chunks had content=None) -> refusal, never a bare
    # sources block with no answer above it
    assert types(_stream_events([])) == ["refusal"]
    assert types(_stream_events(["", "  "])) == ["refusal"]

    # a genuine answer still streams through intact, with sources appended
    evs = _stream_events(["La UVT 2025 ", "vale $49.799."])
    assert "La UVT 2025 vale $49.799." in text(evs)
    assert evs[-1]["type"] == "done"
    assert NO_INFO_SENTINEL not in text(evs)

    # prompt building cites each chunk's source URL (not the .md filename)
    # and puts the raw question (not the context) in the user-turn slot
    retrieved = [{"source_file": "a.md", "source_url": "https://dian.gov.co/a", "chunk_text": "UVT is $49,799."}]
    system_context, user_prompt = _build_messages("What is the UVT?", retrieved)
    assert "[https://dian.gov.co/a]" in system_context
    assert "UVT is $49,799." in system_context
    assert "a.md" not in system_context  # never cite the internal filename
    assert user_prompt == "What is the UVT?"
    assert NO_INFO_SENTINEL in system_context  # LLM is instructed to use the sentinel

    assert REFUSAL == "I don't have that information."

    print("ok")


if __name__ == "__main__":
    demo()
