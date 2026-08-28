import base64
import io
import os
from urllib.parse import quote
from urllib.request import Request, urlopen

from log import log

POLLINATIONS = "https://image.pollinations.ai/prompt"
DEFAULT_HF_MODEL = "black-forest-labs/FLUX.1-schnell"


def _env(name: str) -> str:
    return (os.getenv(name) or "").strip().strip('"')


def hf_token() -> str:
    return _env("HF_TOKEN")


def hf_model() -> str:
    return _env("HF_IMAGE_MODEL") or DEFAULT_HF_MODEL


def pollinations_enabled() -> bool:
    return (_env("POLLINATIONS_ENABLED") or "true").lower() in {
        "1",
        "true",
        "yes",
    }


def _pil_to_data_url(image) -> str:
    buf = io.BytesIO()
    image.convert("RGB").save(buf, format="JPEG", quality=85)
    encoded = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def generate_hf(prompt: str) -> str:
    token = hf_token()
    if not token:
        raise RuntimeError("HF_TOKEN missing")
    from huggingface_hub import InferenceClient

    model = hf_model()
    client = InferenceClient(api_key=token)
    image = client.text_to_image(
        prompt,
        model=model,
        width=512,
        height=512,
        num_inference_steps=4,
    )
    url = _pil_to_data_url(image)
    log("hf_ok", model=model, prompt=prompt[:80])
    return url


def generate_pollinations(prompt: str) -> str:
    if not pollinations_enabled():
        raise RuntimeError("POLLINATIONS_ENABLED is false")
    url = (
        f"{POLLINATIONS}/{quote(prompt)}"
        "?width=825&height=465&nologo=true&model=flux"
    )
    request = Request(url, headers={"User-Agent": "canva-ai-service"})
    with urlopen(request, timeout=90) as response:
        if response.status >= 400:
            raise RuntimeError(f"Pollinations HTTP {response.status}")
        final_url = response.geturl() or url
    log("pollinations_ok", prompt=prompt[:80])
    return final_url


def generate_image(prompt: str) -> dict:
    if hf_token():
        try:
            return {"url": generate_hf(prompt), "provider": "hf"}
        except Exception as e:
            log("hf_failed", error=str(e)[:200])
    return {
        "url": generate_pollinations(prompt),
        "provider": "pollinations",
    }
