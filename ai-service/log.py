import json
from datetime import datetime, timezone


def log(msg, **extra):
    print(
        json.dumps(
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "service": "ai-service",
                "msg": msg,
                **extra,
            }
        ),
        flush=True,
    )
