from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.project import ProjectRead


class GenerationCreate(BaseModel):
    project_id: UUID
    prompt: str = Field(min_length=1, max_length=5000)
    mode: str = Field(default="poster", pattern="^(poster|post|background)$")
    aspect_ratio: str = Field(default="1:1", pattern="^(1:1|9:16|16:9|4:5)$")
    source_url: str | None = None
    visual_style: str = Field(default="Editorial Photo", max_length=120)
    tone_of_voice: str = Field(default="Expert", max_length=120)
    locale: str = Field(default="en", pattern="^(kk|ru|en)$")
    brandbook_id: UUID | None = None


class GenerationRead(BaseModel):
    id: str
    status: str
    output: list[str] | str | None = None
    image_url: str | None = None
    mockup_url: str | None = None
    mockups: dict[str, str] | None = None
    project_id: UUID
    headline: str | None = None
    post_text: str | None = None
    enhanced_prompt: str | None = None
    source_text: str | None = None
    source_platform: str | None = None
    parser: str | None = None
    project: ProjectRead | None = None
