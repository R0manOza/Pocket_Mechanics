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

from services import episode_logger
from services import resilience
from services import system_prompts
from services import vision_utils

if not os.environ.get("POCKET_MECHANICS_UNDER_TEST"):
    load_dotenv()

# Lazy OpenRouter client (only created when needed)
_openai_client: OpenAI | None = None
_genai_configured = False


def _default_log_path(filename: str) -> str:
    """
    Vercel serverless has a read-only filesystem except for /tmp.
    Prefer /tmp when available; otherwise fall back to repo-relative logs/.
    """
    tmp = os.environ.get("TMPDIR") or os.environ.get("TEMP") or ""

    if os.path.isdir("/tmp"):
        return os.path.join("/tmp", filename)
    if tmp and os.path.isdir(tmp):
        return os.path.join(tmp, filename)

    return os.path.join("logs", filename)


def _log_file() -> str:
    return os.environ.get("COST_LOG_PATH", _default_log_path("cost-log.csv"))


# OpenRouter model ids (e.g. google/gemini-2.5-flash)
DEFAULT_OPENROUTER_MODEL = os.environ.get("DEFAULT_MODEL", "google/gemini-2.5-flash")

# Google API model names (no "google/" prefix) — see AI Studio
DEFAULT_GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
ENABLE_PROMPT_CACHE = os.environ.get("ENABLE_PROMPT_CACHE", "true").lower() == "true"
USE_EXTENDED_SYSTEM = os.environ.get("EXTENDED_SYSTEM_PROMPT", "true").lower() == "true"


def build_system_prompt(override: str | None = None) -> str:
    """Lab 8 cache target: default assistant + stable safety policy block."""
    base = override or system_prompts.DEFAULT_SYSTEM
    if not USE_EXTENDED_SYSTEM:
        return base
    if override:
        return base
    return f"{base}\n\n{system_prompts.SAFETY_POLICY_BLOCK}"
DEFAULT_OPENROUTER_FALLBACK_MODELS = [
    "openai/gpt-5.5",
    "deepseek/deepseek-v4-flash",
]


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
    "openai/gpt-5-nano": {"input": 0.05, "output": 0.40},
    "openai/gpt-5.5": {"input": 5.00, "output": 30.00},
    "deepseek/deepseek-v4-flash": {"input": 0.098, "output": 0.196},
    "qwen/qwen3.5-flash-02-23": {"input": 0.325, "output": 1.95},

}


def get_routing() -> str:
    """Public: which backend is active (`gemini` or `openrouter`)."""
    return _routing()


