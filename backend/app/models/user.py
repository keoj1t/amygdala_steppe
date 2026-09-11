from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UuidPrimaryKeyMixin


class User(Base, UuidPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    brandbooks = relationship("Brandbook", back_populates="user", cascade="all, delete-orphan")
    verifications = relationship("EmailVerification", back_populates="user", cascade="all, delete-orphan")
