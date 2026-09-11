from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UuidPrimaryKeyMixin


class Project(Base, UuidPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "projects"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    brandbook_id: Mapped[UUID | None] = mapped_column(ForeignKey("brandbooks.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(1000))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = relationship("User", back_populates="projects")
    brandbook = relationship("Brandbook", back_populates="projects")
