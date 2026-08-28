from pydantic import BaseModel, Field, model_validator


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


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=500)


class GenerateResponse(BaseModel):
    jobId: str
    status: str
    queued: bool


class JobStatusResponse(BaseModel):
    jobId: str
    status: str
    url: str | None = None
    provider: str | None = None
    error: str | None = None


class RembgRequest(BaseModel):
    url: str | None = Field(default=None, max_length=2000)
    image: str | None = Field(default=None, max_length=12_000_000)

    @model_validator(mode="after")
    def require_source(self):
        if not (self.url or self.image):
            raise ValueError("url or image is required")
        return self


class RembgResponse(BaseModel):
    url: str
