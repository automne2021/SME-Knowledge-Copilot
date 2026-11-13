from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, SecretStr, StringConstraints, field_validator


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    username: Annotated[str, StringConstraints(pattern=r"^[a-z0-9][a-z0-9_.-]{2,63}$")]
    password: SecretStr = Field(min_length=1, max_length=128)

    @field_validator("username", mode="before")
    @classmethod
    def canonical_username(cls, value):
        return value.strip().lower() if isinstance(value, str) else value


class SessionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    title: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
    ] = "Cuộc trò chuyện mới"


class SessionRename(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
