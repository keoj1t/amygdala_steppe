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
        "Generation Mode: POSTER (Monumental 3D Commercial Billboard & Swiss Design Aesthetic).\n"
        "- Zero Clutter & Minimalism: Exactly ONE central monumental hero object or iconic architectural sculpture (Focal Point). "
        "Strictly prohibit messy patterns, random clutter, or chaotic decorative elements.\n"
        "- 70/30 Negative Space Rule: 70% of the canvas MUST be clean, deep, aesthetic negative space (deep dark gradient #0D0E11, "
        "cinematic volumetric atmosphere, matte surface, soft ambient shadows) specifically reserved for bold typography and logo overlay.\n"
        "- Lighting & Materials: Cinematic volumetric studio lighting, crisp rim light, raytraced reflections, Octane render quality. "
        "Materials: Translucent frosted glass, brushed titanium, liquid chrome, glossy acrylic, matte carbon fiber."
    ),
    "post": (
        "Generation Mode: POST (Editorial Advertising & Luxury Social Media Art).\n"
        "- Zero Clutter & Minimalism: Single mesmerizing focal object or luxury fashion editorial composition. "
        "Magazine-cover visual impact with deep focal depth (85mm f/1.4 lens) and creamy bokeh background.\n"
        "- 70/30 Negative Space Rule: Balanced composition leaving unobstructed space for headline readability.\n"
        "- Lighting & Materials: Volumetric directional lighting, soft rim light, raytraced reflections, tactile luxury textures."
    ),
    "background": (
        "Generation Mode: BACKGROUND (Ambient Fluid Texture & Minimalist Hero Canvas).\n"
        "- Visual Focus: Minimalist abstract fluid background, ambient depth of field, caustics light refraction, smooth volumetric waves. "
        "No central focal subjects, no characters, zero clutter."
    ),
}

_SYSTEM_PROMPT_TEMPLATE = """You are an elite Executive Creative Director and Lead Prompt Engineer at a world-renowned design agency (Apple, Nike, Cannes Lions Grand Prix aesthetics).

Your mission is to transform the source brief into an ultra-premium, production-grade English prompt for the FLUX image generation model, alongside a high-converting headline and social media caption.

### GRAPHIC DESIGN PRINCIPLES:
1. **Zero Clutter & Single Hero Focus**: Exactly ONE monumental focal element. Forbid chaotic details.
2. **70/30 Negative Space Rule**: 70% clean, dark, atmospheric negative space (dark gradient #0D0E11, soft studio shadows) reserved for typography overlay.
3. **Lighting & Materials**: Cinematic volumetric lighting, rim light, raytracing, Octane render. Translucent frosted glass, brushed titanium, liquid chrome, glossy acrylic.
4. **Style Qualifiers**: 8k resolution, award-winning commercial advertising photography, photorealistic masterwork.
5. **Mode Specifics**:
{mode_instruction}

### BRAND IDENTITY:
{brandbook_instruction}

### STYLE & TONE:
- Visual Style: {visual_style}
- Tone of Voice: {tone_of_voice}

### LANGUAGE REQUIREMENTS:
- Selected Locale: {locale} ({locale_name})
- Generate `headline` (3-6 words) and `post_text` (2-4 sentences with 5-7 relevant hashtags) STRICTLY in {locale_name}.

### CRITICAL RULES:
- The `image_prompt` MUST be in English only.
- The `image_prompt` MUST NEVER request text, letters, slogans, or watermarks.
- The `image_prompt` MUST ALWAYS conclude with: "{no_text_suffix}"

### OUTPUT FORMAT:
Output ONLY a raw JSON object (no markdown, no backticks):
{{
  "headline": "Short impactful title (3-6 words in {locale_name})",
  "post_text": "Engaging caption with hashtags (2-4 sentences in {locale_name})",
  "image_prompt": "Detailed English prompt (150-250 words) ending with {no_text_suffix}"
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
            "No specific brandbook selected. Use an ultra-clean minimalist commercial palette "
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
        f"SOURCE CONTENT / BRIEF:\n{input_content}\n\n"
        f"TARGET GENERATION MODE: {generation_mode}\n\n"
        "Generate the advertising creative JSON now."
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
        return {
            "headline": fallback_title[:60] if fallback_title else "Brand New Vision",
            "post_text": content[:280] if content else "Discover the future with our latest launch.",
            "image_prompt": content if len(content) > 40 else f"A monumental 3D commercial creative visual for {fallback_title}, 70% dark negative space #0D0E11, cinematic volumetric lighting, 85mm lens f/1.4, brushed titanium and frosted glass {_NO_TEXT_SUFFIX}",
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
        "GROK SEND mode=%s locale=%s style=%s tone=%s brandbook=%s",
        generation_mode, locale, visual_style, tone_of_voice,
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
