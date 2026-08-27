from pathlib import Path
import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

from models import (
    IngestRequest,
    IngestResponse,
    PingRequest,
    PingResponse,
    RagQueryRequest,
    RagQueryResponse,
    VectorInfoResponse,
)
from ingest import save_ingest_file
from kafka_events import emit_rag_ingest
from rag_graph import rag_query
from vector_store import info as vector_info

load_dotenv(Path(__file__).resolve().parent / ".env")

PORT = int(os.getenv("PORT", "5004"))
SERVICE = "ai-service"

app = FastAPI(title="Canva AI service")


@app.get("/health")
def health():
    return {
        "ok": True,
        "service": SERVICE,
        "port": PORT,
    }


@app.get("/vector/info", response_model=VectorInfoResponse)
def get_vector_info():
    try:
        return VectorInfoResponse(**vector_info())
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e)) from e


@app.post("/ping", response_model=PingResponse)
def ping(body: PingRequest):
    return PingResponse(ok=True, echo=body.message, service=SERVICE)


@app.post("/rag/query", response_model=RagQueryResponse)
def query_rag(body: RagQueryRequest):
    try:
        return RagQueryResponse(**rag_query(body.query, body.k))
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e)) from e


@app.post("/ingest", response_model=IngestResponse)
def ingest(body: IngestRequest):
    path = save_ingest_file(body.text, body.source)
    queued = emit_rag_ingest(
        {
            "path": str(path),
            "source": body.source,
            "bytes": path.stat().st_size,
        }
    )
    return IngestResponse(
        ok=True,
        source=body.source,
        path=str(path),
        bytes=path.stat().st_size,
        queued=queued,
    )
