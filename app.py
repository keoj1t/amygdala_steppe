import base64
import json
import os
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from uuid import uuid4

ROOT = Path(__file__).parent
GENERATED = ROOT / "generated"
GENERATED.mkdir(exist_ok=True)
POLLINATIONS_BASE_URL = "https://image.pollinations.ai/prompt"


def get_env(key: str) -> str:
    val = os.getenv(key)
    if val:
        return val
    env_path = ROOT / "backend" / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def enhance_prompt(user_prompt: str) -> str:
    api_key = get_env("GROQ_API_KEY")
    if not api_key:
        return user_prompt

    url = get_env("GROQ_API_URL") or "https://api.groq.com/openai/v1/chat/completions"
    model = get_env("GROQ_MODEL") or "llama-3.1-70b-versatile"

    payload = json.dumps({
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an expert AI image prompt engineer. Your task is to take the user's raw input and turn it into a highly detailed, "
                    "descriptive, and cinematic prompt in English for the FLUX image generation model. "
                    "Include vivid details about the main subject, composition, lighting, "
                    "camera angle, style, and atmosphere. "
                    "Return ONLY the English image prompt, without any conversational filler, explanations, or quotes."
                )
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        "temperature": 0.7
    }).encode()

    request = Request(
        url,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    )
    try:
        with urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode())
            return result["choices"][0]["message"]["content"].strip()
    except Exception:
        return user_prompt


def generate_image(prompt: str) -> str:
    base_url = get_env("POLLINATIONS_BASE_URL") or POLLINATIONS_BASE_URL
    model = get_env("POLLINATIONS_MODEL") or "flux"
    encoded_prompt = urllib.parse.quote(prompt.strip())
    image_url = f"{base_url.rstrip('/')}/{encoded_prompt}?width=1080&height=1080&model={model}&nologo=true"

    request = Request(
        image_url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        },
    )
    try:
        with urlopen(request, timeout=120) as response:
            image_bytes = response.read()
            image_id = uuid4().hex
            file_path = GENERATED / f"{image_id}.jpg"
            file_path.write_bytes(image_bytes)
            return f"/generated/{file_path.name}"
    except (HTTPError, URLError) as error:
        raise RuntimeError(f"Pollinations FLUX error: {error}") from error


class Handler(BaseHTTPRequestHandler):
    def send_json(self, status, value):
        data = json.dumps(value, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if self.path != "/generate":
            self.send_json(404, {"error": "Not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length))
            prompt = str(payload.get("prompt", "")).strip()
            if not prompt:
                raise ValueError("Введите промпт")

            enhanced_prompt = enhance_prompt(prompt)
            self.send_json(200, {"image": generate_image(enhanced_prompt)})

        except (ValueError, RuntimeError, HTTPError, URLError, json.JSONDecodeError) as error:
            self.send_json(400, {"error": str(error)})

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            content = (ROOT / "index.html").read_bytes()
            content_type = "text/html; charset=utf-8"
        elif path.startswith("/generated/"):
            filename = Path(path.removeprefix("/generated/")).name
            file_path = GENERATED / filename
            if not file_path.exists():
                self.send_error(404)
                return
            content = file_path.read_bytes()
            content_type = "image/jpeg"
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    print(f"Откройте http://localhost:{port}")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()