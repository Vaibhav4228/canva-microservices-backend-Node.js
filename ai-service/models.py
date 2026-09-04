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


class TemplateObject(BaseModel):
    type: str = Field(default="textbox", max_length=40)
    text: str | None = Field(default=None, max_length=500)
    left: float = 40
    top: float = 80
    width: float | None = None
    height: float | None = None
    fill: str = Field(default="#111111", max_length=40)
    fontSize: int = Field(default=32, ge=8, le=200)
    fontFamily: str = Field(default="Arial", max_length=80)
    fontWeight: str = Field(default="normal", max_length=40)


class TemplateLayout(BaseModel):
    title: str = Field(max_length=200)
    subtitle: str = Field(default="", max_length=300)
    background: str = Field(default="#ffffff", max_length=40)
    width: int = Field(default=825, ge=200, le=2000)
    height: int = Field(default=465, ge=200, le=2000)
    objects: list[TemplateObject] = Field(default_factory=list)


class TemplateFromPromptRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=500)


class TemplateFromPromptResponse(BaseModel):
    layout: TemplateLayout
    notesUsed: int = 0
