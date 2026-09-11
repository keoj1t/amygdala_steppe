import html
import re
from urllib.parse import urlparse
import httpx

async def parse_telegram(url: str) -> tuple[str, str, str]:
    parsed = urlparse(url)
    clean_url = f"https://t.me/{parsed.path.strip('/')}"
    if clean_url.startswith("https://t.me/s/"):
        clean_url = clean_url.replace("https://t.me/s/", "https://t.me/")

    headers = {"User-Agent": "Mozilla/5.0 (compatible; AmygdalaContentFactory/1.0)"}
    async with httpx.AsyncClient(follow_redirects=True, timeout=20) as client:
        response = await client.get(clean_url, headers=headers)
        response.raise_for_status()

    match = re.search(
        r'<meta\s+(?:[^>]*?\s)?(?:property|name)=["\'](?:og:)?description["\'][^>]*?content=["\']([^"\']*)["\'][^>]*>',
        response.text,
        re.IGNORECASE,
    )
    if not match:
        match = re.search(
            r'<meta\s+(?:[^>]*?\s)?content=["\']([^"\']*)["\'][^>]*?(?:property|name)=["\'](?:og:)?description["\'][^>]*>',
            response.text,
            re.IGNORECASE,
        )

    text = ""
    if match:
        text = html.unescape(match.group(1)).strip()

    if not text or len(text) < 50:
        embed_url = f"{clean_url}?embed=1"
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=20) as embed_client:
                embed_response = await embed_client.get(embed_url, headers=headers)
                widget_match = re.search(r'<div class="tgme_widget_message_text[^>]*>(.*?)</div>', embed_response.text, re.DOTALL)
                if widget_match:
                    embed_text = re.sub(r"<br\s*/?>", "\n", widget_match.group(1))
                    embed_text = re.sub(r"<[^>]+>", " ", embed_text).strip()
                    if len(embed_text) > len(text):
                        text = embed_text
        except Exception:
            pass

    if not text:
        text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", response.text)).strip()

    if not text or text == "Founder of Telegram.":
        raise ValueError("Не удалось извлечь текст из Telegram поста.")

    return text.strip(), "telegram", "telegram_parser"
