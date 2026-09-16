from sqlalchemy.orm import Session
from app.models.user import User
from app.models.notification import Notification, NotificationType


def create_notification(
    db: Session,
    user_id,
    ntype: NotificationType,
    title: str,
    message: str,
    reference_type: str | None = None,
    reference_id: str | None = None,
) -> Notification:
    notif = Notification(
        user_id=user_id,
        type=ntype,
        title=title,
        message=message,
        reference_type=reference_type,
        reference_id=str(reference_id) if reference_id else None,
    )
    db.add(notif)
    db.flush()
    return notif
