from typing import Iterable

def simple_chunks(text: str, chunk_size: int = 1000, overlap: int = 200) -> Iterable[str]:
    text = text.strip()
    if not text:
        return []
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + chunk_size, n)
        chunk = text[start:end]
        chunks.append(chunk)
        if end == n:
            break
        start = end - overlap
    return chunks
