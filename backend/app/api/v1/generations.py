from __future__ import annotations

import json
import logging
import random
from pathlib import Path
from uuid import UUID, uuid4

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.db.session import get_db
from app.models.brandbook import Brandbook
from app.models.project import Project
from app.models.user import User
from app.schemas.generation import GenerationCreate, GenerationRead
from app.schemas.project import ProjectRead
from app.services.content_pipeline import parse_source_to_json
from app.services.grok_service import call_grok, get_mockup_scene_prompt
from app.services.image_gen_service import generate_image_bytes
from app.services.image_overlay import apply_poster_overlay
from app.services.mockup_engine import (
    composite_chroma_key_mockup,
    generate_all_mockup_urls,
)

router = APIRouter(prefix="/generations", tags=["generations"])
logger = logging.getLogger("amygdala.pipeline")

ASPECT_RATIO_DIMENSIONS: dict[str, tuple[int, int]] = {
    "1:1": (1080, 1080),
    "9:16": (1080, 1920),
    "16:9": (1920, 1080),
    "4:5": (1080, 1350),
}


def absolute_media_url(request: Request, value: str | None) -> str | None:
    if not value or value.startswith(("http://", "https://", "data:")):
        return value
    return str(request.base_url).rstrip("/") + "/" + value.lstrip("/")


def project_response(project: Project, request: Request) -> ProjectRead:
    data = ProjectRead.model_validate(project).model_dump()
    if data.get("image_url"):
        data["image_url"] = absolute_media_url(request, data["image_url"])
    if data.get("brandbook") and data["brandbook"].get("logo_url"):
        data["brandbook"]["logo_url"] = absolute_media_url(request, data["brandbook"]["logo_url"])
    return ProjectRead.model_validate(data)


def detect_locale(text: str, selected_locale: str) -> str:
    if selected_locale != "en":
        return selected_locale
    if any(character in text for character in "ӘәҒғҚқҢңӨөҰұҮүҺһІі"):
        return "kk"
    if any("А" <= character <= "я" or character in "Ёё" for character in text):
        return "ru"
    return "en"


class MockupRequest(BaseModel):
    project_id: UUID | None = None
    image_url: str | None = None
    template: str = "poster"
    scene_context: str | None = None


