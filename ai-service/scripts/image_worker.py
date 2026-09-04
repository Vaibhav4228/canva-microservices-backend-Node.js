import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from kafka import KafkaConsumer

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from inline_tasks import process_image_job  # noqa: E402
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
    log("image_worker_got", jobId=job_id, prompt=(prompt or "")[:80])
    process_image_job(job_id, prompt)
    consumer.commit()
