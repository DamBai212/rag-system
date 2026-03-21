import json
from pathlib import Path


def chunk_text(text: str, size: int = 300, overlap: int = 50) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        chunks.append(text[start:end].strip())
        start += size - overlap
    return [c for c in chunks if c]


def load_and_chunk(filepath: str, chunk_size: int = 300) -> list[dict]:
    path = Path(filepath)
    text = path.read_text(encoding='utf-8')
    raw_chunks = chunk_text(text, size=chunk_size)
    return [
        {
            "id": f"{path.stem}_{i}",
            "text": chunk,
            "source": path.name,
            "chunk_index": i,
        }
        for i, chunk in enumerate(raw_chunks)
    ]


if __name__ == '__main__':
    chunks = load_and_chunk('data/docs.txt')
    print(f'Created {len(chunks)} chunks')
    print('First chunk:', chunks[0])
    with open('data/chunks.json', 'w') as f:
        json.dump(chunks, f, indent=2)
    print('Saved to data/chunks.json')
