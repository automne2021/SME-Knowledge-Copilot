"""Fake-clock pacing and mock HTTP only; never read corpus or use real inference."""

import asyncio
import json
from types import SimpleNamespace

import pytest

from eval import final_pacing as pacing


def test_even_spacing_and_no_reservation_while_waiting():
    clock = SimpleNamespace(now=0)
    p = pacing.RequestPacer(pacing.POLICY, clock=lambda: clock.now)
    assert p.admit("countTokens") == 0
    assert p.admit("countTokens") == 5.1
    assert len(p.events) == 1
    clock.now = 5.1
    assert p.admit("countTokens") == 0


def test_mixed_sequence_obeys_rolling_request_and_token_caps():
    clock = SimpleNamespace(now=0)
    p = pacing.RequestPacer(pacing.POLICY, clock=lambda: clock.now)
    dispatched = []
    for action in ["generateContent"] * 10 + ["countTokens"] * 30:
        for _ in range(10):
            wait = p.admit(action)
            if wait == 0:
                break
            clock.now += wait
        else:
            pytest.fail("Pacer did not make progress")
        dispatched.append((clock.now, 40000 if action == "generateContent" else 0))
        window = [x for x in dispatched if clock.now - x[0] < 61]
        assert len(window) <= 12 and sum(x[1] for x in window) <= 200000
    assert dispatched[5][0] >= 61  # Sixth generation cannot exceed token allowance.


def test_invalid_policy_and_action():
    with pytest.raises(ValueError):
        pacing.RequestPacer({**pacing.POLICY, "max_requests": 100})
    with pytest.raises(ValueError):
        pacing.RequestPacer(pacing.POLICY).admit("other")


def test_float_window_boundary_is_not_admitted_early():
    clock = SimpleNamespace(now=5.1)
    p = pacing.RequestPacer(pacing.POLICY, clock=lambda: clock.now)
    for _ in range(5):
        while (delay := p.admit("generateContent")) > 0:
            clock.now += delay
    clock.now = 66.1
    assert p.admit("generateContent") > 0


def test_native_dispatch_receipts_and_scope(monkeypatch, tmp_path):
    import httpx

    clock = SimpleNamespace(now=0)
    original_pacer = pacing.RequestPacer
    monkeypatch.setattr(
        pacing, "RequestPacer", lambda policy: original_pacer(policy, clock=lambda: clock.now)
    )
    called = []

    async def sleep(seconds):
        clock.now += seconds

    async def send(client, request, *a, **kw):
        called.append(str(request.url))
        return httpx.Response(200, json={"usageMetadata": {"promptTokenCount": 100}})

    monkeypatch.setattr(asyncio, "sleep", sleep)
    monkeypatch.setattr(httpx.AsyncClient, "send", send)
    summary = {}
    output = tmp_path / "pacing.jsonl"

    async def run():
        with pacing.native_pacing(output, pacing.POLICY, summary):
            async with httpx.AsyncClient(trust_env=False) as client:
                assert client._transport._pool._ssl_context.verify_mode.name == "CERT_REQUIRED"
                assert client._transport._pool._ssl_context.check_hostname
                for action in ("countTokens", "generateContent", "generateContent"):
                    await client.post(
                        "https://generativelanguage.googleapis.com/v1beta/"
                        "models/gemini-3.5-flash-lite:" + action,
                        json={},
                    )
                await client.get("http://127.0.0.1:6333/collections")

    asyncio.run(run())
    rows = [json.loads(line) for line in output.read_text().splitlines()]
    assert len(called) == 4 and len(rows) == summary["request_pacing"]["dispatches"] == 3
    assert [r["input_tokens_reserved"] for r in rows] == [0, 40000, 40000]
    assert clock.now == 10.2
    assert "payload" not in output.read_text() and "headers" not in output.read_text()
    assert httpx.AsyncClient.send is send  # Context restored the previous transport.


def test_wait_cancelled_before_second_transport(monkeypatch, tmp_path):
    import httpx

    calls = []

    async def send(*a, **kw):
        calls.append(1)
        return httpx.Response(200, json={})

    async def sleep(seconds):
        raise asyncio.CancelledError

    monkeypatch.setattr(httpx.AsyncClient, "send", send)
    monkeypatch.setattr(asyncio, "sleep", sleep)
    output, summary = tmp_path / "pacing.jsonl", {}

    async def run():
        with pacing.native_pacing(output, pacing.POLICY, summary):
            async with httpx.AsyncClient(trust_env=False) as client:
                url = "https://generativelanguage.googleapis.com/v1beta/models/"
                url += "gemini-3.5-flash-lite:generateContent"
                await client.post(url, json={})
                with pytest.raises(asyncio.CancelledError):
                    await client.post(url, json={})

    asyncio.run(run())
    assert calls == [1] and len(output.read_text().splitlines()) == 1


def test_transport_failure_retains_dispatch(monkeypatch, tmp_path):
    import httpx

    async def send(*a, **kw):
        raise httpx.ConnectTimeout("synthetic")

    monkeypatch.setattr(httpx.AsyncClient, "send", send)
    output, summary = tmp_path / "pacing.jsonl", {}

    async def run():
        with pacing.native_pacing(output, pacing.POLICY, summary):
            async with httpx.AsyncClient(trust_env=False) as client:
                with pytest.raises(httpx.ConnectTimeout):
                    await client.post(
                        "https://generativelanguage.googleapis.com/v1beta/models/"
                        "gemini-3.5-flash-lite:generateContent",
                        json={},
                    )

    asyncio.run(run())
    assert summary["request_pacing"]["dispatches"] == 1
    assert len(output.read_text().splitlines()) == 1


def test_observed_token_overrun_stops_run(monkeypatch, tmp_path):
    import httpx

    async def send(*a, **kw):
        return httpx.Response(200, json={"usageMetadata": {"promptTokenCount": 40001}})

    monkeypatch.setattr(httpx.AsyncClient, "send", send)
    output, summary = tmp_path / "pacing.jsonl", {}

    async def run():
        with pacing.native_pacing(output, pacing.POLICY, summary):
            async with httpx.AsyncClient(trust_env=False) as client:
                with pytest.raises(RuntimeError, match="reservation"):
                    await client.post(
                        "https://generativelanguage.googleapis.com/v1beta/models/"
                        "gemini-3.5-flash-lite:generateContent",
                        json={},
                    )

    asyncio.run(run())
    assert summary["request_pacing"]["dispatches"] == 1
