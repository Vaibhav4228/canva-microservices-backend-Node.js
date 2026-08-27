from datetime import datetime, timezone
from pathlib import Path

INGEST_DIR = Path(__file__).resolve().parent / "data" / "ingest"


def safe_stem(source: str) -> str:
    stem = Path(source).stem or "manual"
    cleaned = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in stem).strip("-")
    return (cleaned[:80] or "manual")


def save_ingest_file(text: str, source: str) -> Path:
    INGEST_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    path = INGEST_DIR / f"{stamp}-{safe_stem(source)}.md"
    path.write_text(text, encoding="utf-8")
    return path
