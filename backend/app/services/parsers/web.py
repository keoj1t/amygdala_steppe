import html
import re
import httpx

async def parse_web(url: str) -> tuple[str, str, str]:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; AmygdalaContentFactory/1.0)"}
    async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
        response = await client.get(url, headers=headers)
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

    if not text:
        text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", response.text)).strip()[:5000]

    if not text:
        raise ValueError("Не удалось извлечь текст из ссылки web")

    return text[:5000], "web", "web_parser"
