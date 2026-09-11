from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UuidPrimaryKeyMixin


class Brandbook(Base, UuidPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "brandbooks"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    primary_color: Mapped[str] = mapped_column(String(7), nullable=False)
    secondary_color: Mapped[str] = mapped_column(String(7), nullable=False)
    text_color: Mapped[str] = mapped_column(String(7), nullable=False)
    background_color: Mapped[str] = mapped_column(String(7), nullable=False)
    font_header: Mapped[str] = mapped_column(String(120), nullable=False)
    font_body: Mapped[str] = mapped_column(String(120), nullable=False)
    font_family: Mapped[str] = mapped_column(String(120), nullable=False, default="Inter", server_default="Inter")
    logo_url: Mapped[str | None] = mapped_column(String(500))

    user = relationship("User", back_populates="brandbooks")
    projects = relationship("Project", back_populates="brandbook")
