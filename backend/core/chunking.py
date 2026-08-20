import hashlib


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 75) -> list[str]:
    """Split text into overlapping chunks by word count."""
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


def make_chunk_id(url: str, index: int) -> str:
    """Generate a deterministic chunk ID from URL + index."""
    url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
    return f"{url_hash}_{index}"
