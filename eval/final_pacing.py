"""Eval-only rolling request/token reservations; no provider imports offline."""

import time
from collections import deque
from threading import Lock

POLICY = {
    "window_seconds": 61,
    "max_requests": 12,
    "min_interval_seconds": 5.1,
    "max_input_tokens": 200000,
    "input_tokens_per_generation": 40000,
}


class RequestPacer:
    """Reserve before dispatch; failed transports retain reservations, no retries.

    Tokens concern generation. Count calls also consume our conservative request
    allowance. This process cannot control other clients of the same project.
    """

    def __init__(self, policy, *, clock=time.monotonic):
        if policy != POLICY:
            raise ValueError("Expected the frozen conservative free-tier pacing policy")
        self.policy, self.clock = dict(policy), clock
        self.events, self.lock = deque(), Lock()

    def admit(self, action):
        """Return wait seconds, or zero after atomically reserving dispatch."""
        if action not in {"countTokens", "generateContent"}:
            raise ValueError("Unknown paced action")
        tokens = self.policy["input_tokens_per_generation"] if action == "generateContent" else 0
        with self.lock:
            now = self.clock()
            window = self.policy["window_seconds"]

            # A small boundary margin avoids float subtraction admitting early.
            def expires(stamp):
                return stamp + window + 0.001

            while self.events and now >= expires(self.events[0][0]):
                self.events.popleft()
            wait = 0
            if self.events:
                wait = max(0, self.events[-1][0] + self.policy["min_interval_seconds"] - now)
            if len(self.events) >= self.policy["max_requests"]:
                wait = max(wait, expires(self.events[0][0]) - now)
            total = sum(e[1] for e in self.events)
            if total + tokens > self.policy["max_input_tokens"]:
                for stamp, reserved in self.events:
                    total -= reserved
                    if total + tokens <= self.policy["max_input_tokens"]:
                        wait = max(wait, expires(stamp) - now)
                        break
            if wait > 0:
                return wait
            self.events.append((now, tokens))
            return 0


def native_pacing(output, policy, summary):
    """Wrap only Gemini dispatch; preserve native provider and TLS verification."""
    import asyncio
    import json
    import ssl
    from contextlib import contextmanager
    from pathlib import Path
    from unittest.mock import patch

    import certifi
    import httpx
    import httpx._transports.default as transport

    from app.services.gemini import BASE_URL, MODEL

    @contextmanager
    def context():
        pacer = RequestPacer(policy)
        started = time.monotonic()
        original = httpx.AsyncClient.send
        original_ssl = transport.create_ssl_context
        tls = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        tls.load_verify_locations(cadata=Path(certifi.where()).read_text(encoding="ascii"))

        def ssl_context(verify=True, cert=None, trust_env=True):
            # Same verified certifi trust roots; avoid repeated slow Windows cafile loads.
            if verify is True and cert is None and not trust_env:
                return tls
            return original_ssl(verify=verify, cert=cert, trust_env=trust_env)

        summary["request_pacing"] = {"policy": dict(policy), "dispatches": 0, "wait_ms": 0}
        with output.open("x", encoding="utf-8") as receipts:

            async def send(client, request, *args, **kwargs):
                actions = {
                    BASE_URL + "/models/" + MODEL + ":" + a: a
                    for a in ("countTokens", "generateContent")
                }
                action = actions.get(str(request.url))
                if action is None:
                    return await original(client, request, *args, **kwargs)
                before = time.monotonic()
                while (delay := pacer.admit(action)) > 0:
                    # Await remains inside GeminiProvider's existing HTTP timeout.
                    await asyncio.sleep(delay)
                waited = round((time.monotonic() - before) * 1000, 3)
                receipt = {
                    "action": action,
                    "dispatch_elapsed_ms": round((time.monotonic() - started) * 1000, 3),
                    "wait_ms": waited,
                    "input_tokens_reserved": (
                        policy["input_tokens_per_generation"] if action == "generateContent" else 0
                    ),
                }
                receipts.write(json.dumps(receipt) + "\n")
                receipts.flush()
                summary["request_pacing"]["dispatches"] += 1
                summary["request_pacing"]["wait_ms"] += waited
                response = await original(client, request, *args, **kwargs)
                if action == "generateContent" and response.status_code == 200:
                    usage = response.json().get("usageMetadata")
                    actual = usage.get("promptTokenCount") if isinstance(usage, dict) else None
                    if type(actual) is int and actual > policy["input_tokens_per_generation"]:
                        raise RuntimeError("Input exceeded pacing reservation; stop run")
                return response

            with (
                patch("httpx.AsyncClient.send", send),
                patch.object(transport, "create_ssl_context", ssl_context),
            ):
                yield

    return context()
