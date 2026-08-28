import json
import os
from datetime import datetime, timezone

from kafka import KafkaProducer

from log import log

TOPIC_RAG = "rag.ingest"
TOPIC_JOBS = "ai.jobs"
_client = None


def _get_producer():
    global _client
    if _client is None:
        brokers = (os.getenv("KAFKA_BROKERS") or "localhost:9092").split(",")
        _client = KafkaProducer(
            bootstrap_servers=brokers,
            value_serializer=lambda value: json.dumps(value).encode("utf-8"),
            key_serializer=lambda key: key.encode("utf-8") if key else None,
            request_timeout_ms=3000,
        )
        log("kafka_connected", brokers=brokers)
    return _client


def emit_rag_ingest(payload: dict) -> bool:
    try:
        producer = _get_producer()
        producer.send(
            TOPIC_RAG,
            key=payload.get("path"),
            value={
                "event": "rag.ingest",
                **payload,
                "ts": datetime.now(timezone.utc).isoformat(),
            },
        )
        producer.flush(timeout=2)
        return True
    except Exception as e:
        log("kafka_produce_failed", event="rag.ingest", error=str(e))
        return False


def emit_ai_job(payload: dict) -> bool:
    try:
        producer = _get_producer()
        producer.send(
            TOPIC_JOBS,
            key=payload.get("jobId"),
            value={
                "event": "ai.jobs",
                **payload,
                "ts": datetime.now(timezone.utc).isoformat(),
            },
        )
        producer.flush(timeout=2)
        return True
    except Exception as e:
        log("kafka_produce_failed", event="ai.jobs", error=str(e))
        return False
