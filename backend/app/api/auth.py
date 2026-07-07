from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_client_ip, get_current_user
from app.exceptions import AuthenticationError, ConflictError
from app.models.enums import AuditLevel
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserProfile,
)
from app.security import PasswordHasher, create_access_token
from app.services.audit_service import audit_service
from datetime import datetime, timezone

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserProfile, status_code=201)
async def register(payload: RegisterRequest, request: Request, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none() is not None:
        raise ConflictError("An account with this email already exists")

    user = User(
        email=payload.email,
        hashed_password=PasswordHasher.hash(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    await db.flush()
    await audit_service.log(
        db,
        action="user.register",
        user_id=user.id,
        resource_type="user",
        resource_id=user.id,
        ip_address=get_client_ip(request),
        commit=False,
    )
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if user is None or not PasswordHasher.verify(payload.password, user.hashed_password):
        raise AuthenticationError("Incorrect email or password")
    if not user.is_active:
        raise AuthenticationError("This account has been disabled")

    user.last_login_at = datetime.now(timezone.utc)
    await audit_service.log(
        db,
        action="user.login",
        user_id=user.id,
        resource_type="user",
        resource_id=user.id,
        ip_address=get_client_ip(request),
        commit=False,
    )
    await db.commit()

    token = create_access_token(user.id, user.role.value)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserProfile)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserProfile)
async def update_me(
    payload: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if payload.full_name:
        current_user.full_name = payload.full_name

    if payload.new_password:
        if not payload.current_password or not PasswordHasher.verify(
            payload.current_password, current_user.hashed_password
        ):
            raise AuthenticationError("Current password is incorrect")
        current_user.hashed_password = PasswordHasher.hash(payload.new_password)

    await db.commit()
    await db.refresh(current_user)
    return current_user
