from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.brandbook import BrandbookRead


class ProjectCreate(BaseModel):
    brandbook_id: UUID | None = None
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1, max_length=5000)


class ProjectUpdate(BaseModel):
    brandbook_id: UUID | None = None
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1, max_length=5000)


class ProjectRead(BaseModel):
    id: UUID
    user_id: UUID
    brandbook_id: UUID | None
    title: str
    description: str
    image_url: str | None = None
    brandbook: BrandbookRead | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