def _routing() -> str:
    """
    Return 'gemini' or 'openrouter'.

    Priority:
    - USE_DIRECT_GEMINI=true  -> Gemini (requires GEMINI_API_KEY)
    - Only GEMINI_API_KEY set -> Gemini
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
        "No AI key found. Set GEMINI_API_KEY and/or OPENROUTER_KEY in Backend/.env"
    )


def _ensure_genai() -> None:
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
            timeout=float(os.environ.get("OPENROUTER_TIMEOUT_SECONDS", "30")),
            max_retries=int(os.environ.get("OPENROUTER_MAX_RETRIES", "2")),
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
    cache_read_tokens: int
    cache_write_tokens: int
    latency_ms: int
    fallback_triggered: bool
    cost_usd: float


def _log(record: CallRecord) -> None:
    # Always print a summary line; file logging is best-effort.
    print(
        f"[COST] {record.timestamp} | {record.model} | {record.purpose} | "
        f"in={record.input_tokens} out={record.output_tokens} | "
        f"{record.latency_ms}ms | ${record.cost_usd:.6f}"
    )

    try:
        log_file = _log_file()
        log_dir = os.path.dirname(log_file)

        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        file_exists = os.path.isfile(log_file)

        with open(log_file, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(asdict(record).keys()))
            if not file_exists:
                writer.writeheader()
            writer.writerow(asdict(record))

    except OSError:
        # Read-only filesystem, e.g. Vercel, or other IO failure.
        # Keep stdout logging so the API call still succeeds.
        return


def _calculate_cost(pricing_key: str, in_tok: int, out_tok: int) -> float:
    p = MODEL_PRICING.get(pricing_key, {"input": 0.0, "output": 0.0})
    return (in_tok / 1_000_000) * p["input"] + (out_tok / 1_000_000) * p["output"]


def _int_attr(obj, *names: str) -> int:
    for name in names:
        if obj is None:
            return 0
        if isinstance(obj, dict):
            value = obj.get(name)
            if isinstance(value, int):
                return value
            if isinstance(value, dict):
                for key in names:
                    nested = value.get(key)
                    if isinstance(nested, int):
                        return nested
                return 0
            continue
        value = getattr(obj, name, None)
        if isinstance(value, int):
            return value
        if isinstance(value, dict):
            for key in names:
                nested = value.get(key)
                if isinstance(nested, int):
                    return nested
    return 0


def _openrouter_model_chain(model: str | None) -> list[str]:
    model_name = _normalize_openrouter_model(model)
    if model and not os.environ.get("OPENROUTER_ENABLE_FALLBACK_FOR_MODEL"):
        return [model_name]

    configured = [
        item.strip()
        for item in os.environ.get("OPENROUTER_FALLBACK_MODELS", "").split(",")
        if item.strip()
    ]
    fallbacks = configured or DEFAULT_OPENROUTER_FALLBACK_MODELS
    return [model_name] + [fallback for fallback in fallbacks if fallback != model_name]


def _openrouter_system_content(system: str, model_name: str):
    if ENABLE_PROMPT_CACHE and model_name.startswith("anthropic/"):
        return [
            {
                "type": "text",
                "text": system,
                "cache_control": {"type": "ephemeral"},
            }
        ]
    return system


def _cache_usage_from_openrouter(usage) -> tuple[int, int]:
    details = getattr(usage, "prompt_tokens_details", None)
    cache_read = _int_attr(
        usage,
        "cache_read_input_tokens",
        "cached_tokens",
        "cached_input_tokens",
    ) or _int_attr(details, "cache_read_input_tokens", "cached_tokens", "cached_input_tokens")
    cache_write = _int_attr(
        usage,
        "cache_creation_input_tokens",
        "cache_write_input_tokens",
    ) or _int_attr(details, "cache_creation_input_tokens", "cache_write_input_tokens")
    return cache_read, cache_write


def generate(
    prompt: str,
    system: str = "You are a helpful assistant.",
    model: str | None = None,
    purpose: str = "generate",
    images: list[str] | None = None,
) -> dict:
    routing = _routing()
    start = time.perf_counter()
    image_urls = vision_utils.validate_image_data_urls(images)

    if routing == "gemini":
        _ensure_genai()
        import google.generativeai as genai

        model_name = _normalize_gemini_model(model)
        m = genai.GenerativeModel(model_name, system_instruction=system)
        user_parts = (
            vision_utils.gemini_generate_parts(prompt, image_urls)
            if image_urls
            else prompt
        )
        timeout_s = float(os.environ.get("GEMINI_TIMEOUT_SECONDS", "30"))

        def _gemini_call():
            return m.generate_content(
                user_parts,
                request_options={"timeout": timeout_s},
            )

        response, _retry_count = resilience.call_with_resilience(
            _gemini_call,
            session_id=purpose,
            model=model_name,
            timeout_ms=int(timeout_s * 1000),
        )

        latency = max(1, int((time.perf_counter() - start) * 1000))

        meta = response.usage_metadata
        in_tok = meta.prompt_token_count if meta else 0
        out_tok = meta.candidates_token_count if meta else 0
        cache_read_tokens = _int_attr(meta, "cached_content_token_count")
        cache_write_tokens = 0
        content = response.text or ""
        stored_model = model_name
        pricing_key = _pricing_key_for_cost(routing, model_name)
        fallback_triggered = False

    else:
        client = _get_openrouter_client()
        user_content = vision_utils.openrouter_user_content(prompt, image_urls)
        last_error: Exception | None = None
        response = None
        stored_model = ""
        fallback_triggered = False

        timeout_ms = resilience.timeout_ms_from_env()

        for attempt_index, model_name in enumerate(_openrouter_model_chain(model)):
            try:

                def _openrouter_call(mn: str = model_name):
                    return client.chat.completions.create(
                        model=mn,
                        messages=[
                            {
                                "role": "system",
                                "content": _openrouter_system_content(system, mn),
                            },
                            {"role": "user", "content": user_content},
                        ],
                    )

                response, _retry_count = resilience.call_with_resilience(
                    _openrouter_call,
                    session_id=purpose,
                    model=model_name,
                    timeout_ms=timeout_ms,
                )
                stored_model = model_name
                fallback_triggered = attempt_index > 0
                break
            except Exception as exc:
                last_error = exc

        if response is None:
            raise RuntimeError(
                f"All OpenRouter models failed: {type(last_error).__name__}: {last_error}"
            )

        latency = max(1, int((time.perf_counter() - start) * 1000))

        usage = response.usage
        in_tok = usage.prompt_tokens if usage else 0
        out_tok = usage.completion_tokens if usage else 0
        cache_read_tokens, cache_write_tokens = _cache_usage_from_openrouter(usage)
        msg = response.choices[0].message
        content = (msg.content or "") if msg else ""
        pricing_key = _pricing_key_for_cost(routing, stored_model)

    record = CallRecord(
        timestamp=datetime.now(timezone.utc).isoformat(),
        model=stored_model,
        purpose=purpose,
        input_tokens=in_tok,
        output_tokens=out_tok,
        total_tokens=in_tok + out_tok,
        cache_read_tokens=cache_read_tokens,
        cache_write_tokens=cache_write_tokens,
        latency_ms=latency,
        fallback_triggered=fallback_triggered,
        cost_usd=_calculate_cost(pricing_key, in_tok, out_tok),
    )

    _log(record)
    episode_logger.log_llm_call(
        session_id=purpose,
        model=stored_model,
        input_tokens=in_tok,
        output_tokens=out_tok,
        cache_read_tokens=cache_read_tokens,
        cache_write_tokens=cache_write_tokens,
        latency_ms=latency,
        cost_usd=record.cost_usd,
        provider=episode_logger.extract_provider(stored_model),
        fallback_triggered=fallback_triggered,
        timeout_ms=resilience.timeout_ms_from_env(),
    )

    return {
        "content": content,
        "model": stored_model,
        "input_tokens": in_tok,
        "output_tokens": out_tok,
        "cache_read_tokens": cache_read_tokens,
        "cache_write_tokens": cache_write_tokens,
        "latency_ms": latency,
        "fallback_triggered": fallback_triggered,
        "cost_usd": record.cost_usd,
    }
