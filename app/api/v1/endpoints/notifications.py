from fastapi import APIRouter, Query
from uuid import UUID

from app.core.dependencies import DB, CurrentUser
from app.core.exceptions import not_found
from app.models.notification import Notification
from app.schemas.notification import NotificationResponse, UnreadCountResponse
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=PaginatedResponse[NotificationResponse])
def get_notifications(user: CurrentUser, db: DB, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    query = (
        db.query(Notification)
        .filter(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
    )
    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse[NotificationResponse](
        items=[NotificationResponse.model_validate(n) for n in items],
        page=page, page_size=page_size, total=total, total_pages=total_pages,
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
def get_unread_count(user: CurrentUser, db: DB):
    count = (
        db.query(Notification)
        .filter(Notification.user_id == user.id, Notification.is_read == False)
        .count()
    )
    return UnreadCountResponse(unread_count=count)


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_read(notification_id: UUID, user: CurrentUser, db: DB):
    notif = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == user.id)
        .first()
    )
    if not notif:
        raise not_found("NOTIFICATION_NOT_FOUND", "Notification not found")
    notif.is_read = True
    db.commit()
    db.refresh(notif)
    return NotificationResponse.model_validate(notif)


@router.patch("/read-all")
def mark_all_read(user: CurrentUser, db: DB):
    db.query(Notification).filter(
        Notification.user_id == user.id, Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    return {"message": "All notifications marked as read"}
