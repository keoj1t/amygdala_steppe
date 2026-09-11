from __future__ import annotations

import io
import logging
from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageChops, ImageDraw, ImageOps

logger = logging.getLogger("amygdala.mockups")

MOCKUP_TEMPLATES: dict[str, dict] = {
    "poster": {
        "file": "poster.jpg",
        "aliases": ["poster", "billboard", "billboard_mockup.png", "poster_frame.png", "frame"],
        "bbox": (1820, 680, 4196, 3336),
        "corner_radius": 12,
    },
    "instagram": {
        "file": "instagram.jpg",
        "aliases": ["instagram", "post", "phone", "phone_mockup.png", "mobile"],
        "bbox": (950, 320, 2050, 1680),
        "corner_radius": 34,
    },
    "linkedin": {
        "file": "linkedin.png",
        "aliases": ["linkedin", "web", "desktop", "background"],
        "bbox": (16, 110, 458, 395),
        "corner_radius": 6,
    },
}


def _get_mockup_dir() -> Path:
    backend_root = Path(__file__).resolve().parents[2]
    candidate = backend_root.parent / "mockups"
    if candidate.exists():
        return candidate
    return backend_root / "mockups"


def _resolve_template_key(mode_or_name: str) -> str:
    cleaned = mode_or_name.lower().strip()
    for key, spec in MOCKUP_TEMPLATES.items():
        if cleaned == key or cleaned in spec["aliases"] or cleaned == spec["file"].lower():
            return key
    if "post" in cleaned or "phone" in cleaned or "insta" in cleaned:
        return "instagram"
    if "poster" in cleaned or "billboard" in cleaned or "frame" in cleaned:
        return "poster"
    return "poster"


def detect_chroma_key_bbox(scene_img: Image.Image) -> tuple[int, int, int, int] | None:
    rgb = scene_img.convert("RGB")
    r, g, b = rgb.split()
    mask_g = Image.eval(g, lambda v: 255 if v > 140 else 0)
    mask_r = Image.eval(r, lambda v: 255 if v < 110 else 0)
    mask_b = Image.eval(b, lambda v: 255 if v < 110 else 0)
    green_mask = ImageChops.multiply(ImageChops.multiply(mask_g, mask_r), mask_b)
    bbox = green_mask.getbbox()
    if bbox:
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        if w > 40 and h > 40:
            return bbox
    return None


def apply_glass_and_shadow_overlay(poster_fitted: Image.Image, radius: int = 0) -> Image.Image:
    w, h = poster_fitted.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    draw.polygon(
        [(0, 0), (int(w * 0.65), 0), (0, int(h * 0.65))],
        fill=(255, 255, 255, 26),
    )

    border_w = max(2, int(min(w, h) * 0.008))
    if radius > 0:
        draw.rounded_rectangle((0, 0, w, h), radius=radius, outline=(0, 0, 0, 60), width=border_w)
    else:
        draw.rectangle((0, 0, w, h), outline=(0, 0, 0, 60), width=border_w)

    return Image.alpha_composite(poster_fitted.convert("RGBA"), overlay)


def _create_rounded_mask(size: tuple[int, int], radius: int) -> Image.Image:
    scale = 4
    w, h = size[0] * scale, size[1] * scale
    r = radius * scale
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, w, h), radius=r, fill=255)
    return mask.resize(size, Image.Resampling.LANCZOS)


