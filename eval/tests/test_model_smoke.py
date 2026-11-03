"""Contract tests using fake inputs/transport. Real inference is in versioned smoke runs."""

import json

import httpx
import pytest

from eval.embedding_runtime import InputTooLong, check_lengths, prepare_inputs
from eval.gemini_smoke import (
    BASE_URL,
    MODEL,
    SmokeProviderError,
    generate,
    preflight,
    request_payload,
    validate_answer,
)
from eval.model_smoke import llm_cases, llm_smoke


def settings():
    return {
        "LLM_API_KEY": "fake-contract-key",
        "LLM_MODEL": MODEL,
        "LLM_BASE_URL": BASE_URL,
        "LLM_FREE_TIER_CONFIRMED": "true",
        "LLM_QUOTA_CONFIRMED": "true",
    }


def answer():
    return {
        "answer_status": "grounded",
        "claims": [{"text": "12 ngày phép.", "evidence_ids": ["G1"]}],
        "missing_evidence": [],
    }


def test_e5_prefix_is_explicit_for_both_roles():
    assert prepare_inputs(["Nghỉ phép"], "query") == ["query: Nghỉ phép"]
    assert prepare_inputs(["Tiêu đề\nNội dung"], "passage") == ["passage: Tiêu đề\nNội dung"]


@pytest.mark.parametrize("texts", [[], [""], ["  "], [None]])
def test_empty_embedding_input_is_rejected(texts):
    with pytest.raises(ValueError, match="nonempty"):
        prepare_inputs(texts, "passage")


def test_length_guard_includes_special_tokens_and_disables_truncation():
    def tokenizer(inputs, **kwargs):
        assert kwargs == {"truncation": False}
        return {"input_ids": [[0] * (len(text.split()) + 2) for text in inputs]}

    assert check_lengths(tokenizer, ["xin " * 510]) == [512]
    with pytest.raises(InputTooLong):
        check_lengths(tokenizer, ["xin " * 511])


@pytest.mark.parametrize(
    "key",
    ["LLM_API_KEY", "LLM_MODEL", "LLM_BASE_URL", "LLM_FREE_TIER_CONFIRMED", "LLM_QUOTA_CONFIRMED"],
)
def test_incomplete_free_tier_preflight_never_sends(key):
    values = settings()
    values.pop(key)

    def unexpected(request):
        pytest.fail("HTTP sent before preflight completed")

    with httpx.Client(transport=httpx.MockTransport(unexpected)) as client:
        with pytest.raises(SmokeProviderError, match="preflight_failed"):
            generate(values, "Question", [], client)
    assert preflight(values)


def test_request_uses_structured_schema_without_tools_or_key_in_body():
    payload = request_payload("Question", [])
    assert payload["generationConfig"]["responseFormat"]["text"]["mimeType"] == "APPLICATION_JSON"
    assert "tools" not in payload
    assert "api_key" not in json.dumps(payload)


@pytest.mark.parametrize(
    "modification",
    ["unknown_id", "missing_conditions", "extra_field", "unsupported_claim", "empty_claim_text"],
)
def test_invalid_answer_is_rejected(modification):
    obj = answer()
    if modification == "unknown_id":
        obj["claims"][0]["evidence_ids"] = ["E999"]
    elif modification == "missing_conditions":
        obj["answer_status"] = "partial"
    elif modification == "extra_field":
        obj["extra"] = "unexpected"
    elif modification == "unsupported_claim":
        obj["answer_status"] = "insufficient_evidence"
    else:
        obj["claims"][0]["text"] = " "
    with pytest.raises(ValueError):
        validate_answer(json.dumps(obj), {"G1"})


def test_valid_abstention_has_no_business_claims():
    obj = {
        "answer_status": "insufficient_evidence",
        "claims": [],
        "missing_evidence": ["Không có chính sách năm 2030."],
    }
    assert validate_answer(json.dumps(obj), set()).answer_status == "insufficient_evidence"


def test_native_response_is_parsed_without_storing_thoughts():
    def handler(request):
        assert request.headers["x-goog-api-key"] == "fake-contract-key"
        assert not request.url.query
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "finishReason": "STOP",
                        "content": {
                            "parts": [
                                {"thought": True, "text": "not a business answer"},
                                {"text": json.dumps(answer())},
                            ]
                        },
                    }
                ],
                "usageMetadata": {"totalTokenCount": 30},
                "modelVersion": "fake-test-version",
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = generate(
            settings(), "Question", [{"evidence_id": "G1", "text": "12 ngày"}], client
        )
    assert result["answer"]["claims"][0]["evidence_ids"] == ["G1"]
    assert "not a business answer" not in json.dumps(result)


