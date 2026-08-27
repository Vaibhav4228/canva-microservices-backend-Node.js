import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from kafka import KafkaConsumer

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from log import log  # noqa: E402
from rag_index import index_file  # noqa: E402

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
    try:
        result = index_file(path, source)
        consumer.commit()
        log("rag_worker_ok", **result)
    except (FileNotFoundError, ValueError, TypeError) as e:
        log("rag_worker_skip", path=path, source=source, error=str(e))
        consumer.commit()
    except Exception as e:
        log("rag_worker_failed", path=path, source=source, error=str(e))
