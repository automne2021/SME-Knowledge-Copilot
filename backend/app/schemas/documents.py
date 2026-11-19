"""Document classification only; identity and lifecycle are never client writable."""

import uuid

from pydantic import BaseModel, ConfigDict


class DocumentFolderUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    folder_id: uuid.UUID | None
