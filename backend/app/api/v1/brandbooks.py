from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.db.session import get_db
from app.models.brandbook import Brandbook
from app.models.user import User
from app.schemas.brandbook import BrandbookCreate, BrandbookRead, BrandbookUpdate


router = APIRouter(prefix="/brandbooks", tags=["brandbooks"])


def absolute_media_url(request: Request, value: str | None) -> str | None:
    if not value or value.startswith(("http://", "https://", "data:")):
        return value
    return str(request.base_url).rstrip("/") + "/" + value.lstrip("/")


async def save_logo(file: UploadFile | None) -> str | None:
    if file is None:
        return None
    content_type = file.content_type or ""
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Logo must be an image")
    suffix = Path(file.filename or "logo").suffix.lower() or ".png"
    upload_dir = Path(get_settings().upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4()}{suffix}"
    target = upload_dir / filename
    data = await file.read()
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Logo is too large")
    target.write_bytes(data)
    return f"/static/uploads/{filename}"


@router.get("", response_model=list[BrandbookRead])
async def list_brandbooks(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[BrandbookRead]:
    result = await db.execute(
        select(Brandbook).where(Brandbook.user_id == current_user.id).order_by(Brandbook.created_at.desc())
    )
    return [
        BrandbookRead.model_validate({**brandbook.__dict__, "logo_url": absolute_media_url(request, brandbook.logo_url)})
        for brandbook in result.scalars().all()
    ]


@router.post("", response_model=BrandbookRead, status_code=status.HTTP_201_CREATED)
async def create_brandbook(
    request: Request,
    name: str = Form(...),
    primary_color: str = Form(...),
    secondary_color: str = Form(...),
    text_color: str = Form(...),
    background_color: str = Form(...),
    font_header: str = Form(...),
    font_body: str = Form(...),
    font_family: str = Form("Inter"),
    logo: UploadFile | None = File(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BrandbookRead:
    validated = BrandbookCreate.model_validate(
        {
            "name": name,
            "primary_color": primary_color,
            "secondary_color": secondary_color,
            "text_color": text_color,
            "background_color": background_color,
            "font_header": font_header,
            "font_body": font_body,
            "font_family": font_family,
        }
    )
    logo_url = await save_logo(logo)
    brandbook = Brandbook(
        user_id=current_user.id,
        name=validated.name,
        primary_color=validated.primary_color,
        secondary_color=validated.secondary_color,
        text_color=validated.text_color,
        background_color=validated.background_color,
        font_header=validated.font_header,
        font_body=validated.font_body,
        font_family=validated.font_family,
        logo_url=logo_url,
    )
    db.add(brandbook)
    await db.commit()
    await db.refresh(brandbook)
    return BrandbookRead.model_validate({**brandbook.__dict__, "logo_url": absolute_media_url(request, brandbook.logo_url)})


@router.put("/{brandbook_id}", response_model=BrandbookRead)
async def update_brandbook(
    brandbook_id: UUID,
    request: Request,
    payload: BrandbookUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Brandbook:
    brandbook = await db.scalar(
        select(Brandbook).where(Brandbook.id == brandbook_id, Brandbook.user_id == current_user.id)
    )
    if brandbook is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brandbook not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(brandbook, key, value)
    await db.commit()
    await db.refresh(brandbook)
    return BrandbookRead.model_validate({**brandbook.__dict__, "logo_url": absolute_media_url(request, brandbook.logo_url)})


@router.delete("/{brandbook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_brandbook(
    brandbook_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    brandbook = await db.scalar(
        select(Brandbook).where(Brandbook.id == brandbook_id, Brandbook.user_id == current_user.id)
    )
    if brandbook is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brandbook not found")
    await db.delete(brandbook)
    await db.commit()
