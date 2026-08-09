"""Self-check for the anti-hallucination gate. Run: python test_rag.py

Pure-function tests only — no model/index loading, no network.
"""
from rag import REFUSAL, _build_messages, _passes_threshold


def demo():
    # below threshold -> gate refuses, no LLM call is even reachable
    assert _passes_threshold([{"score": 0.2}], threshold=0.35) is False
    # above threshold -> gate opens
    assert _passes_threshold([{"score": 0.5}], threshold=0.35) is True
    # empty retrieval (empty/corrupt index) -> refuse, never crash
    assert _passes_threshold([], threshold=0.35) is False
    # boundary is inclusive
    assert _passes_threshold([{"score": 0.35}], threshold=0.35) is True

    # prompt building cites each chunk's source file and puts the raw
    # question (not the context) in the user-turn slot
    retrieved = [{"source_file": "a.md", "chunk_text": "UVT is $49,799."}]
    system_context, user_prompt = _build_messages("What is the UVT?", retrieved)
    assert "[a.md]" in system_context
    assert "UVT is $49,799." in system_context
    assert user_prompt == "What is the UVT?"

    assert REFUSAL == "I don't have that information."

    print("ok")


if __name__ == "__main__":
    demo()
