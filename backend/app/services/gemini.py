"""Native Gemini only; hard wall-clock HTTP bounds, no retries/tools/paid fallback."""

import asyncio
import logging

import httpx

from app.core.errors import AppError
from app.services.answering import remaining

BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
MODEL = "gemini-3.5-flash-lite"
logger = logging.getLogger(__name__)

# Provider failures keep the public code model_unavailable (eval runners and clients rely on it);
# details.reason tells the user whether to wait for quota, retry later, or fix configuration.
FAILURE_MESSAGES = {
    "quota": "Đã chạm giới hạn quota free tier của Gemini; thử lại sau.",
    "overloaded": "Gemini đang quá tải hoặc lỗi tạm thời; thử lại sau ít phút.",
    "rejected": "Gemini từ chối yêu cầu; kiểm tra cấu hình API key và model.",
    "network": "Không kết nối được tới Gemini.",
}


def failure_reason(status_code: int) -> str:
    if status_code == 429:
        return "quota"
    return "overloaded" if status_code >= 500 else "rejected"


class GeminiProvider:
    def __init__(self, settings):
        self.settings = settings
        if (
            settings.llm_base_url != BASE_URL
            or settings.llm_model != MODEL
            or not settings.llm_api_key
            or not settings.llm_api_key.get_secret_value()
            or not settings.llm_free_tier_confirmed
            or not settings.llm_quota_confirmed
        ):
            raise AppError(
                503, "model_unavailable", "Cần cấu hình model và xác nhận free tier/quota."
            )

    async def _post_async(self, action, payload, timeout):
        try:
            async with asyncio.timeout(timeout):
                async with httpx.AsyncClient(trust_env=False, follow_redirects=False) as client:
                    response = await client.post(
                        f"{BASE_URL}/models/{MODEL}:{action}",
                        headers={"x-goog-api-key": self.settings.llm_api_key.get_secret_value()},
                        json=payload,
                        timeout=timeout,
                    )
        except (TimeoutError, httpx.TimeoutException):
            logger.warning("Gemini %s timed out after %.0f s", action, timeout)
            raise AppError(
                504, "model_timeout", "Gemini không phản hồi trong thời gian cho phép."
            ) from None
        except httpx.RequestError:
            logger.warning("Gemini %s network error", action)
            raise AppError(
                503, "model_unavailable", FAILURE_MESSAGES["network"], {"reason": "network"}
            ) from None
        if response.status_code != 200:
            # Status only: provider bodies may echo request content and are never logged.
            reason = failure_reason(response.status_code)
            logger.warning("Gemini %s returned HTTP %s (%s)", action, response.status_code, reason)
            raise AppError(503, "model_unavailable", FAILURE_MESSAGES[reason], {"reason": reason})
        try:
            body = response.json()
            if not isinstance(body, dict):
                raise ValueError
            return body
        except ValueError:
            raise AppError(
                502, "invalid_model_output", "Provider trả dữ liệu không hợp lệ."
            ) from None

    def _post(self, action, payload, deadline):
        return asyncio.run(
            self._post_async(
                action, payload, min(remaining(deadline), self.settings.llm_call_timeout_seconds)
            )
        )

    def count_tokens(self, payload, deadline):
        body = self._post(
            "countTokens",
            {"generateContentRequest": {"model": "models/" + MODEL, **payload}},
            deadline,
        )
        count = body.get("totalTokens")
        if type(count) is not int or count < 0:
            raise AppError(502, "invalid_model_output", "Provider trả token count không hợp lệ.")
        return count

    def generate(self, payload, deadline):
        body = self._post("generateContent", payload, deadline)
        usage = body.get("usageMetadata", {})
        safe_usage = {
            key: value
            for key, value in (usage.items() if isinstance(usage, dict) else [])
            if key
            in {
                "promptTokenCount",
                "candidatesTokenCount",
                "totalTokenCount",
                "thoughtsTokenCount",
                "cachedContentTokenCount",
            }
            and type(value) is int
            and value >= 0
        }
        try:
            candidate = body["candidates"][0]
            parts = candidate.get("content", {}).get("parts", [])
            if not isinstance(parts, list) or any(
                not isinstance(p, dict)
                or (
                    not p.get("thought")
                    and (
                        not isinstance(p.get("text"), str)
                        or set(p) - {"text", "thought", "thoughtSignature"}
                    )
                )
                for p in parts
            ):
                raise ValueError
            text = "".join(p["text"] for p in parts if not p.get("thought"))
            if len(text) > 100_000:
                raise ValueError
            return {
                "text": text,
                "finish_reason": candidate.get("finishReason"),
                "usage": safe_usage or None,
                "model_version": body.get("modelVersion")
                if isinstance(body.get("modelVersion"), str)
                else None,
            }
        except (KeyError, IndexError, TypeError, AttributeError, ValueError):
            # No raw output/thoughts/provider body retained or attached to errors.
            return {
                "text": "",
                "finish_reason": "INVALID",
                "usage": safe_usage or None,
                "model_version": None,
            }
