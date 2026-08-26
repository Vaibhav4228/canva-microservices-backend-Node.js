from pathlib import Path
import os

from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv(Path(__file__).resolve().parent / ".env")

PORT = int(os.getenv("PORT", "5004"))
SERVICE = "ai-service"

app = FastAPI(title="Canva AI service")


@app.get("/health")
def health():
    return {
        "ok": True,
        "service": SERVICE,
        "port": PORT,
    }
