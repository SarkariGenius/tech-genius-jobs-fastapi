from fastapi import APIRouter
from uuid import UUID
from datetime import datetime, timezone, timedelta

from app.core.dependencies import DB, CurrentUser
from app.core.exceptions import not_found, forbidden
from app.models.candidate import CandidateProfile, ProfileVisibility
from app.models.hr import HRProfile
from app.models.profile_view import ProfileView
from app.models.notification import NotificationType
from app.services.notification_service import create_notification
from app.core.config import settings
from app.schemas.candidate import ProfileViewResponse

router = APIRouter(tags=["Profile Views"])


@router.post("/candidates/{candidate_id}/profile-view", response_model=ProfileViewResponse)
def record_profile_view(candidate_id: UUID, user: CurrentUser, db: DB):
    if user.role.value != "HR":
        raise forbidden("HR_ONLY", "Only HR can view candidate profiles")

    candidate = (
        db.query(CandidateProfile)
        .filter(CandidateProfile.id == candidate_id)
        .first()
    )
    if not candidate:
        raise not_found("CANDIDATE_NOT_FOUND", "Candidate not found")

    if candidate.profile_visibility == ProfileVisibility.PRIVATE:
        raise forbidden("PROFILE_PRIVATE", "This candidate's profile is private")

    hr = db.query(HRProfile).filter(HRProfile.user_id == user.id).first()
    if not hr:
        raise not_found("HR_PROFILE_NOT_FOUND", "HR profile not found")

    dedup_window = datetime.now(timezone.utc) - timedelta(minutes=settings.PROFILE_VIEW_DEDUP_MINUTES)
    recent = (
        db.query(ProfileView)
        .filter(
            ProfileView.candidate_id == candidate_id,
            ProfileView.hr_profile_id == hr.id,
            ProfileView.created_at >= dedup_window,
        )
        .first()
    )
    if recent:
        total = db.query(ProfileView).filter(ProfileView.candidate_id == candidate_id).count()
        return ProfileViewResponse(profile_view_count=total, recorded=False)

    view = ProfileView(
        candidate_id=candidate_id,
        hr_profile_id=hr.id,
        created_at=datetime.now(timezone.utc),
    )
    db.add(view)
    db.flush()

    company_name = hr.company.name if hr.company else "A company"
    create_notification(
        db, candidate.user_id, NotificationType.PROFILE_VIEWED,
        "Your profile was viewed",
        f"{company_name} viewed your profile.",
        reference_type="PROFILE_VIEW",
        reference_id=view.id,
    )
    db.commit()

    total = db.query(ProfileView).filter(ProfileView.candidate_id == candidate_id).count()
    return ProfileViewResponse(profile_view_count=total, recorded=True)
