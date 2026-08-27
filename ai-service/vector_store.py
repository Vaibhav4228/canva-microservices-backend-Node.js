import os

from upstash_vector import Index

_index = None


def _env(name: str) -> str:
    return (os.getenv(name) or "").strip().strip('"')


def get_index() -> Index:
    global _index
    if _index is None:
        url = _env("UPSTASH_VECTOR_REST_URL")
        token = _env("UPSTASH_VECTOR_REST_TOKEN")
        if not url or not token:
            raise RuntimeError("UPSTASH_VECTOR_REST_URL and UPSTASH_VECTOR_REST_TOKEN are required")
        _index = Index(url=url, token=token)
    return _index


def upsert_vectors(rows: list[tuple[str, list[float], dict, str]]) -> int:
    get_index().upsert(vectors=rows)
    return len(rows)


def info() -> dict:
    data = get_index().info()
    return {
        "ok": True,
        "vectorCount": int(data.vector_count or 0),
        "pendingCount": int(data.pending_vector_count or 0),
        "dimension": data.dimension,
        "similarity": data.similarity_function,
    }


def query_vectors(vector: list[float], k: int = 4) -> list[dict]:
    rows = get_index().query(
        vector=vector,
        top_k=k,
        include_metadata=True,
        include_data=True,
        include_vectors=False,
    )
    hits = getattr(rows, "hits", rows) or []
    docs = []
    for hit in hits:
        metadata = getattr(hit, "metadata", None) or {}
        text = getattr(hit, "data", None) or metadata.get("text") or ""
        if not str(text).strip():
            continue
        docs.append(
            {
                "id": getattr(hit, "id", None),
                "text": str(text),
                "source": metadata.get("source"),
                "score": getattr(hit, "score", None),
            }
        )
    return docs
