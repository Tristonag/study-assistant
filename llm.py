"""Everything that talks to the Gemini API lives here, so the rest of the code stays simple.

ask() sends a prompt (plus optional images) and gives back the reply and what it cost.
"""
import base64
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai

import config

load_dotenv()   # copies the lines in your .env file into environment variables

_client = None


def client():
    """Create the API client once and reuse it."""
    global _client
    if _client is None:
        if not os.getenv("GEMINI_API_KEY"):
            raise SystemExit("No GEMINI_API_KEY found. Copy .env.example to .env and paste your key after the =")
        _client = genai.Client()   # reads GEMINI_API_KEY by itself
    return _client


def cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    """What this call would cost on the paid tier, in US dollars."""
    price = config.PRICES.get(model)
    if not price:
        return 0.0
    return (input_tokens * price["input"] + output_tokens * price["output"]) / 1_000_000


def _image_part(image) -> dict:
    """An image for the API: a path to a .png/.jpg file, or raw PNG bytes."""
    if isinstance(image, bytes):
        data, mime = image, "image/png"
    else:
        path = Path(image)
        data = path.read_bytes()
        mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    return {"type": "image", "data": base64.b64encode(data).decode("ascii"), "mime_type": mime}


def ask(prompt: str, *, model: str = config.ANSWER_MODEL, images=(), system: str | None = None,
        max_output_tokens: int = 800, json_output: bool = False) -> tuple[str, dict]:
    """Send a prompt (and optional images). Returns (reply_text, usage)."""
    request = {
        "model": model,
        "input": [{"type": "text", "text": prompt}] + [_image_part(img) for img in images],
        "generation_config": {"max_output_tokens": max_output_tokens},
        "store": False,   # don't keep a copy on Google's side
    }
    if system:
        request["system_instruction"] = system
    if json_output:
        request["response_mime_type"] = "application/json"
    if config.THINKING_LEVEL:
        request["generation_config"]["thinking_level"] = config.THINKING_LEVEL

    for attempt in range(5):
        try:
            reply = client().interactions.create(**request)
            break
        except Exception as error:
            code = getattr(error, "status_code", None)
            if code in (429, 500, 503) and attempt < 4:
                wait = 20 * (attempt + 1)
                print(f"  (API said {code}: busy or rate limit. Waiting {wait}s, then trying again)")
                time.sleep(wait)
                continue
            if code == 429:
                raise SystemExit("Still rate-limited. On the free tier that usually means today's limit is used up. "
                                 "It resets at midnight US Pacific time (2 or 3 pm in Bangkok).") from error
            raise

    usage = reply.usage
    input_tokens = usage.total_input_tokens or 0
    # "Thinking" tokens are billed like output, so count them in (safe side).
    output_tokens = (usage.total_output_tokens or 0) + (usage.total_thought_tokens or 0)
    return (reply.output_text or "").strip(), {
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": round(cost_usd(model, input_tokens, output_tokens), 6),
    }
