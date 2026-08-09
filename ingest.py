"""Ingest docs/dian/*.md into a local FAISS vector index.

Runnable as: python ingest.py

To add new corpus data: drop a new .md file into docs/dian/ and re-run
this script. docs/dian/ is the DIAN tax corpus only -- kept separate
from docs/ itself, which also holds protto's own project-scaffold docs
(architecture/, specs/, context.md, etc.) that must never be indexed.

Chunks every markdown file directly under docs/dian/ (flat, not
recursive) by paragraph, embeds chunks locally with sentence-transformers
(CPU, no API calls), and writes index.faiss + chunks.json so rag.py can
load them for retrieval.
"""
import json
from pathlib import Path

DOCS_DIR = Path("docs/dian")
INDEX_PATH = Path("index.faiss")
CHUNKS_PATH = Path("chunks.json")
MODEL_NAME = "all-MiniLM-L6-v2"


def chunk_text(text: str, max_chars: int = 1000) -> list[str]:
    """Split into paragraphs; merge/split so no chunk exceeds max_chars."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    buf = ""
    for p in paragraphs:
        # ponytail: paragraphs longer than max_chars are hard-sliced, no sentence-aware splitting
        if len(p) > max_chars:
            for i in range(0, len(p), max_chars):
                piece = p[i : i + max_chars]
                if piece.strip():
                    chunks.append(piece.strip())
            continue
        if buf and len(buf) + len(p) + 2 > max_chars:
            chunks.append(buf)
            buf = p
        else:
            buf = f"{buf}\n\n{p}" if buf else p
    if buf:
        chunks.append(buf)
    return chunks


def build_chunks() -> list[dict]:
    records = []
    # Flat, not recursive: docs/ also holds protto scaffold docs in
    # subdirectories (architecture/, specs/, design-system/) that are
    # project meta-docs, not DIAN corpus content.
    for path in sorted(DOCS_DIR.glob("*.md")):
        if path.name == "SOURCES.md":  # metadata about the corpus, not corpus content
            continue
        text = path.read_text(encoding="utf-8")
        for chunk in chunk_text(text):
            records.append({"chunk_text": chunk, "source_file": str(path.relative_to(DOCS_DIR))})
    return records


def main() -> None:
    if not DOCS_DIR.is_dir():
        print(f"{DOCS_DIR}/ does not exist yet; nothing to ingest.")
        return

    records = build_chunks()
    if not records:
        print(f"No .md files found under {DOCS_DIR}/; nothing to ingest.")
        return

    # ponytail: sentence-transformers (torch) must import before faiss on
    # this platform, else the two libraries' bundled OpenMP runtimes clash
    # and segfault on first encode() call.
    from sentence_transformers import SentenceTransformer
    import faiss

    try:
        # Fully offline: use only the locally cached model, no Hub network call.
        model = SentenceTransformer(MODEL_NAME, device="cpu", local_files_only=True)
    except OSError:
        # First run on this machine: model isn't cached yet. One-time download,
        # every subsequent run (this is what "ingestion is offline" means in
        # practice) resolves from cache via local_files_only=True above.
        print(f"'{MODEL_NAME}' not cached locally; downloading once (one-time network call)...")
        model = SentenceTransformer(MODEL_NAME, device="cpu")
    embeddings = model.encode(
        [r["chunk_text"] for r in records],
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    faiss.write_index(index, str(INDEX_PATH))
    CHUNKS_PATH.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")

    n_files = len([p for p in DOCS_DIR.glob("*.md") if p.name != "SOURCES.md"])
    print(f"Indexed {len(records)} chunks from {n_files} files.")
    print(f"Wrote {INDEX_PATH} and {CHUNKS_PATH}.")


if __name__ == "__main__":
    main()
