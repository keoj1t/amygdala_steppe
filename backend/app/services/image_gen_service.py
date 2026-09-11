from __future__ import annotations

import base64
import logging
import re
import urllib.parse
from pathlib import Path
from uuid import uuid4

import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings

logger = logging.getLogger("amygdala.image_gen")


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
    clean_prompt = _sanitize_prompt(prompt)
    model = settings.pollinations_model or "black-forest-labs/flux.2-klein-4b"
    api_key = settings.pollinations_api_key

    raw_image_bytes: bytes | None = None
    content_type = "image/jpeg"

    if api_key:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
        }
        payload = {
            "model": model,
            "prompt": clean_prompt,
            "size": f"{width}x{height}",
            "response_format": "url",
        }
        if seed is not None:
            payload["seed"] = seed

        logger.info("POLLINATIONS API POST model=%s size=%dx%d", model, width, height)

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    settings.pollinations_api_url,
                    headers=headers,
                    json=payload,
                )
            if response.status_code == 200:
                result = response.json()
                remote_url = None
                if isinstance(result, dict):
                    if "data" in result and isinstance(result["data"], list) and result["data"]:
                        remote_url = result["data"][0].get("url")
                    elif "image" in result:
                        remote_url = result["image"]

                if remote_url:
                    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as dl_client:
                        dl_resp = await dl_client.get(remote_url)
                        dl_resp.raise_for_status()
                        raw_image_bytes = dl_resp.content
                        content_type = dl_resp.headers.get("content-type", "image/jpeg").split(";", maxsplit=1)[0]
        except Exception as err:
            logger.warning("POLLINATIONS POST FAILED: %s. Falling back to direct URL generator.", err)

    if not raw_image_bytes:
        encoded_prompt = urllib.parse.quote(clean_prompt)
        base_url = settings.pollinations_base_url.rstrip("/")
        query_parts = [
            f"width={width}",
            f"height={height}",
            f"model={urllib.parse.quote(model)}",
            "nologo=true",
        ]
        if seed is not None:
            query_parts.append(f"seed={seed}")

        direct_url = f"{base_url}/{encoded_prompt}?{'&'.join(query_parts)}"
        get_headers = {"User-Agent": "Mozilla/5.0"}
        if api_key:
            get_headers["Authorization"] = f"Bearer {api_key}"

        logger.info("POLLINATIONS GET FALLBACK url=%s", direct_url[:160])

        try:
            async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
                get_resp = await client.get(direct_url, headers=get_headers)
                get_resp.raise_for_status()
                raw_image_bytes = get_resp.content
                content_type = get_resp.headers.get("content-type", "image/jpeg").split(";", maxsplit=1)[0]
        except httpx.HTTPError as error:
            logger.error("POLLINATIONS GENERATION FAILED: %s", error)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Pollinations image generation failed: {error}",
            ) from error

    if not raw_image_bytes:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Pollinations did not return valid image content",
        )

    extension = ".png" if "png" in content_type else ".jpg"
    generation_id = uuid4().hex
    filename = f"{generation_id}{extension}"
    output_dir = Path(settings.upload_dir) / "generated"
    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / filename
    out_file.write_bytes(raw_image_bytes)

    relative_url = f"/static/uploads/generated/{filename}"
    logger.info("POLLINATIONS DONE bytes=%d file=%s url=%s", len(raw_image_bytes), filename, relative_url)
    return raw_image_bytes, filename, relative_url, content_type


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