@pytest.mark.parametrize("status", [400, 401, 429, 500])
def test_provider_failure_is_one_call_without_response_body_leak(status):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(status, text="fake-contract-key: sensitive error body")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(SmokeProviderError, match=f"http_{status}") as error:
            generate(settings(), "Question", [], client)
    assert len(calls) == 1
    assert "fake-contract-key" not in str(error.value)


def test_llm_runner_stops_at_first_quota_error(monkeypatch):
    for key, value in settings().items():
        monkeypatch.setenv(key, value)
    client_type = httpx.Client
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(429)

    monkeypatch.setattr(
        httpx,
        "Client",
        lambda **kwargs: client_type(transport=httpx.MockTransport(handler), **kwargs),
    )
    result, rows = llm_smoke({"max_calls": 5})
    assert result["status"] == "failed"
    assert len(calls) == len(rows) == result["api_calls_attempted"] == 1
    assert rows[0]["error_code"] == "http_429"


def test_llm_smoke_uses_dev_and_explicit_adhoc_case():
    assert {case["id"] for case in llm_cases()} == {
        "q001",
        "q007",
        "q009",
        "q014",
        "adhoc_conflict_not_human_gold",
    }


@pytest.mark.parametrize("violation", ["partial_without_missing", "extra_field"])
def test_invalid_response_retains_usage_without_raw_inputs(violation):
    obj = answer()
    if violation == "partial_without_missing":
        obj["answer_status"] = "partial"
        expected = "partial_missing_evidence"
    else:
        obj["unexpected"] = "fake-contract-key private input"
        expected = "schema_validation_failed"

    def handler(request):
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {"finishReason": "STOP", "content": {"parts": [{"text": json.dumps(obj)}]}}
                ],
                "usageMetadata": {"totalTokenCount": 31, "unexpectedSecret": "must-not-log"},
                "modelVersion": MODEL,
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(SmokeProviderError, match=expected) as error:
            generate(settings(), "Question", [{"evidence_id": "G1"}], client)
    assert error.value.metadata["usage"] == {"totalTokenCount": 31}
    assert error.value.metadata["model_version"] == MODEL
    assert "fake-contract-key" not in json.dumps(error.value.metadata)
    assert "must-not-log" not in json.dumps(error.value.metadata)


def test_selected_conflict_case_sends_one_request(monkeypatch):
    for key, value in settings().items():
        monkeypatch.setenv(key, value)
    client_type = httpx.Client
    calls = []

    def handler(request):
        calls.append(request)
        obj = {
            "answer_status": "partial",
            "claims": [
                {"text": "Bản A ghi 12 ngày.", "evidence_ids": ["E1"]},
                {"text": "Bản B ghi 15 ngày.", "evidence_ids": ["E2"]},
            ],
            "missing_evidence": ["Thiếu căn cứ ngày hiệu lực."],
        }
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {"finishReason": "STOP", "content": {"parts": [{"text": json.dumps(obj)}]}}
                ],
                "usageMetadata": {"totalTokenCount": 31},
                "modelVersion": MODEL,
            },
        )

    monkeypatch.setattr(
        httpx,
        "Client",
        lambda **kwargs: client_type(transport=httpx.MockTransport(handler), **kwargs),
    )
    result, rows = llm_smoke({"max_calls": 5}, "adhoc_conflict_not_human_gold")
    assert result["status"] == "passed"
    assert len(calls) == len(rows) == result["api_calls_attempted"] == 1
    assert result["requested_case_ids"] == ["adhoc_conflict_not_human_gold"]


def test_unknown_case_is_rejected_before_network():
    with pytest.raises(ValueError, match="Unknown smoke case ID"):
        llm_smoke({"max_calls": 5}, "q024_test_not_allowed")


@pytest.mark.parametrize("limit", [0, -1, True, 6])
def test_invalid_call_limit_cannot_report_zero_call_success(limit):
    with pytest.raises(ValueError, match="max_calls must be an integer"):
        llm_smoke({"max_calls": limit})
