import re

_CLAUSE_HEADER_RE = re.compile(
    r"(?=^\s*(?:\d+(?:\.\d+)*[.)]|Section\s+\d+|Article\s+\d+|[A-Z][A-Z \-]{4,}:)\s*$)",
    re.MULTILINE,
)


def chunk_document_text(text: str, target_chars: int = 1600, min_chars: int = 200) -> list[str]:
    """Splits contract text into clause/paragraph-sized chunks for embedding.

    Uses cheap heuristics (numbered clause headers, blank-line paragraph breaks) rather
    than an LLM call, keeping chunking fast and free. Chunks below `min_chars` are merged
    into the previous chunk so short trailing clauses don't become noise-sized embeddings.
    """
    text = text.strip()
    if not text:
        return []

    segments = [seg.strip() for seg in _CLAUSE_HEADER_RE.split(text) if seg.strip()]
    if len(segments) <= 1:
        segments = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

    chunks: list[str] = []
    buffer = ""
    for segment in segments:
        candidate = f"{buffer}\n\n{segment}".strip() if buffer else segment
        if len(candidate) > target_chars and buffer:
            chunks.append(buffer)
            buffer = segment
        else:
            buffer = candidate
    if buffer:
        chunks.append(buffer)

    merged: list[str] = []
    for chunk in chunks:
        if merged and len(chunk) < min_chars:
            merged[-1] = f"{merged[-1]}\n\n{chunk}"
        else:
            merged.append(chunk)

    return merged
