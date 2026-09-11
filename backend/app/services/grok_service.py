from __future__ import annotations

import json
import logging
import re
from typing import Optional

import httpx

from app.core.config import get_settings
from app.models.brandbook import Brandbook

logger = logging.getLogger("amygdala.grok")

_NO_TEXT_SUFFIX = "--no text, letters, typography, writing, words, signature, watermark, logos, clutter, noise, ugly, cartoon, low quality, distorted"

_MODE_INSTRUCTIONS: dict[str, str] = {
    "poster": (
        "- Generation Mode: POSTER (Monumental 3D Commercial Billboard & Swiss Design Aesthetic).\n"
        "- Zero Clutter & Single Hero Focus: Exactly ONE central monumental hero object or iconic physical subject (Focal Point).\n"
        "- 70/30 Negative Space Rule: 70% of the canvas MUST be clean, deep, aesthetic negative space (#0D0E11 dark moody gradient) specifically reserved for bold headline and logo overlay."
    ),
    "post": (
        "- Generation Mode: POST (Editorial Advertising & Luxury Social Media Art).\n"
        "- Single mesmerizing focal object or luxury commercial editorial composition with deep focal depth (85mm f/1.4 lens) and creamy bokeh background.\n"
        "- 70/30 Negative Space Rule: Balanced composition leaving unobstructed space for headline readability."
    ),
    "background": (
        "- Generation Mode: BACKGROUND (Ambient Fluid Texture & Minimalist Hero Canvas).\n"
        "- Minimalist abstract fluid background, ambient depth of field, caustics light refraction, smooth volumetric waves, zero central clutter."
    ),
}

_SYSTEM_PROMPT_TEMPLATE = """You are a World-Class Art Director at a top creative advertising agency (Apple, Nike, Porsche level).

CRITICAL TASK:
You will receive the FULL PARSED TEXT of a social media post or article. You MUST analyze the ENTIRE text payload from start to finish.

STEP-BY-STEP PROCESS:
1. READ THE ENTIRE PARSED TEXT: Understand the full story, core product/service, central topic, and key message (NOT just the first sentence).
2. EXTRACT PHYSICAL SUBJECT MATTER: Identify the exact real-world subject (e.g., if coffee -> premium espresso cup with crema and dark roast beans; if real estate -> glass architecture; if tickets/sale/event -> glowing concert stage, golden VIP passes, dynamic illuminated amphitheater; if tech/AI -> brushed titanium hardware or sleek holographic terminal). NO generic abstract shapes or meaningless floating blobs.
3. WRITE A HIGH-END IMAGE PROMPT (in English):
   - Style: Commercial editorial photography or hyper-realistic 3D Octane render.
   - Layout: 70/30 Negative Space rule (70% clean moody background #0D0E11 for text/logo overlay).
   - Lighting: Cinematic studio rim light, volumetric softbox diffusion.
   {mode_instruction}
   {brandbook_instruction}
   - Visual Style Direction: {visual_style}
   - Tone of Voice: {tone_of_voice}
   - Ending Suffix (MANDATORY): Always append "{no_text_suffix}"

LANGUAGE REQUIREMENTS:
- Selected Locale: {locale} ({locale_name})
- Generate `headline` (3-6 words) and `post_text` (engaging summary of the full post with hashtags and CTA) STRICTLY in {locale_name}.

RETURN ONLY RAW JSON (no markdown, no backticks):
{{
  "headline": "Short punchy summary (3-6 words in {locale_name})",
  "post_text": "Adapted engaging text summarizing the entire post with CTA and hashtags in {locale_name}",
  "image_prompt": "Your masterwork English image prompt (150-250 words) based on the full parsed text ending with {no_text_suffix}"
}}"""

_LOCALE_NAMES = {"kk": "Kazakh", "ru": "Russian", "en": "English"}

MOCKUP_SCENE_PROMPTS: dict[str, str] = {
    "billboard": (
        "A high-end outdoor billboard at night in Shibuya Tokyo, subtle neon reflections, wet pavement, "
        "cinematic lighting, the central billboard display is pure flat green screen #00FF00 with sharp rectangular borders. "
        "8k resolution, photorealistic commercial photography "
        "--no text, letters, clutter, noise, people"
    ),
    "poster_frame": (
        "Minimalist concrete gallery wall with a black thin modern frame hanging, soft natural directional sunlight and gentle shadows, "
        "inside the frame is a pure flat monochrome green screen #00FF00 with clean straight edges. "
        "8k resolution, architectural interior photography "
        "--no text, letters, clutter, noise, people"
    ),
    "phone": (
        "A sleek bezel-less smartphone mockup resting on a luxury dark slate desk, subtle studio rim lighting, "
        "blurred modern architectural background, the phone screen displays a pure flat monochrome green #00FF00. "
        "8k resolution, commercial product photography "
        "--no text, letters, clutter, noise, people"
    ),
}


class GrokResponse:
    __slots__ = ("headline", "post_text", "image_prompt", "raw")

    def __init__(self, headline: str, post_text: str, image_prompt: str, raw: dict) -> None:
        self.headline = headline
        self.post_text = post_text
        self.image_prompt = image_prompt
        self.raw = raw


