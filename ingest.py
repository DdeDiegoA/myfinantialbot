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
import re
from pathlib import Path

DOCS_DIR = Path("docs/dian")
INDEX_PATH = Path("index.faiss")
CHUNKS_PATH = Path("chunks.json")
MODEL_NAME = "all-MiniLM-L6-v2"

SOURCE_COMMENT_RE = re.compile(r"<!--\s*source:\s*(\S+).*?-->", re.DOTALL)


def extract_source_url(text: str) -> str:
    """Pull the source URL from the '<!-- source: URL -->' first-line comment."""
    m = SOURCE_COMMENT_RE.search(text)
    if not m:
        raise ValueError("missing '<!-- source: URL -->' comment")
    return m.group(1)


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


def _with_heading_context(text: str) -> str:
    """Prefix each paragraph with its nearest preceding '#' heading.

    Naive paragraph-boundary chunking loses section context when a chunk
    split falls right after a heading line -- the heading and the content
    under it can land in different chunks, and the content-only chunk then
    embeds poorly against questions phrased using the heading's own words.
    Observed: a chunk that was just a bare enumerated list ranked dead last
    (31/31) against "what are the six conditions", because the phrase "seis
    condiciones" only existed in the "## Las seis condiciones" heading one
    chunk earlier.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    heading = ""
    out = []
    for p in paragraphs:
        if p.startswith("#"):
            heading = p
            out.append(p)
        elif heading and not p.startswith(heading):
            # single \n, not \n\n: chunk_text() re-splits on "\n\n", so a \n\n
            # join here would immediately undo this and re-separate them
            out.append(f"{heading}\n{p}")
        else:
            out.append(p)
    return "\n\n".join(out)


def build_chunks() -> list[dict]:
    records = []
    # Flat, not recursive: docs/ also holds protto scaffold docs in
    # subdirectories (architecture/, specs/, design-system/) that are
    # project meta-docs, not DIAN corpus content.
    for path in sorted(DOCS_DIR.glob("*.md")):
        if path.name == "SOURCES.md":  # metadata about the corpus, not corpus content
            continue
        text = path.read_text(encoding="utf-8")
        source_url = extract_source_url(text)
        body = SOURCE_COMMENT_RE.sub("", text, count=1).strip()  # already captured in source_url
        body = _with_heading_context(body)
        for chunk in chunk_text(body):
            records.append({
                "chunk_text": chunk,
                "source_file": str(path.relative_to(DOCS_DIR)),
                "source_url": source_url,
            })
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