def composite_chroma_key_mockup(
    scene_bytes: bytes,
    poster_bytes: bytes,
    fallback_key: str = "poster",
    output_dir: Path | str | None = None,
) -> tuple[bytes, str, str]:
    scene_img = Image.open(io.BytesIO(scene_bytes)).convert("RGBA")
    poster_img = Image.open(io.BytesIO(poster_bytes)).convert("RGBA")

    detected_bbox = detect_chroma_key_bbox(scene_img)
    if not detected_bbox:
        spec = MOCKUP_TEMPLATES.get(fallback_key, MOCKUP_TEMPLATES["poster"])
        detected_bbox = spec["bbox"]

    x1, y1, x2, y2 = detected_bbox
    slot_w = x2 - x1
    slot_h = y2 - y1

    fitted_poster = ImageOps.fit(
        poster_img,
        (slot_w, slot_h),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    )

    enhanced_poster = apply_glass_and_shadow_overlay(fitted_poster, radius=8)

    composite = scene_img.copy()
    composite.paste(enhanced_poster, (x1, y1), mask=enhanced_poster)

    if composite.width > 2560:
        ratio = 2560 / composite.width
        target_size = (2560, int(composite.height * ratio))
        composite = composite.resize(target_size, Image.Resampling.LANCZOS)

    output_buffer = io.BytesIO()
    composite.convert("RGB").save(output_buffer, format="JPEG", quality=94, optimize=True)
    result_bytes = output_buffer.getvalue()

    filename = f"mockup_dynamic_{uuid4().hex}_{fallback_key}.jpg"
    public_url = f"/static/uploads/generated/{filename}"

    if output_dir:
        out_path = Path(output_dir) / filename
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(result_bytes)

    return result_bytes, filename, public_url


def composite_mockup(
    image_bytes: bytes,
    template_name_or_mode: str = "poster",
    output_dir: Path | str | None = None,
) -> tuple[bytes, str, str]:
    template_key = _resolve_template_key(template_name_or_mode)
    spec = MOCKUP_TEMPLATES[template_key]
    mockup_dir = _get_mockup_dir()
    template_path = mockup_dir / spec["file"]

    if not template_path.exists():
        raise FileNotFoundError(f"Mockup template file not found: {template_path}")

    template_img = Image.open(template_path).convert("RGBA")
    source_img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")

    x1, y1, x2, y2 = spec["bbox"]
    slot_w = x2 - x1
    slot_h = y2 - y1
    radius = spec.get("corner_radius", 0)

    fitted_img = ImageOps.fit(
        source_img,
        (slot_w, slot_h),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    )

    enhanced_img = apply_glass_and_shadow_overlay(fitted_img, radius=radius)
    mask = _create_rounded_mask((slot_w, slot_h), radius) if radius > 0 else Image.new("L", (slot_w, slot_h), 255)

    base_layer = Image.new("RGBA", template_img.size, (0, 0, 0, 0))
    base_layer.paste(enhanced_img, (x1, y1), mask=mask)

    has_transparency = (
        template_img.mode == "RGBA" and any(pixel[3] < 255 for pixel in template_img.getdata())
    )

    if has_transparency:
        composite = Image.alpha_composite(base_layer, template_img)
    else:
        template_copy = template_img.copy()
        template_copy.paste(enhanced_img, (x1, y1), mask=mask)
        composite = template_copy

    if composite.width > 2560:
        ratio = 2560 / composite.width
        target_size = (2560, int(composite.height * ratio))
        composite = composite.resize(target_size, Image.Resampling.LANCZOS)

    output_buffer = io.BytesIO()
    composite.convert("RGB").save(output_buffer, format="JPEG", quality=94, optimize=True)
    result_bytes = output_buffer.getvalue()

    filename = f"mockup_{uuid4().hex}_{template_key}.jpg"
    public_url = f"/static/uploads/generated/{filename}"

    if output_dir:
        out_path = Path(output_dir) / filename
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(result_bytes)

    return result_bytes, filename, public_url


def generate_all_mockup_urls(
    image_bytes: bytes,
    output_dir: Path | str,
) -> dict[str, str]:
    results: dict[str, str] = {}
    for key in MOCKUP_TEMPLATES:
        try:
            _, _, public_url = composite_mockup(image_bytes, template_name_or_mode=key, output_dir=output_dir)
            results[key] = public_url
        except Exception as err:
            logger.warning("Failed to generate mockup %s: %s", key, err)
    return results
