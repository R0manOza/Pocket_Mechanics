"""
LLM Service — Google Gemini (AI Studio) direct and/or OpenRouter.
Picks a route from env; logs every call (tokens, latency, estimated USD).
"""

import csv
import os
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Lazy OpenRouter client (only created when needed)
_openai_client: OpenAI | None = None
_genai_configured = False

LOG_FILE = os.environ.get("COST_LOG_PATH", "logs/cost-log.csv")

# OpenRouter model ids (e.g. google/gemini-2.5-flash)
DEFAULT_OPENROUTER_MODEL = os.environ.get("DEFAULT_MODEL", "google/gemini-2.5-flash")
# Google API model names (no "google/" prefix) — see AI Studio
DEFAULT_GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

MODEL_PRICING = {
    "gemini-2.5-flash-lite": {"input": 0.00, "output": 0.00},
    "gemini-2.5-flash": {"input": 0.00, "output": 0.00},
    "gemini-2.5-pro": {"input": 0.00, "output": 0.00},
    "meta-llama/llama-4-maverick:free": {"input": 0.00, "output": 0.00},
    "google/gemma-3-27b-it:free": {"input": 0.00, "output": 0.00},
    "deepseek/deepseek-r1:free": {"input": 0.00, "output": 0.00},
    "openrouter/free": {"input": 0.00, "output": 0.00},
    "google/gemini-2.5-flash": {"input": 0.15, "output": 0.60},
    "google/gemini-2.5-pro": {"input": 1.25, "output": 10.00},
    "anthropic/claude-haiku-4-5-20251001": {"input": 1.00, "output": 5.00},
    "anthropic/claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "openai/gpt-4o": {"input": 2.50, "output": 10.00},
}


def get_routing() -> str:
    """Public: which backend is active (`gemini` or `openrouter`)."""
    return _routing()


def _routing() -> str:
    """
    Return 'gemini' or 'openrouter'.

    Priority:
    - USE_DIRECT_GEMINI=true  -> Gemini (requires GEMINI_API_KEY)
    - Only GEMINI_API_KEY set -> Gemini (typical for your setup)
    - Only OPENROUTER_KEY set -> OpenRouter
    - Both set -> OpenRouter unless USE_DIRECT_GEMINI=true
    """
    force_gemini = os.environ.get("USE_DIRECT_GEMINI", "").lower() == "true"
    or_key = os.environ.get("OPENROUTER_KEY", "").strip()
    g_key = os.environ.get("GEMINI_API_KEY", "").strip()

    if force_gemini:
        if not g_key:
            raise RuntimeError("USE_DIRECT_GEMINI=true requires GEMINI_API_KEY in Backend/.env")
        return "gemini"
    if or_key and g_key:
        return "openrouter"
    if g_key and not or_key:
        return "gemini"
    if or_key:
        return "openrouter"
    raise RuntimeError(
        "No AI key found. Set GEMINI_API_KEY (Google AI Studio) and/or OPENROUTER_KEY in Backend/.env"
    )


def _ensure_genai():
    global _genai_configured
    if _genai_configured:
        return
    import google.generativeai as genai

    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    _genai_configured = True


def get_openrouter_client() -> OpenAI:
    """Public accessor for streaming (OpenRouter path)."""
    return _get_openrouter_client()


def ensure_gemini() -> None:
    """Configure Google Generative AI (Gemini direct path)."""
    _ensure_genai()


def normalize_gemini_model(model: str | None) -> str:
    return _normalize_gemini_model(model)


def normalize_openrouter_model(model: str | None) -> str:
    return _normalize_openrouter_model(model)


def _get_openrouter_client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        key = os.environ.get("OPENROUTER_KEY", "").strip()
        if not key:
            raise RuntimeError("OPENROUTER_KEY missing in Backend/.env")
        _openai_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=key,
        )
    return _openai_client


def _normalize_gemini_model(model: str | None) -> str:
    """Map request override / env to a Google API model id."""
    if not model or not model.strip():
        return DEFAULT_GEMINI_MODEL
    m = model.strip()
    if "/" in m:
        # e.g. google/gemini-2.5-flash -> gemini-2.5-flash
        m = m.split("/")[-1]
    return m


def _normalize_openrouter_model(model: str | None) -> str:
    if not model or not model.strip():
        return DEFAULT_OPENROUTER_MODEL
    return model.strip()


def _pricing_key_for_cost(routing: str, model: str) -> str:
    if routing == "openrouter":
        return model
    # Gemini direct: cost table uses short names
    return model


@dataclass
class CallRecord:
    timestamp: str
    model: str
    purpose: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    latency_ms: int
    cost_usd: float


def _log(record: CallRecord) -> None:
    log_dir = os.path.dirname(LOG_FILE)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(record).keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(asdict(record))
    print(
        f"[COST] {record.timestamp} | {record.model} | {record.purpose} | "
        f"in={record.input_tokens} out={record.output_tokens} | "
        f"{record.latency_ms}ms | ${record.cost_usd:.6f}"
    )


def _calculate_cost(pricing_key: str, in_tok: int, out_tok: int) -> float:
    p = MODEL_PRICING.get(pricing_key, {"input": 0.0, "output": 0.0})
    return (in_tok / 1_000_000) * p["input"] + (out_tok / 1_000_000) * p["output"]


def generate(
    prompt: str,
    system: str = "You are a helpful assistant.",
    model: str | None = None,
    purpose: str = "generate",
) -> dict:
    routing = _routing()
    start = time.time()

    if routing == "gemini":
        _ensure_genai()
        import google.generativeai as genai

        model_name = _normalize_gemini_model(model)
        m = genai.GenerativeModel(model_name, system_instruction=system)
        response = m.generate_content(prompt)
        latency = int((time.time() - start) * 1000)
        meta = response.usage_metadata
        in_tok = meta.prompt_token_count if meta else 0
        out_tok = meta.candidates_token_count if meta else 0
        content = response.text or ""
        stored_model = model_name
        pricing_key = _pricing_key_for_cost(routing, model_name)
    else:
        client = _get_openrouter_client()
        model_name = _normalize_openrouter_model(model)
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )
        latency = int((time.time() - start) * 1000)
        usage = response.usage
        in_tok = usage.prompt_tokens if usage else 0
        out_tok = usage.completion_tokens if usage else 0
        msg = response.choices[0].message
        content = (msg.content or "") if msg else ""
        stored_model = model_name
        pricing_key = _pricing_key_for_cost(routing, model_name)

    record = CallRecord(
        timestamp=datetime.now(timezone.utc).isoformat(),
        model=stored_model,
        purpose=purpose,
        input_tokens=in_tok,
        output_tokens=out_tok,
        total_tokens=in_tok + out_tok,
        latency_ms=latency,
        cost_usd=_calculate_cost(pricing_key, in_tok, out_tok),
    )
    _log(record)

    return {
        "content": content,
        "model": stored_model,
        "input_tokens": in_tok,
        "output_tokens": out_tok,
        "latency_ms": latency,
        "cost_usd": record.cost_usd,
    }
