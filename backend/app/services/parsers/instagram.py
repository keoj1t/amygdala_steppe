import asyncio
import re

def _parse_instagram_with_ytdlp(url: str) -> str:
    from yt_dlp import YoutubeDL
    options = {"quiet": True, "extract_flat": True, "skip_download": True}
    with YoutubeDL(options) as downloader:
        info = downloader.extract_info(url, download=False)
    return str(info.get("description") or "").strip()

def _parse_instagram_with_instaloader(url: str) -> str:
    import instaloader
    match = re.search(r"instagram\.com/(?:p|reel)/([^/?]+)", url)
    if not match:
        return ""
    loader = instaloader.Instaloader(quiet=True)
    post = instaloader.Post.from_shortcode(loader.context, match.group(1))
    return str(post.caption or "").strip()

async def parse_instagram(url: str) -> tuple[str, str, str]:
    text = ""
    for parser in (_parse_instagram_with_ytdlp, _parse_instagram_with_instaloader):
        try:
            text = await asyncio.to_thread(parser, url)
            if text:
                break
        except Exception:
            continue
    if not text:
        raise ValueError("Не удалось извлечь текст из ссылки instagram")
    return text.strip(), "instagram", "instagram_parser"
