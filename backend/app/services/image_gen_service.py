from __future__ import annotations

import logging
import re
import urllib.parse
from pathlib import Path
from uuid import uuid4

import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings

logger = logging.getLogger("amygdala.image_gen")


def _sanitize_model(raw_model: str | None) -> str:
    if not raw_model:
        return "flux"
    model = raw_model.strip().lower()
    if model.startswith("sk_") or len(model) > 30 or not re.match(r"^[a-zA-Z0-9_\-\./]+$", model):
        return "flux"
    return model


def _sanitize_prompt(raw_prompt: str) -> str:
    cleaned = re.sub(r"[\r\n\t]+", " ", raw_prompt).strip()
    cleaned = re.sub(r" {2,}", " ", cleaned)
    return cleaned[:1500]


async def generate_image_bytes(
    prompt: str,
    width: int = 1080,
    height: int = 1080,
    seed: int | None = None,
) -> tuple[bytes, str, str, str]:
    settings = get_settings()
    base_url = settings.pollinations_base_url.rstrip("/")
    model = _sanitize_model(settings.pollinations_model)
    clean_prompt = _sanitize_prompt(prompt)
    encoded_prompt = urllib.parse.quote(clean_prompt)

    params = [
        f"width={width}",
        f"height={height}",
        f"model={model}",
        "nologo=true",
    ]
    if seed is not None:
        params.append(f"seed={seed}")

    query_string = "&".join(params)
    image_url = f"{base_url}/{encoded_prompt}?{query_string}"

    logger.info("POLLINATIONS FLUX SEND size=%dx%d model=%s", width, height, model)

    try:
        async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
            response = await client.get(
                image_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            )
            response.raise_for_status()
            image_bytes = response.content
            content_type = response.headers.get("content-type", "image/jpeg").split(";", maxsplit=1)[0]
    except httpx.HTTPError as error:
        logger.error("POLLINATIONS FLUX ERROR: %s (url=%s)", error, image_url[:200])
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Pollinations FLUX image generation failed: {error}",
        ) from error

    extension = ".png" if "png" in content_type else ".jpg"
    generation_id = uuid4().hex
    filename = f"{generation_id}{extension}"
    output_dir = Path(settings.upload_dir) / "generated"
    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / filename
    out_file.write_bytes(image_bytes)

    relative_url = f"/static/uploads/generated/{filename}"
    logger.info("POLLINATIONS FLUX DONE bytes=%d file=%s", len(image_bytes), filename)
    return image_bytes, filename, relative_url, content_type


async def generate_image(
    prompt: str,
    width: int = 1080,
    height: int = 1080,
    seed: int | None = None,
) -> str:
    _, _, relative_url, _ = await generate_image_bytes(
        prompt=prompt,
        width=width,
        height=height,
        seed=seed,
    )
    return relative_url
