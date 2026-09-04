"""Run AI jobs in-process when Kafka is unavailable (Render / no Redpanda).

When KAFKA_BROKERS is reachable, workers consume topics as usual.
"""

import threading

from image_gen import generate_image
from jobs import update_job
from log import log
from rag_index import index_file


def process_image_job(job_id: str, prompt: str) -> None:
    try:
        if not job_id or not prompt:
            raise ValueError("jobId and prompt are required")
        log("inline_image_start", jobId=job_id, prompt=prompt[:80])
        update_job(job_id, status="running")
        result = generate_image(prompt)
        update_job(
            job_id,
            status="done",
            url=result["url"],
            provider=result["provider"],
            error=None,
        )
        log("inline_image_ok", jobId=job_id, provider=result["provider"])
    except (ValueError, TypeError) as e:
        log("inline_image_skip", jobId=job_id, error=str(e))
        if job_id:
            update_job(job_id, status="error", error=str(e))
    except Exception as e:
        log("inline_image_failed", jobId=job_id, error=str(e))
        if job_id:
            update_job(job_id, status="error", error=str(e))


def schedule_image_job(job_id: str, prompt: str) -> None:
    thread = threading.Thread(
        target=process_image_job,
        args=(job_id, prompt),
        daemon=True,
        name=f"inline-image-{job_id[:8]}",
    )
    thread.start()
    log("inline_image_scheduled", jobId=job_id)


def process_rag_ingest(path: str, source: str) -> None:
    try:
        result = index_file(path, source)
        log("inline_rag_ok", **result)
    except (FileNotFoundError, ValueError, TypeError) as e:
        log("inline_rag_skip", path=path, source=source, error=str(e))
    except Exception as e:
        log("inline_rag_failed", path=path, source=source, error=str(e))


def schedule_rag_ingest(path: str, source: str) -> None:
    thread = threading.Thread(
        target=process_rag_ingest,
        args=(path, source),
        daemon=True,
        name=f"inline-rag-{source[:12]}",
    )
    thread.start()
    log("inline_rag_scheduled", path=path, source=source)
