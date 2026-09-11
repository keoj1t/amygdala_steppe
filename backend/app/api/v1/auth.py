import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.email import EmailClient
from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.db.session import get_db
from app.models.email_verification import EmailVerification
from app.models.user import User
from app.schemas.auth import LoginRequest, MessageResponse, RegisterRequest, TokenPair, VerifyEmailRequest
from app.schemas.user import UserRead


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> MessageResponse:
    normalized_email = payload.email.lower()
    existing_user = await db.scalar(select(User).where(User.email == normalized_email))
    if existing_user and existing_user.is_verified:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = existing_user or User(email=normalized_email, password_hash=hash_password(payload.password))
    if existing_user:
        user.password_hash = hash_password(payload.password)
    db.add(user)
    await db.flush()
    code = f"{secrets.randbelow(1_000_000):06d}"
    verification = EmailVerification(
        user_id=user.id,
        code_hash=hash_password(code),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=get_settings().otp_expire_minutes),
    )
    db.add(verification)
    await db.commit()
    await EmailClient().send_verification_code(normalized_email, code)
    return MessageResponse(message="Verification code sent")


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    payload: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    normalized_email = payload.email.lower()
    user = await db.scalar(select(User).where(User.email == normalized_email))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    result = await db.execute(
        select(EmailVerification)
        .where(EmailVerification.user_id == user.id, EmailVerification.consumed_at.is_(None))
        .order_by(EmailVerification.created_at.desc())
    )
    verification = next(
        (item for item in result.scalars().all() if verify_password(payload.code, item.code_hash)),
        None,
    )
    if verification is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired code")
    expires_at = verification.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired code")
    verification.consumed_at = datetime.now(timezone.utc)
    user.is_verified = True
    await db.commit()
    return MessageResponse(message="Email verified")


@router.post("/login", response_model=TokenPair)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenPair:
    normalized_email = payload.email.lower()
    user = await db.scalar(select(User).where(User.email == normalized_email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email is not verified")
    return TokenPair(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        user=UserRead.model_validate(user),
    )


@router.get("/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: dict, db: AsyncSession = Depends(get_db)) -> TokenPair:
    from app.core.security import decode_token
    import jwt as pyjwt

    refresh_token = payload.get("refresh_token", "")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="refresh_token is required")

    try:
        decoded = decode_token(refresh_token)
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")
    except pyjwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if decoded.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    from uuid import UUID
    user_id = UUID(decoded["sub"])
    user = await db.scalar(select(User).where(User.id == user_id))
    if user is None or not user.is_verified:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or not verified")

    return TokenPair(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        user=UserRead.model_validate(user),
    )
