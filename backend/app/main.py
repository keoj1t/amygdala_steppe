from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine


settings = get_settings()


async def create_local_schema() -> None:
    if not settings.database_url.startswith("sqlite"):
        return
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


app = FastAPI(title=settings.app_name, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.backend_cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
app.mount("/static/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")
mockups_dir = Path(__file__).resolve().parents[2] / "mockups"
if mockups_dir.exists():
    app.mount("/static/mockups", StaticFiles(directory=mockups_dir), name="mockups")
app.include_router(api_router)


@app.on_event("startup")
async def on_startup() -> None:
    await create_local_schema()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
