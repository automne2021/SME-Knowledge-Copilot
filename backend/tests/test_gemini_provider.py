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
    "status,code,reason",
    [
        (429, "model_unavailable", "quota"),
        (503, "model_unavailable", "overloaded"),
        (500, "model_unavailable", "overloaded"),
        (401, "model_unavailable", "rejected"),
        (302, "model_unavailable", "rejected"),
    ],
)
def test_no_http_retry_redirect_or_fallback(monkeypatch, caplog, status, code, reason):
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
    assert exc.value.status_code == 503 and exc.value.details == {"reason": reason}
    assert "must-not-leak" not in str(exc.value)
    assert calls[0].headers["x-goog-api-key"] == "test-only-key"
    # The provider status is logged for diagnosis; bodies and the key never are.
    assert f"HTTP {status} ({reason})" in caplog.text
    assert "must-not-leak" not in caplog.text and "test-only-key" not in caplog.text


def test_hung_provider_call_times_out_at_the_call_bound(monkeypatch, caplog):
    real = httpx.AsyncClient

    async def hang(request):
        await asyncio.sleep(5)
        return httpx.Response(200, json={})

    monkeypatch.setattr(
        "app.services.gemini.httpx.AsyncClient",
        lambda **kwargs: real(transport=httpx.MockTransport(hang), **kwargs),
    )
    provider = GeminiProvider(settings().model_copy(update={"llm_call_timeout_seconds": 0.2}))
    started = time.monotonic()
    with pytest.raises(AppError) as exc:
        provider.generate({}, time.monotonic() + 10)
    assert exc.value.code == "model_timeout" and exc.value.status_code == 504
    assert time.monotonic() - started < 2
    assert "timed out" in caplog.text and "test-only-key" not in caplog.text


def test_network_error_is_classified_without_retry(monkeypatch):
    calls = []
    real = httpx.AsyncClient

    def fail(request):
        calls.append(request)
        raise httpx.ConnectError("offline", request=request)

    monkeypatch.setattr(
        "app.services.gemini.httpx.AsyncClient",
        lambda **kwargs: real(transport=httpx.MockTransport(fail), **kwargs),
    )
    with pytest.raises(AppError) as exc:
        GeminiProvider(settings()).generate({}, time.monotonic() + 2)
    assert exc.value.code == "model_unavailable" and exc.value.details == {"reason": "network"}
    assert len(calls) == 1


def test_default_call_timeout_fails_a_hung_call_well_before_the_query_deadline():
    defaults = type(get_settings()).model_fields
    assert defaults["llm_call_timeout_seconds"].default == 60
    assert defaults["query_timeout_seconds"].default == 150


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
