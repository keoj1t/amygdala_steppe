import html
import json
import logging
import re
import asyncio
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

import httpx

from app.core.config import get_settings
from .parsers import parse_telegram, parse_instagram, parse_linkedin, parse_web

logger = logging.getLogger("amygdala.pipeline")

_NO_TEXT_SUFFIX = "--no text, letters, typography, watermark, signature, logos, words, gibberish"

META_PATTERN = re.compile(
    r'<meta\s+(?:[^>]*?\s)?(?:property|name)=["\']([^"\']+)["\'][^>]*?content=["\']([^"\']*)["\'][^>]*>',
    re.IGNORECASE,
)
REVERSE_META_PATTERN = re.compile(
    r'<meta\s+(?:[^>]*?\s)?content=["\']([^"\']*)["\'][^>]*?(?:property|name)=["\']([^"\']+)["\'][^>]*>',
    re.IGNORECASE,
)


def _metadata(page: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for key, value in [*META_PATTERN.findall(page), *[(name, value) for value, name in REVERSE_META_PATTERN.findall(page)]]:
        values.setdefault(key.lower(), html.unescape(value).strip())
    return values


def _platform(url: str) -> str:
    hostname = urlparse(url).netloc.lower()
    if "instagram" in hostname:
        return "instagram"
    if "linkedin" in hostname:
        return "linkedin"
    if "t.me" in hostname or "telegram" in hostname:
        return "telegram"
    return "web"


async def parse_source_url(source_url: str) -> tuple[str, str, str]:
    platform = _platform(source_url)
    if platform == "telegram":
        return await parse_telegram(source_url)
    elif platform == "instagram":
        return await parse_instagram(source_url)
    elif platform == "linkedin":
        return await parse_linkedin(source_url)
    else:
        return await parse_web(source_url)


async def parse_source_to_json(source_url: str) -> dict[str, str | None]:
    logger.info("PARSER START url=%s", source_url)
    text, platform, parser_name = await parse_source_url(source_url)
    parsed = {
        "source_url": source_url,
        "platform": platform,
        "parser": parser_name,
        "title": text.split("\n", maxsplit=1)[0][:240],
        "text": text,
        "media_url": None,
    }
    parsed_dir = Path(get_settings().upload_dir).parent / "parsed"
    parsed_dir.mkdir(parents=True, exist_ok=True)
    json_path = parsed_dir / f"{uuid4().hex}.json"
    json_path.write_text(
        json.dumps(parsed, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info(
        "PARSER DONE parser=%s platform=%s text_chars=%d json=%s",
        parser_name,
        platform,
        len(text),
        json_path,
    )
    return parsed


async def extract_source_text(source_url: str) -> tuple[str, str]:
    text, platform, _ = await parse_source_url(source_url)
    return text, platform


async def improve_prompt(
    source_text: str,
    platform: str,
    mode: str,
    brandbook_context: str | None = None,
) -> str:
    settings = get_settings()

    if mode == "poster":
        format_instruction = (
            "Format: POSTER 1:1 (1024x1024). Bold monolithic composition, clean negative space reserved for typography."
        )
    else:
        format_instruction = (
            "Format: POST / FEED 4:5 (1080x1350). Cinematic 3D render, luxury editorial fashion aesthetics."
        )

    user_message_parts = [
        f"Source content ({platform}):\n{source_text}\n\n",
        f"{format_instruction}\n",
    ]

    if brandbook_context:
        user_message_parts.append(
            f"\nBrand Identity:\n{brandbook_context}\n"
        )
    else:
        user_message_parts.append(
            "\nColor palette: #CC5500 warm amber with #ADD8E6 arctic blue highlights.\n"
        )

    user_message_parts.append(
        f"\nCreate a detailed FLUX prompt in English with cinematic lighting, 85mm lens, luxury materials, and concluding with '{_NO_TEXT_SUFFIX}'."
    )

    fallback = (
        f"A luxury commercial advertising visual for {source_text[:300]}. "
        f"85mm lens f/1.4, cinematic volumetric lighting, raytracing, soft studio rim light, 8k resolution {_NO_TEXT_SUFFIX}"
    )

    if not settings.groq_api_key:
        return fallback

    payload = {
        "model": settings.groq_model,
        "temperature": 0.7,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an award-winning Creative Director. Convert the source text into an elite English image prompt "
                    f"for FLUX. Return ONLY the prompt text ending with {_NO_TEXT_SUFFIX}."
                ),
            },
            {
                "role": "user",
                "content": "".join(user_message_parts),
            },
        ],
    }

    headers = {"Authorization": f"Bearer {settings.groq_api_key}", "Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(settings.groq_api_url, headers=headers, json=payload)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            prompt = str(content).strip() or fallback
            if _NO_TEXT_SUFFIX not in prompt:
                prompt = f"{prompt.rstrip('.')} {_NO_TEXT_SUFFIX}"
            return prompt
    except Exception as err:
        logger.warning("GROQ PROMPT IMPROVE ERROR: %s", err)
        return fallback
