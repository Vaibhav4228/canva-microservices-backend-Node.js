import os

from sentence_transformers import SentenceTransformer

from log import log

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
_model = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        name = os.getenv("EMBEDDING_MODEL") or DEFAULT_MODEL
        log("embedding_load", model=name)
        _model = SentenceTransformer(name)
        log("embedding_ready", model=name, dim=_model.get_sentence_embedding_dimension())
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    vectors = get_model().encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return [row.tolist() for row in vectors]


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
