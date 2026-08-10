"""Self-check for the anti-hallucination gate. Run: python test_rag.py

Pure-function tests only — no model/index loading, no network.
"""
from rag import NO_INFO_SENTINEL, REFUSAL, _build_messages, _passes_threshold


def demo():
    # below threshold -> gate refuses, no LLM call is even reachable
    assert _passes_threshold([{"score": 0.2}], threshold=0.35) is False
    # above threshold -> gate opens
    assert _passes_threshold([{"score": 0.5}], threshold=0.35) is True
    # empty retrieval (empty/corrupt index) -> refuse, never crash
    assert _passes_threshold([], threshold=0.35) is False
    # boundary is inclusive
    assert _passes_threshold([{"score": 0.35}], threshold=0.35) is True

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
