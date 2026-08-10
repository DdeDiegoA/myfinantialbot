"""Eval harness for rag.py: scores grounding + citation presence over tests/qa.json.

Runnable as: python eval.py
"""
import json
import re
import sys
from pathlib import Path

from rag import answer_question, retrieve, REFUSAL

QA_PATH = Path("tests/qa.json")
GROUNDING_OVERLAP_THRESHOLD = 0.5  # ponytail: token-overlap heuristic, not semantic entailment

_WORD_RE = re.compile(r"[a-záéíóúñ0-9]+", re.IGNORECASE)


def _tokens(text: str) -> set[str]:
    return set(_WORD_RE.findall(text.lower()))


def _grounding_score(answer: str, retrieved: list[dict]) -> float:
    """Fraction of the answer's tokens that also appear in the retrieved context."""
    answer_tokens = _tokens(answer)
    if not answer_tokens:
        return 0.0
    context_tokens = set()
    for r in retrieved:
        context_tokens |= _tokens(r["chunk_text"])
    return len(answer_tokens & context_tokens) / len(answer_tokens)


def _cited_docs(answer: str) -> set[str]:
    """Extract (Fuente: <url>)-style inline citations from the answer text."""
    return set(re.findall(r"\(Fuente:\s*(\S+)\)", answer))


def score_case(case: dict) -> tuple[float, str]:
    """Return (score in [0,1], note) for one QA case."""
    question = case["question"]
    retrieved = retrieve(question)
    result = answer_question(question)
    answer = result["answer"]

    if case["expected_type"] == "refusal":
        ok = answer == REFUSAL
        return (1.0 if ok else 0.0), ("exact refusal" if ok else f"expected refusal, got: {answer[:80]!r}")

    # expected_type == "answer"
    grounding = _grounding_score(answer, retrieved)
    grounding_ok = grounding >= GROUNDING_OVERLAP_THRESHOLD

    retrieved_docs = {r["source_url"] for r in retrieved}
    cited = _cited_docs(answer)
    citation_ok = bool(cited) and cited.issubset(retrieved_docs)

    score = 0.5 * grounding_ok + 0.5 * citation_ok
    note = f"grounding={grounding:.2f}({'ok' if grounding_ok else 'fail'}) citation={'ok' if citation_ok else 'fail'} cited={cited or '{}'}"
    return score, note


def main() -> float:
    cases = json.loads(QA_PATH.read_text(encoding="utf-8"))
    total = 0.0
    errors = 0
    for case in cases:
        try:
            score, note = score_case(case)
        except Exception as e:  # noqa: BLE001 -- a single API hiccup must not kill a 23-case run
            score, note, errors = 0.0, f"ERROR (not scored as a real fail): {e}", errors + 1
        total += score
        print(f"[{score:.2f}] {case['question'][:60]!r} — {note}")

    overall = 100 * total / len(cases)
    print(f"\nOverall score: {overall:.1f} / 100 ({len(cases)} cases, {errors} errored)")
    return overall


if __name__ == "__main__":
    main()
