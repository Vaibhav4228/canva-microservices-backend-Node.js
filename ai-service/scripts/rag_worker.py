import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from kafka import KafkaConsumer

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from inline_tasks import process_rag_ingest  # noqa: E402
from log import log  # noqa: E402

TOPIC = "rag.ingest"
brokers = (os.getenv("KAFKA_BROKERS") or "localhost:9092").split(",")

consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=brokers,
    auto_offset_reset="earliest",
    group_id="ai-rag-worker",
    value_deserializer=lambda value: json.loads(value.decode("utf-8")),
    enable_auto_commit=False,
)

log("rag_worker_listening", topic=TOPIC, brokers=brokers)

for message in consumer:
    payload = message.value or {}
    path = payload.get("path")
    source = payload.get("source") or "manual"
    process_rag_ingest(path, source)
    consumer.commit()
