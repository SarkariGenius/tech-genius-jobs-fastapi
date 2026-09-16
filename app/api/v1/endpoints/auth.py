from fastapi import APIRouter
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.exceptions import conflict, bad_request, unauthorized, not_found
from app.core.dependencies import CurrentUser, DB
from app.models.user import User, UserRole
from app.models.candidate import CandidateProfile, ExperienceLevel
from app.models.hr import HRProfile
from app.models.company import Company
from app.models.refresh_token import RefreshToken
from app.schemas.auth import (
    StudentRegisterRequest, HRRegisterRequest, LoginRequest,
    RefreshRequest, AuthResponse, UserResponse, MessageResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register/student", response_model=AuthResponse)
def register_student(req: StudentRegisterRequest, db: DB):
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise conflict("EMAIL_EXISTS", "Email already registered")
    user = User(
        email=req.email,
        password_hash=hash_password(req.password),
        full_name=req.full_name,
        phone=req.phone,
        role=UserRole.STUDENT,
    )
    db.add(user)
    db.flush()
    try:
        exp_level = ExperienceLevel(req.experience_level)
    except ValueError:
        exp_level = ExperienceLevel.FRESHER
    candidate = CandidateProfile(
        user_id=user.id,
        current_city=req.current_city,
        experience_level=exp_level,
    )
    db.add(candidate)
    db.commit()
    db.refresh(user)

    access = create_access_token(user.id, {"role": user.role.value})
    refresh = create_refresh_token(user.id)
    _store_refresh_token(db, user.id, refresh)
    return AuthResponse(
        access_token=access,
        refresh_token=refresh,
        token_type="bearer",
        user=UserResponse(id=user.id, email=user.email, role=user.role.value),
    )


@router.post("/register/hr", response_model=AuthResponse)
def register_hr(req: HRRegisterRequest, db: DB):
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise conflict("EMAIL_EXISTS", "Email already registered")
    user = User(
        email=req.email,
        password_hash=hash_password(req.password),
        full_name=req.full_name,
        phone=req.phone,
        role=UserRole.HR,
    )
    db.add(user)
    db.flush()
    company = db.query(Company).filter(Company.name.ilike(req.company_name)).first()
    if not company:
        company = Company(name=req.company_name, city="Indore", location="Indore")
        db.add(company)
        db.flush()
    hr_profile = HRProfile(
        user_id=user.id,
        company_id=company.id,
        designation=req.designation,
    )
    db.add(hr_profile)
    db.commit()
    db.refresh(user)

    access = create_access_token(user.id, {"role": user.role.value})
    refresh = create_refresh_token(user.id)
    _store_refresh_token(db, user.id, refresh)
    return AuthResponse(
        access_token=access,
        refresh_token=refresh,
        token_type="bearer",
        user=UserResponse(id=user.id, email=user.email, role=user.role.value),
    )


@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest, db: DB):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise unauthorized("INVALID_CREDENTIALS", "Invalid email or password")
    if not user.is_active:
        raise unauthorized("ACCOUNT_DISABLED", "Account is disabled")
    access = create_access_token(user.id, {"role": user.role.value})
    refresh = create_refresh_token(user.id)
    _store_refresh_token(db, user.id, refresh)
    return AuthResponse(
        access_token=access,
        refresh_token=refresh,
        token_type="bearer",
        user=UserResponse(id=user.id, email=user.email, role=user.role.value),
    )


@router.post("/refresh", response_model=AuthResponse)
def refresh_token(req: RefreshRequest, db: DB):
    payload = decode_token(req.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise unauthorized("INVALID_REFRESH_TOKEN", "Invalid refresh token")
    user_id = payload.get("sub")
    user = db.get(User, user_id)
    if not user:
        raise unauthorized("USER_NOT_FOUND", "User not found")
    access = create_access_token(user.id, {"role": user.role.value})
    new_refresh = create_refresh_token(user.id)
    _store_refresh_token(db, user.id, new_refresh)
    return AuthResponse(
        access_token=access,
        refresh_token=new_refresh,
        token_type="bearer",
        user=UserResponse(id=user.id, email=user.email, role=user.role.value),
    )


@router.post("/logout", response_model=MessageResponse)
def logout(user: CurrentUser, db: DB):
    db.query(RefreshToken).filter(RefreshToken.user_id == user.id).update({"revoked": True})
    db.commit()
    return MessageResponse(message="Logged out successfully")


@router.get("/me", response_model=UserResponse)
def get_me(user: CurrentUser):
    return UserResponse(id=user.id, email=user.email, role=user.role.value)


def _store_refresh_token(db: Session, user_id, token: str):
    from hashlib import sha256
    token_hash = sha256(token.encode()).hexdigest()
    from datetime import datetime, timezone, timedelta
    from app.core.config import settings
    expires = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    rt = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires)
    db.add(rt)
    db.commit()
