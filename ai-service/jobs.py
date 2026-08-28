import json
import os
from uuid import uuid4

from upstash_redis import Redis

from log import log

JOB_TTL_SEC = 3600
_redis = None


def _env(name: str) -> str:
    return (os.getenv(name) or "").strip().strip('"')


def get_redis() -> Redis:
    global _redis
    if _redis is None:
        url = _env("UPSTASH_REDIS_REST_URL")
        token = _env("UPSTASH_REDIS_REST_TOKEN")
        if not url or not token:
            raise RuntimeError("UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN are required")
        _redis = Redis(url=url, token=token)
    return _redis


def _key(job_id: str) -> str:
    return f"ai:job:{job_id}"


def create_job(prompt: str) -> dict:
    job_id = str(uuid4())
    payload = {
        "jobId": job_id,
        "prompt": prompt,
        "status": "pending",
        "url": None,
        "provider": None,
        "error": None,
    }
    get_redis().set(_key(job_id), json.dumps(payload), ex=JOB_TTL_SEC)
    log("job_created", jobId=job_id)
    return payload


def get_job(job_id: str) -> dict | None:
    raw = get_redis().get(_key(job_id))
    if raw is None:
        return None
    if isinstance(raw, dict):
        return raw
    return json.loads(raw)


def update_job(job_id: str, **fields) -> dict | None:
    job = get_job(job_id)
    if not job:
        return None
    job.update(fields)
    get_redis().set(_key(job_id), json.dumps(job), ex=JOB_TTL_SEC)
    log("job_updated", jobId=job_id, status=job.get("status"))
    return job
