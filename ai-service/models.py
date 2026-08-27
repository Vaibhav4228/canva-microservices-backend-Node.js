from pydantic import BaseModel, Field


class PingRequest(BaseModel):
    message: str = Field(min_length=1, max_length=500)


class PingResponse(BaseModel):
    ok: bool
    echo: str
    service: str


class IngestRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20000)
    source: str = Field(default="manual", max_length=200)


class IngestResponse(BaseModel):
    ok: bool
    source: str
    path: str
    bytes: int
    queued: bool


class VectorInfoResponse(BaseModel):
    ok: bool
    vectorCount: int
    pendingCount: int = 0
    dimension: int | None = None
    similarity: str | None = None


class RagQueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    k: int = Field(default=4, ge=1, le=12)


class RagSource(BaseModel):
    text: str
    source: str | None = None


class RagQueryResponse(BaseModel):
    answer: str
    sources: list[RagSource]
