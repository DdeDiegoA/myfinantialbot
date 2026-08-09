"""Minimal self-check for ingest.chunk_text. Run: python test_ingest.py"""
from ingest import chunk_text


def demo():
    # paragraphs under limit stay merged into one chunk
    small = "para one.\n\npara two."
    chunks = chunk_text(small, max_chars=1000)
    assert chunks == ["para one.\n\npara two."], chunks

    # a paragraph longer than max_chars gets hard-sliced, none exceed the limit
    long_para = "x" * 2500
    chunks = chunk_text(long_para, max_chars=1000)
    assert all(len(c) <= 1000 for c in chunks), chunks
    assert "".join(chunks) == long_para

    # normal paragraphs split into separate chunks once the limit is hit
    paras = "\n\n".join(["a" * 600] * 3)
    chunks = chunk_text(paras, max_chars=1000)
    assert len(chunks) == 3, len(chunks)

    print("ok")


if __name__ == "__main__":
    demo()
