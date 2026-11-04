"""Application answer contract; provider JSON alone is never sufficient validation."""

import re
import uuid
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictInt,
    StrictStr,
    StringConstraints,
    field_validator,
    model_validator,
)

from app.schemas.search import SearchFilters

ShortText = Annotated[
    str, StringConstraints(strict=True, strip_whitespace=True, min_length=1, max_length=500)
]
ClaimText = Annotated[
    str, StringConstraints(strict=True, strip_whitespace=True, min_length=1, max_length=1000)
]
EvidenceID = Annotated[str, StringConstraints(strict=True, pattern=r"^E[1-9][0-9]?$", max_length=3)]


class Claim(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    text: ClaimText
    evidence_ids: list[EvidenceID] = Field(min_length=1, max_length=10)

    @model_validator(mode="after")
    def references(self):
        if len(self.evidence_ids) != len(set(self.evidence_ids)):
            raise ValueError("duplicate_reference")
        # Rendered markers are backend-owned, including inline markers in claim text.
        if re.search(r"\[E\d+\]", self.text):
            raise ValueError("inline_reference")
        return self


class StructuredAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    answer_status: Literal["grounded", "partial", "insufficient_evidence"]
    claims: list[Claim] = Field(max_length=12)
    limitations: list[ShortText] = Field(max_length=5)
    missing_information: list[ShortText] = Field(max_length=5)
    conflict_detected: StrictBool

    @model_validator(mode="after")
    def status_contract(self):
        if self.answer_status == "insufficient_evidence":
            if self.claims or self.conflict_detected:
                raise ValueError("invalid_abstention")
        elif not self.claims:
            raise ValueError("missing_claims")
        if self.answer_status == "partial" and not (self.limitations or self.missing_information):
            raise ValueError("missing_partial_limit")
        if self.answer_status == "grounded" and (
            self.missing_information or self.conflict_detected
        ):
            raise ValueError("invalid_grounded")
        if self.conflict_detected:
            ids = {key for claim in self.claims for key in claim.evidence_ids}
            if self.answer_status != "partial" or len(ids) < 2:
                raise ValueError("conflict_needs_two_sources")
        return self


def validate_answer(raw, evidence):
    answer = StructuredAnswer.model_validate_json(raw)
    allowed = {item["evidence_id"] for item in evidence}
    if any(key not in allowed for claim in answer.claims for key in claim.evidence_ids):
        raise ValueError("unknown_evidence_id")
    return answer


class ChatQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: uuid.UUID
    client_request_id: uuid.UUID
    question: StrictStr = Field(min_length=1, max_length=4000)
    retrieval_mode: StrictStr = "dense"
    top_k: StrictInt | None = Field(default=None, ge=1, le=10)
    filters: SearchFilters = Field(default_factory=SearchFilters)

    @field_validator("question", mode="before")
    @classmethod
    def trim(cls, value):
        return value.strip() if isinstance(value, str) else value