def build_grok_system_prompt(
    generation_mode: str,
    visual_style: str,
    tone_of_voice: str,
    brandbook: Optional[Brandbook],
    locale: str = "en",
) -> str:
    mode_instruction = _MODE_INSTRUCTIONS.get(generation_mode, _MODE_INSTRUCTIONS["poster" if generation_mode == "poster" else "post"])

    if brandbook is not None:
        brandbook_instruction = (
            f"- Brand Name: {brandbook.name}\n"
            f"- Primary Brand Color: {brandbook.primary_color} (dominant aesthetic color)\n"
            f"- Secondary Accent Color: {brandbook.secondary_color} (accent highlights and contrast)\n"
            f"- Background Tone: {brandbook.background_color}\n"
            f"- Typography Direction: {brandbook.font_header} ({getattr(brandbook, 'font_family', 'Modern Sans')})"
        )
    else:
        brandbook_instruction = (
            "- Brand Identity: Ultra-clean minimalist commercial palette "
            "with #CC5500 warm amber and #ADD8E6 electric blue highlights against deep cinematic neutral tones (#0D0E11)."
        )

    locale_name = _LOCALE_NAMES.get(locale, "English")

    return _SYSTEM_PROMPT_TEMPLATE.format(
        mode_instruction=mode_instruction,
        brandbook_instruction=brandbook_instruction,
        visual_style=visual_style,
        tone_of_voice=tone_of_voice,
        locale=locale,
        locale_name=locale_name,
        no_text_suffix=_NO_TEXT_SUFFIX,
    )


def _build_user_message(input_content: str, generation_mode: str) -> str:
    return (
        f"FULL PARSED POST / SOURCE CONTENT:\n{input_content.strip()}\n\n"
        f"TARGET GENERATION MODE: {generation_mode}\n\n"
        "Analyze the entire text payload above and generate the advertising creative JSON now."
    )


def _parse_grok_json(raw_content: str, fallback_title: str) -> dict:
    content = raw_content.strip()
    if content.startswith("```"):
        lines = content.splitlines()
        content = "\n".join(
            line for line in lines if not line.strip().startswith("```")
        ).strip()
    if not content.startswith("{"):
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            content = match.group(0)
    try:
        return json.loads(content)
    except Exception:
        first_line = fallback_title.split("\n", 1)[0].strip() if fallback_title else "Special Launch"
        return {
            "headline": first_line if first_line else "Special Launch",
            "post_text": content if content else fallback_title.strip(),
            "image_prompt": content if len(content) > 40 else f"A monumental 3D commercial creative visual representing {first_line}, 70% dark negative space #0D0E11, cinematic volumetric lighting, 85mm lens f/1.4, brushed titanium and frosted glass {_NO_TEXT_SUFFIX}",
        }


def _ensure_no_text_suffix(prompt: str) -> str:
    cleaned = prompt.strip()
    if _NO_TEXT_SUFFIX not in cleaned:
        cleaned = f"{cleaned.rstrip('.')} {_NO_TEXT_SUFFIX}"
    return cleaned


def get_mockup_scene_prompt(scene_context: str) -> str:
    key = scene_context.lower().strip()
    return MOCKUP_SCENE_PROMPTS.get(key, MOCKUP_SCENE_PROMPTS["poster_frame"])


async def call_grok(
    input_content: str,
    generation_mode: str,
    visual_style: str,
    tone_of_voice: str,
    brandbook: Optional[Brandbook] = None,
    locale: str = "en",
) -> GrokResponse:
    settings = get_settings()

    system_prompt = build_grok_system_prompt(
        generation_mode=generation_mode,
        visual_style=visual_style,
        tone_of_voice=tone_of_voice,
        locale=locale,
        brandbook=brandbook,
    )
    user_message = _build_user_message(input_content, generation_mode)

    payload = {
        "model": settings.groq_model,
        "temperature": 0.65,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    }

    headers = {
        "Authorization": f"Bearer {settings.groq_api_key}",
        "Content-Type": "application/json",
    }

    logger.info(
        "GROK SEND mode=%s locale=%s style=%s tone=%s text_chars=%d brandbook=%s",
        generation_mode, locale, visual_style, tone_of_voice,
        len(input_content),
        brandbook.name if brandbook else "none",
    )

    try:
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(settings.groq_api_url, headers=headers, json=payload)
            response.raise_for_status()
        raw_content: str = response.json()["choices"][0]["message"]["content"]
    except Exception as err:
        logger.warning("GROK API CALL FAILED: %s. Using advertising fallback prompt.", err)
        raw_content = ""

    parsed = _parse_grok_json(raw_content, fallback_title=input_content)
    raw_prompt = str(parsed.get("image_prompt", ""))
    sanitized_prompt = _ensure_no_text_suffix(raw_prompt)

    result = GrokResponse(
        headline=str(parsed.get("headline", "")).strip(),
        post_text=str(parsed.get("post_text", "")).strip(),
        image_prompt=sanitized_prompt,
        raw=parsed,
    )

    logger.info(
        "GROK DONE headline=%r image_prompt_chars=%d",
        result.headline, len(result.image_prompt),
    )
    return result