@router.post("/mockup")
async def create_mockup_endpoint(
    payload: MockupRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    settings = get_settings()
    image_bytes: bytes | None = None

    if payload.project_id:
        project = await db.scalar(
            select(Project).where(Project.id == payload.project_id, Project.user_id == current_user.id)
        )
        if not project or not project.image_url:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project or project image not found")
        img_rel = project.image_url.removeprefix("/static/uploads/").lstrip("/")
        local_path = Path(settings.upload_dir) / img_rel
        if local_path.exists():
            image_bytes = local_path.read_bytes()

    if not image_bytes and payload.image_url:
        try:
            if payload.image_url.startswith(("http://", "https://")):
                async with httpx.AsyncClient(timeout=30) as client:
                    resp = await client.get(payload.image_url)
                    resp.raise_for_status()
                    image_bytes = resp.content
            else:
                img_rel = payload.image_url.removeprefix("/static/uploads/").lstrip("/")
                local_path = Path(settings.upload_dir) / img_rel
                if local_path.exists():
                    image_bytes = local_path.read_bytes()
        except Exception as err:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not load source image: {err}")

    if not image_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No valid source image provided")

    output_dir = Path(settings.upload_dir) / "generated"

    if payload.scene_context and payload.scene_context in {"billboard", "poster_frame", "phone"}:
        scene_prompt = get_mockup_scene_prompt(payload.scene_context)
        scene_seed = random.SystemRandom().randint(1, 2_147_483_647)
        try:
            scene_bytes, _, _, _ = await generate_image_bytes(
                prompt=scene_prompt,
                width=1080,
                height=1080,
                seed=scene_seed,
            )
            _, _, dyn_url = composite_chroma_key_mockup(
                scene_bytes=scene_bytes,
                poster_bytes=image_bytes,
                fallback_key=payload.scene_context,
                output_dir=output_dir,
            )
            abs_dyn = absolute_media_url(request, dyn_url) or dyn_url
            return {
                payload.scene_context: abs_dyn,
                "dynamic": abs_dyn,
            }
        except Exception as err:
            logger.warning("DYNAMIC SCENE GENERATION FALLBACK: %s", err)

    mockup_results = generate_all_mockup_urls(image_bytes, output_dir=output_dir)
    return {k: absolute_media_url(request, v) or v for k, v in mockup_results.items()}


@router.post("", response_model=GenerationRead, status_code=status.HTTP_201_CREATED)
async def create_generation(
    payload: GenerationCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GenerationRead:
    project = await db.scalar(
        select(Project).where(Project.id == payload.project_id, Project.user_id == current_user.id)
    )
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    settings = get_settings()
    if not settings.groq_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GROQ_API_KEY is not configured on the backend",
        )

    brandbook: Brandbook | None = None
    if payload.brandbook_id is not None:
        brandbook = await db.scalar(select(Brandbook).where(Brandbook.id == payload.brandbook_id, Brandbook.user_id == current_user.id))
        if brandbook is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid brandbook")
        project.brandbook_id = brandbook.id
        await db.flush()
    
    if project.brandbook_id:
        brandbook = brandbook or await db.scalar(select(Brandbook).where(Brandbook.id == project.brandbook_id, Brandbook.user_id == current_user.id))

    source_text: str | None = None
    source_platform: str | None = None
    parser_name: str | None = None

    if payload.source_url:
        try:
            parsed_post = await parse_source_to_json(payload.source_url)
            source_text = str(parsed_post["text"])
            source_platform = str(parsed_post["platform"])
            parser_name = str(parsed_post["parser"])
            logger.info("GENERATION PARSED source_url=%s parser=%s", payload.source_url, parser_name)
            grok_input = source_text
        except (httpx.HTTPError, ValueError) as error:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Не удалось обработать ссылку: {error}",
            ) from error
    else:
        logger.info("PARSER SKIP direct_text_input=true text_chars=%d", len(payload.prompt))
        grok_input = payload.prompt
        source_platform = "direct"

    locale = detect_locale(grok_input, payload.locale)
    try:
        grok_result = await call_grok(
            input_content=grok_input,
            generation_mode=payload.mode,
            visual_style=payload.visual_style,
            tone_of_voice=payload.tone_of_voice,
            locale=locale,
            brandbook=brandbook,
        )
    except (httpx.HTTPError, ValueError, KeyError) as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Grok API error: {error}",
        ) from error

    image_prompt = grok_result.image_prompt
    headline = grok_result.headline
    post_text_body = grok_result.post_text

    prompt_dir = Path(settings.upload_dir).parent / "prompts"
    prompt_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = prompt_dir / f"{uuid4().hex}.json"
    prompt_path.write_text(
        json.dumps(
            {
                "source_url": payload.source_url,
                "platform": source_platform,
                "parser": parser_name,
                "mode": payload.mode,
                "aspect_ratio": payload.aspect_ratio,
                "visual_style": payload.visual_style,
                "tone_of_voice": payload.tone_of_voice,
                "headline": headline,
                "post_text": post_text_body,
                "image_prompt": image_prompt,
                "brandbook_applied": brandbook is not None,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    logger.info("PROMPT SAVED path=%s chars=%d", prompt_path, len(image_prompt))

    generation_seed = random.SystemRandom().randint(1, 2_147_483_647)
    target_width, target_height = ASPECT_RATIO_DIMENSIONS.get(payload.aspect_ratio, (1080, 1080))

    image_bytes, filename, output_url, content_type = await generate_image_bytes(
        prompt=image_prompt,
        width=target_width,
        height=target_height,
        seed=generation_seed,
    )

    effective_source_url = (
        payload.source_url
        or (payload.prompt.strip() if payload.prompt.strip().startswith(("http://", "https://")) else None)
    )

    output_dir = Path(settings.upload_dir) / "generated"
    output_dir.mkdir(parents=True, exist_ok=True)

    if payload.mode == "poster":
        try:
            image_bytes = await apply_poster_overlay(
                image_bytes=image_bytes,
                brandbook=brandbook,
                headline=headline,
                upload_dir=settings.upload_dir,
                source_url=effective_source_url,
            )
            content_type = "image/jpeg"
            out_file = output_dir / filename
            out_file.write_bytes(image_bytes)
        except Exception as error:
            logger.warning("POSTER OVERLAY FAILED error=%s", error)

    mockup_map: dict[str, str] = {}
    try:
        mockup_map = generate_all_mockup_urls(image_bytes, output_dir=output_dir)
    except Exception as err:
        logger.warning("MOCKUP GENERATION FAILED error=%s", err)

    primary_mockup_key = "poster" if payload.mode == "poster" else "instagram"
    mockup_url = mockup_map.get(primary_mockup_key) or mockup_map.get("poster")

    project.image_url = output_url
    await db.commit()
    project = await db.scalar(
        select(Project).options(joinedload(Project.brandbook)).where(Project.id == project.id)
    )

    logger.info("GENERATION RETURN project=%s image=%s mockup=%s", payload.project_id, output_url, mockup_url)

    abs_output_url = absolute_media_url(request, output_url) or output_url
    abs_mockup_url = absolute_media_url(request, mockup_url) if mockup_url else None
    abs_mockups = {k: absolute_media_url(request, v) or v for k, v in mockup_map.items()}

    return GenerationRead(
        id=filename.split(".")[0],
        status="succeeded",
        output=[abs_output_url],
        project_id=payload.project_id,
        image_url=abs_output_url,
        mockup_url=abs_mockup_url,
        mockups=abs_mockups,
        headline=headline,
        post_text=post_text_body,
        enhanced_prompt=image_prompt,
        source_text=source_text,
        source_platform=source_platform,
        parser=parser_name,
        project=project_response(project, request),
    )
