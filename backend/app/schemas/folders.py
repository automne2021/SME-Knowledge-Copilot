"""Folder names are trimmed; scope and creator always come from authenticated identity."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints


class FolderName(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
