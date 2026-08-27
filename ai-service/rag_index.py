import hashlib
from pathlib import Path

from chunk import split_text
from embeddings import embed_texts
from ingest import INGEST_DIR
from log import log
from vector_store import upsert_vectors

INGEST_ROOT = INGEST_DIR.resolve()


def _safe_path(raw: str | Path) -> Path:
    path = Path(raw).expanduser().resolve()
    if path != INGEST_ROOT and INGEST_ROOT not in path.parents:
        raise ValueError("ingest path is outside data/ingest")
    if not path.is_file():
        raise FileNotFoundError(str(path))
    return path


def _chunk_id(path: Path, index: int) -> str:
    digest = hashlib.sha1(str(path).encode("utf-8")).hexdigest()[:12]
    return f"{digest}:{index}"


def index_file(path: str | Path, source: str) -> dict:
    file_path = _safe_path(path)
    text = file_path.read_text(encoding="utf-8")
    chunks = split_text(text)
    if not chunks:
        log("index_skip_empty", path=str(file_path), source=source)
        return {"ok": True, "path": str(file_path), "chunks": 0}

    vectors = embed_texts(chunks)
    rows = []
    for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
        rows.append(
            (
                _chunk_id(file_path, i),
                vector,
                {"source": source, "path": file_path.name},
                chunk,
            )
        )
    upsert_vectors(rows)
    log("index_upserted", path=str(file_path), source=source, chunks=len(rows))
    return {"ok": True, "path": str(file_path), "chunks": len(rows)}
