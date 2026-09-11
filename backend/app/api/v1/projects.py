from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.brandbook import Brandbook
from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate


router = APIRouter(prefix="/projects", tags=["projects"])


def absolute_media_url(request: Request, value: str | None) -> str | None:
    if not value or value.startswith(("http://", "https://", "data:")):
        return value
    return str(request.base_url).rstrip("/") + "/" + value.lstrip("/")


def project_response(project: Project, request: Request) -> ProjectRead:
    data = ProjectRead.model_validate(project).model_dump()
    if data.get("image_url"):
        data["image_url"] = absolute_media_url(request, data["image_url"])
    if data.get("brandbook") and data["brandbook"].get("logo_url"):
        data["brandbook"]["logo_url"] = absolute_media_url(request, data["brandbook"]["logo_url"])
    return ProjectRead.model_validate(data)


async def ensure_brandbook_access(
    brandbook_id: UUID | None,
    current_user: User,
    db: AsyncSession,
) -> None:
    if brandbook_id is None:
        return
    brandbook = await db.scalar(
        select(Brandbook).where(Brandbook.id == brandbook_id, Brandbook.user_id == current_user.id)
    )
    if brandbook is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid brandbook")


@router.get("", response_model=list[ProjectRead])
async def list_projects(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ProjectRead]:
    result = await db.execute(
        select(Project).options(joinedload(Project.brandbook)).where(Project.user_id == current_user.id).order_by(Project.updated_at.desc())
    )
    return [project_response(project, request) for project in result.scalars().unique().all()]


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    request: Request,
    payload: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectRead:
    await ensure_brandbook_access(payload.brandbook_id, current_user, db)
    project = Project(user_id=current_user.id, **payload.model_dump())
    db.add(project)
    await db.commit()
    project = await db.scalar(select(Project).options(joinedload(Project.brandbook)).where(Project.id == project.id))
    return project_response(project, request)


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectRead:
    project = await db.scalar(select(Project).options(joinedload(Project.brandbook)).where(Project.id == project_id, Project.user_id == current_user.id))
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project_response(project, request)


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: UUID,
    request: Request,
    payload: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectRead:
    project = await db.scalar(select(Project).options(joinedload(Project.brandbook)).where(Project.id == project_id, Project.user_id == current_user.id))
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    await ensure_brandbook_access(payload.brandbook_id, current_user, db)
    for field, value in payload.model_dump().items():
        setattr(project, field, value)
    await db.commit()
    project = await db.scalar(select(Project).options(joinedload(Project.brandbook)).where(Project.id == project.id))
    return project_response(project, request)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    project = await db.scalar(select(Project).where(Project.id == project_id, Project.user_id == current_user.id))
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    await db.delete(project)
    await db.commit()
