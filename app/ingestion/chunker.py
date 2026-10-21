"""Split document text into chunks small enough to embed and cite.

Paragraph-aware: we pack whole paragraphs up to `max_chars`, so a chunk usually reads as a
self-contained thought. A paragraph longer than the limit is cut with a small overlap so a
sentence straddling the cut still appears intact in one of the pieces.
"""


def chunk_text(text: str, max_chars: int = 1200, overlap: int = 150) -> list[str]:
    if overlap >= max_chars:
        raise ValueError("overlap must be smaller than max_chars")

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        if len(para) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(_hard_split(para, max_chars, overlap))
            continue
        candidate = f"{current}\n\n{para}" if current else para
        if len(candidate) <= max_chars:
            current = candidate
        else:
            chunks.append(current)
            current = para

    if current:
        chunks.append(current)
    return chunks


def _hard_split(text: str, max_chars: int, overlap: int) -> list[str]:
    step = max_chars - overlap
    return [text[i : i + max_chars] for i in range(0, len(text), step) if text[i : i + max_chars]]
