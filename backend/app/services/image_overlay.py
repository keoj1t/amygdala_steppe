from __future__ import annotations

import io
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

import httpx
import qrcode
from PIL import Image, ImageDraw, ImageFont

from app.models.brandbook import Brandbook

FONT_MAP: dict[str, str] = {
    "Inter": "assets/fonts/Inter-Bold.ttf",
    "Montserrat": "assets/fonts/Montserrat-Bold.ttf",
    "Roboto": "assets/fonts/Roboto-Bold.ttf",
    "Playfair Display": "assets/fonts/PlayfairDisplay-Bold.ttf",
    "Oswald": "assets/fonts/Oswald-Bold.ttf",
}


def _font_path(font_name: str | None) -> str | None:
    backend_root = Path(__file__).resolve().parents[2]
    fonts_dir = backend_root / "assets" / "fonts"
    fonts_dir.mkdir(parents=True, exist_ok=True)

    if font_name:
        for key, rel_path in FONT_MAP.items():
            if key.lower() in font_name.lower() or font_name.lower() in key.lower():
                cand = backend_root / rel_path
                if cand.exists():
                    return str(cand)

        normalized = font_name.lower().replace(" ", "").replace("-", "")
        for path in fonts_dir.glob("*.*"):
            if normalized in path.stem.lower().replace("-", ""):
                return str(path)

    noto = fonts_dir / "NotoSans-Bold.ttf"
    if noto.exists():
        return str(noto)

    for fallback_name in ["Roboto-Bold.ttf", "Montserrat-Bold.ttf", "Inter-Bold.ttf"]:
        fb = fonts_dir / fallback_name
        if fb.exists():
            return str(fb)

    return None


def _font(brandbook: Brandbook | None, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    font_name = getattr(brandbook, "font_family", "Inter") if brandbook else "Inter"
    path = _font_path(font_name)
    if path:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()


async def _load_logo(logo_url: str | None, upload_dir: str) -> Image.Image | None:
    if not logo_url:
        return None
    try:
        parsed = urlparse(logo_url)
        if parsed.scheme in {"http", "https"}:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(logo_url)
                response.raise_for_status()
                return Image.open(io.BytesIO(response.content)).convert("RGBA")

        rel_path = parsed.path.removeprefix("/static/uploads/").lstrip("/")
        local_path = Path(upload_dir) / rel_path
        if local_path.exists():
            return Image.open(local_path).convert("RGBA")
    except Exception:
        pass
    return None


def _parse_hex_color(hex_str: str | None, default: tuple[int, int, int]) -> tuple[int, int, int]:
    if not hex_str:
        return default
    cleaned = hex_str.strip().lstrip("#")
    if len(cleaned) == 6:
        try:
            return tuple(int(cleaned[i:i + 2], 16) for i in (0, 2, 4))
        except ValueError:
            pass
    return default


def _wrap_text(text: str, font: ImageFont.ImageFont | ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
    words = text.split()
    if not words:
        return []
    lines: list[str] = []
    current_line: list[str] = []
    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if (bbox[2] - bbox[0]) <= max_width or not current_line:
            current_line.append(word)
        else:
            lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))
    return lines[:3]


def generate_qr_code_image(
    url: str,
    size: int = 130,
    padding: int = 8,
    radius: int = 12,
) -> Image.Image:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=1,
    )
    qr.add_data(url)
    qr.make(fit=True)
    raw_qr = qr.make_image(fill_color="black", back_color="white").convert("RGBA")

    inner_size = size - (padding * 2)
    resized_qr = raw_qr.resize((inner_size, inner_size), Image.Resampling.LANCZOS)

    badge = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(badge)
    draw.rounded_rectangle(
        (0, 0, size, size),
        radius=radius,
        fill=(255, 255, 255, 245),
        outline=(200, 200, 200, 180),
        width=1,
    )
    badge.alpha_composite(resized_qr, (padding, padding))
    return badge


async def apply_poster_overlay(
    image_bytes: bytes,
    brandbook: Brandbook | None,
    headline: str,
    upload_dir: str,
    source_url: str | None = None,
) -> bytes:
    canvas = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    width, height = canvas.size
    min_dim = min(width, height)
    padding = max(24, int(min_dim * 0.045))
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")

    logo_placed = False
    if brandbook and brandbook.logo_url:
        logo = await _load_logo(brandbook.logo_url, upload_dir)
        if logo is not None:
            max_logo_w = int(width * 0.22)
            max_logo_h = int(height * 0.09)
            logo.thumbnail((max_logo_w, max_logo_h), Image.Resampling.LANCZOS)
            logo_x = width - padding - logo.width
            logo_y = padding
            overlay.alpha_composite(logo, (logo_x, logo_y))
            logo_placed = True

    plate_height = 0
    plate_top_y = height - padding

    if headline and headline.strip():
        bg_rgb = _parse_hex_color(brandbook.background_color if brandbook else None, (15, 15, 20))
        fg_rgb = _parse_hex_color(brandbook.text_color if brandbook else None, (255, 255, 255))

        font_size = max(26, int(min_dim * 0.048))
        font = _font(brandbook, font_size)

        max_text_w = width - (padding * 4)
        lines = _wrap_text(headline.strip(), font, max_text_w, draw)

        line_height = int(font_size * 1.25)
        text_total_h = len(lines) * line_height
        plate_height = text_total_h + (padding * 2)
        plate_top_y = height - padding - plate_height

        draw.rounded_rectangle(
            (padding, plate_top_y, width - padding, height - padding),
            radius=max(14, padding // 2),
            fill=(*bg_rgb, 225),
            outline=(255, 255, 255, 40),
            width=1,
        )

        for i, line in enumerate(lines):
            line_y = plate_top_y + padding + (i * line_height)
            draw.text(
                (padding * 2, line_y),
                line,
                font=font,
                fill=(*fg_rgb, 255),
            )

    target_url = source_url.strip() if source_url else None
    if target_url and (target_url.startswith("http://") or target_url.startswith("https://")):
        qr_size = max(100, min(140, int(min_dim * 0.13)))
        qr_badge = generate_qr_code_image(target_url, size=qr_size, padding=6, radius=10)

        if logo_placed:
            qr_x = padding
            qr_y = padding
        else:
            qr_x = width - padding - qr_size
            qr_y = padding

        overlay.alpha_composite(qr_badge, (qr_x, qr_y))

    combined = Image.alpha_composite(canvas, overlay)
    output = io.BytesIO()
    combined.convert("RGB").save(output, format="JPEG", quality=95, optimize=True)
    return output.getvalue()