import json
import os
from pathlib import Path

from dotenv import load_dotenv
from kafka import KafkaConsumer

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

TOPIC = "rag.ingest"
brokers = (os.getenv("KAFKA_BROKERS") or "localhost:9092").split(",")

consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=brokers,
    auto_offset_reset="latest",
    group_id="ai-rag-logger",
    value_deserializer=lambda value: json.loads(value.decode("utf-8")),
)

print(json.dumps({"service": "rag-logger", "msg": "listening", "topic": TOPIC, "brokers": brokers}), flush=True)

for message in consumer:
    print(
        json.dumps(
            {
                "service": "rag-logger",
                "msg": "event",
                "key": message.key.decode("utf-8") if message.key else None,
                "value": message.value,
            }
        ),
        flush=True,
    )
