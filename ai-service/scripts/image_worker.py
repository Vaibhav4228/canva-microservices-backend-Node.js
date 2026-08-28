import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from kafka import KafkaConsumer

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from image_gen import generate_image  # noqa: E402
from jobs import update_job  # noqa: E402
from log import log  # noqa: E402

TOPIC = "ai.jobs"
brokers = (os.getenv("KAFKA_BROKERS") or "localhost:9092").split(",")

consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=brokers,
    auto_offset_reset="earliest",
    group_id="ai-image-worker",
    value_deserializer=lambda value: json.loads(value.decode("utf-8")),
    enable_auto_commit=False,
)

log("image_worker_listening", topic=TOPIC, brokers=brokers)

for message in consumer:
    payload = message.value or {}
    job_id = payload.get("jobId")
    prompt = payload.get("prompt") or ""
    try:
        if not job_id or not prompt:
            raise ValueError("jobId and prompt are required")
        update_job(job_id, status="running")
        result = generate_image(prompt)
        update_job(
            job_id,
            status="done",
            url=result["url"],
            provider=result["provider"],
            error=None,
        )
        consumer.commit()
        log("image_worker_ok", jobId=job_id, provider=result["provider"])
    except (ValueError, TypeError) as e:
        log("image_worker_skip", jobId=job_id, error=str(e))
        if job_id:
            update_job(job_id, status="error", error=str(e))
        consumer.commit()
    except Exception as e:
        log("image_worker_failed", jobId=job_id, error=str(e))
        if job_id:
            update_job(job_id, status="error", error=str(e))
        consumer.commit()
