from typing import Annotated
from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.core.exceptions import unauthorized, forbidden
from app.models.user import User, UserRole

DB = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DB,
    authorization: str | None = Header(default=None),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise unauthorized("NOT_AUTHENTICATED", "Not authenticated")
    token = authorization.removeprefix("Bearer ").strip()
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise unauthorized("INVALID_TOKEN", "Invalid or expired token")
    user_id = payload.get("sub")
    user = db.get(User, user_id)
    if not user:
        raise unauthorized("USER_NOT_FOUND", "User not found")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(*roles: UserRole):
    def checker(user: CurrentUser) -> User:
        if user.role not in roles:
            raise forbidden("FORBIDDEN", "You do not have permission to access this resource")
        return user
    return checker


def get_current_student(user: CurrentUser) -> User:
    if user.role != UserRole.STUDENT:
        raise forbidden("STUDENT_ONLY", "This endpoint is for students only")
    return user


def get_current_hr(user: CurrentUser) -> User:
    if user.role != UserRole.HR:
        raise forbidden("HR_ONLY", "This endpoint is for HR only")
    return user


def get_current_admin(user: CurrentUser) -> User:
    if user.role != UserRole.ADMIN:
        raise forbidden("ADMIN_ONLY", "This endpoint is for admins only")
    return user


CurrentStudent = Annotated[User, Depends(get_current_student)]
CurrentHR = Annotated[User, Depends(get_current_hr)]
CurrentAdmin = Annotated[User, Depends(get_current_admin)]
