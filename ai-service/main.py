from collections import defaultdict
from pathlib import Path
import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

from log import log

from models import (
    GenerateRequest,
    GenerateResponse,
    IngestRequest,
    IngestResponse,
    JobStatusResponse,
    PingRequest,
    PingResponse,
    RagQueryRequest,
    RagQueryResponse,
    RembgRequest,
    RembgResponse,
    TemplateFromPromptRequest,
    TemplateFromPromptResponse,
    VectorInfoResponse,
)
from ingest import save_ingest_file
from jobs import create_job, get_job
from kafka_events import emit_ai_job, emit_rag_ingest
from vector_store import info as vector_info

load_dotenv(Path(__file__).resolve().parent / ".env")

PORT = int(os.getenv("PORT", "5004"))
SERVICE = "ai-service"

app = FastAPI(title="Canva AI service")  # :5004
_job_polls = defaultdict(int)


class _QuietJobPolls(logging.Filter):
    def filter(self, record):
        try:
            return "/jobs/" not in record.getMessage()
        except Exception:
            return True


logging.getLogger("uvicorn.access").addFilter(_QuietJobPolls())


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
    from rag_graph import rag_query

    try:
        return RagQueryResponse(**rag_query(body.query, body.k))
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e)) from e


@app.post("/generate", response_model=GenerateResponse)
def generate(body: GenerateRequest):
    try:
        job = create_job(body.prompt)
        queued = emit_ai_job({"jobId": job["jobId"], "prompt": body.prompt})
        log(
            "generate_accepted",
            jobId=job["jobId"],
            queued=queued,
            promptLen=len(body.prompt),
        )
        if queued:
            log(
                "generate_waiting_worker",
                jobId=job["jobId"],
                hint="npm run dev:image-worker",
            )
        else:
            log(
                "generate_not_queued",
                jobId=job["jobId"],
                hint="Redpanda/Kafka down? npm run kafka:up",
            )
        return GenerateResponse(jobId=job["jobId"], status=job["status"], queued=queued)
    except Exception as e:
        log("generate_failed", error=str(e))
        raise HTTPException(status_code=503, detail=str(e)) from e


@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
def job_status(job_id: str):
    try:
        job = get_job(job_id)
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    _job_polls[job_id] += 1
    polls = _job_polls[job_id]
    status = job["status"]
    if polls == 1 or polls % 15 == 0 or status != "pending":
        extra = {}
        if status == "pending":
            extra["hint"] = "still pending — start npm run dev:image-worker"
        log("job_poll", jobId=job_id, status=status, polls=polls, **extra)
    return JobStatusResponse(
        jobId=job["jobId"],
        status=status,
        url=job.get("url"),
        provider=job.get("provider"),
        error=job.get("error"),
    )


@app.post("/templates/from-prompt", response_model=TemplateFromPromptResponse)
def templates_from_prompt(body: TemplateFromPromptRequest):
    from template_layout import template_from_prompt

    try:
        result = template_from_prompt(body.prompt)
        return TemplateFromPromptResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e)) from e


@app.post("/edit/rembg", response_model=RembgResponse)
def edit_rembg(body: RembgRequest):
    from rembg_edit import remove_background

    try:
        return RembgResponse(url=remove_background(url=body.url, image=body.image))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
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
