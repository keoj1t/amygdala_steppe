from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


hex_pattern = r"^#[0-9A-Fa-f]{6}$"


class BrandbookBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    primary_color: str = Field(pattern=hex_pattern)
    secondary_color: str = Field(pattern=hex_pattern)
    text_color: str = Field(pattern=hex_pattern)
    background_color: str = Field(pattern=hex_pattern)
    font_header: str = Field(min_length=1, max_length=120)
    font_body: str = Field(min_length=1, max_length=120)
    font_family: str = Field(default="Inter", min_length=1, max_length=120)


class BrandbookCreate(BrandbookBase):
    pass


class BrandbookUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    primary_color: str | None = Field(default=None, pattern=hex_pattern)
    secondary_color: str | None = Field(default=None, pattern=hex_pattern)
    text_color: str | None = Field(default=None, pattern=hex_pattern)
    background_color: str | None = Field(default=None, pattern=hex_pattern)
    font_header: str | None = Field(default=None, min_length=1, max_length=120)
    font_body: str | None = Field(default=None, min_length=1, max_length=120)
    font_family: str | None = Field(default=None, min_length=1, max_length=120)


class BrandbookRead(BrandbookBase):
    id: UUID
    user_id: UUID
    logo_url: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
