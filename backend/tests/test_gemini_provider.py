"""Native HTTP adapter contract via MockTransport; no network/quota consumption."""

import asyncio
import time

import httpx
import pytest
from pydantic import SecretStr

from app.core.config import get_settings
from app.core.errors import AppError
from app.services.answering import request_payload
from app.services.gemini import BASE_URL, MODEL, GeminiProvider


def settings():
    return get_settings().model_copy(
        update={
            "llm_api_key": SecretStr("test-only-key"),
            "llm_base_url": BASE_URL,
            "llm_model": MODEL,
            "llm_free_tier_confirmed": True,
            "llm_quota_confirmed": True,
        }
    )


@pytest.mark.parametrize(
    "change",
    [
        {"llm_api_key": None},
        {"llm_base_url": "https://untrusted.invalid"},
        {"llm_model": "other"},
        {"llm_free_tier_confirmed": False},
        {"llm_quota_confirmed": False},
    ],
)
def test_preflight_refuses_unconfirmed_or_unpinned_endpoint(change):
    with pytest.raises(AppError) as exc:
        GeminiProvider(settings().model_copy(update=change))
    assert exc.value.code == "model_unavailable"


@pytest.mark.parametrize(
    "status,code",
    [
        (429, "model_unavailable"),
        (503, "model_unavailable"),
        (401, "model_unavailable"),
        (302, "model_unavailable"),
    ],
)
def test_no_http_retry_redirect_or_fallback(monkeypatch, status, code):
    calls = []
    real = httpx.AsyncClient

    def handle(request):
        calls.append(request)
        return httpx.Response(
            status,
            json={"private_error": "must-not-leak"},
            headers={"Location": "https://untrusted.invalid"},
        )

    monkeypatch.setattr(
        "app.services.gemini.httpx.AsyncClient",
        lambda **kwargs: real(transport=httpx.MockTransport(handle), **kwargs),
    )
    with pytest.raises(AppError) as exc:
        GeminiProvider(settings()).generate({}, time.monotonic() + 2)
    assert exc.value.code == code and len(calls) == 1
    assert "must-not-leak" not in str(exc.value)
    assert calls[0].headers["x-goog-api-key"] == "test-only-key"


def test_actual_count_payload_and_safe_usage_thought_filter(monkeypatch):
    calls = []
    real = httpx.AsyncClient

    def handle(request):
        import json

        calls.append(json.loads(request.content))
        if str(request.url).endswith(":countTokens"):
            return httpx.Response(200, json={"totalTokens": 123})
        return httpx.Response(
            200,
            json={
                "modelVersion": MODEL,
                "usageMetadata": {
                    "promptTokenCount": 123,
                    "thoughtsTokenCount": 10,
                    "secret": "private",
                },
                "candidates": [
                    {
                        "finishReason": "STOP",
                        "content": {
                            "parts": [{"thought": True, "text": "private-thought"}, {"text": "{}"}]
                        },
                    }
                ],
            },
        )

    monkeypatch.setattr(
        "app.services.gemini.httpx.AsyncClient",
        lambda **kwargs: real(transport=httpx.MockTransport(handle), **kwargs),
    )
    provider = GeminiProvider(settings())
    payload = request_payload("q", [], settings(), True)
    assert provider.count_tokens(payload, time.monotonic() + 2) == 123
    assert calls[0]["generateContentRequest"]["systemInstruction"] == payload["systemInstruction"]
    result = provider.generate(payload, time.monotonic() + 2)
    assert result["text"] == "{}" and "private" not in str(result)
    assert result["usage"]["thoughtsTokenCount"] == 10


def test_hard_timeout_includes_slow_response(monkeypatch):
    real = httpx.AsyncClient

    async def handle(request):
        await asyncio.sleep(1)
        return httpx.Response(200, json={})

    monkeypatch.setattr(
        "app.services.gemini.httpx.AsyncClient",
        lambda **kwargs: real(transport=httpx.MockTransport(handle), **kwargs),
    )
    started = time.monotonic()
    with pytest.raises(AppError) as exc:
        GeminiProvider(settings()).generate({}, started + 0.03)
    assert exc.value.code == "model_timeout" and time.monotonic() - started < 0.5


@pytest.mark.parametrize("value", [True, -1, "12", None])
def test_invalid_count_is_technical(monkeypatch, value):
    monkeypatch.setattr(GeminiProvider, "_post", lambda *args: {"totalTokens": value})
    with pytest.raises(AppError) as exc:
        GeminiProvider(settings()).count_tokens({}, time.monotonic() + 1)
    assert exc.value.code == "invalid_model_output"
