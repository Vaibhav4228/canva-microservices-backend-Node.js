import base64
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from log import log

MAX_BYTES = 8 * 1024 * 1024


def _decode_image_field(image: str) -> bytes:
    raw = image.strip()
    if raw.startswith("data:") and "," in raw:
        raw = raw.split(",", 1)[1]
    return base64.b64decode(raw)


def _fetch_url(url: str) -> bytes:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("url must be http or https")
    request = Request(url, headers={"User-Agent": "canva-ai-service"})
    with urlopen(request, timeout=30) as response:
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("image too large")
    return data


def remove_background(*, url: str | None = None, image: str | None = None) -> str:
    if image:
        src = _decode_image_field(image)
    elif url:
        src = _fetch_url(url)
    else:
        raise ValueError("url or image is required")
    if len(src) > MAX_BYTES:
        raise ValueError("image too large")

    from rembg import remove

    out = remove(src)
    encoded = base64.b64encode(out).decode("ascii")
    log("rembg_ok", inBytes=len(src), outBytes=len(out))
    return f"data:image/png;base64,{encoded}"
