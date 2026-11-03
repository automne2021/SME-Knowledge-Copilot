"""Strict search contract; clients cannot select workspace/model/provider/collection."""

import uuid

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr, field_validator


class SearchFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")
    document_ids: list[uuid.UUID] = Field(default_factory=list, max_length=50)

    @field_validator("document_ids")
    @classmethod
    def unique_ids(cls, value):
        if len(value) != len(set(value)):
            raise ValueError("Document IDs must be distinct")
        return value


class SearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: StrictStr = Field(min_length=1, max_length=4000)
    top_k: StrictInt | None = Field(default=None, ge=1, le=10)
    mode: StrictStr = "dense"
    filters: SearchFilters = Field(default_factory=SearchFilters)

    @field_validator("query", mode="before")
    @classmethod
    def trim_query(cls, value):
        return value.strip() if isinstance(value, str) else value
