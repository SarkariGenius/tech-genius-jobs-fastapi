from fastapi import APIRouter, Query
from uuid import UUID
from typing import Optional

from app.core.dependencies import DB, CurrentStudent
from app.core.exceptions import not_found, conflict
from app.models.application import Application, ApplicationStatus
from app.models.candidate import CandidateProfile
from app.models.job import Job, JobStatus
from app.models.notification import NotificationType
from app.services.notification_service import create_notification
from app.repositories.job_repo import get_job_by_id
from app.schemas.application import ApplyRequest, ApplicationResponse
from app.schemas.job import JobResponse, JobSkillOut
from app.schemas.common import PaginatedResponse
from sqlalchemy.orm import joinedload

router = APIRouter(tags=["Applications"])


def _job_to_response(job) -> JobResponse:
    return JobResponse(
        id=job.id,
        title=job.title,
        description=job.description,
        company={
            "id": job.company.id,
            "name": job.company.name,
            "logo_url": job.company.logo_url,
            "is_verified": job.company.is_verified,
        },
        location=job.location,
        city=job.city,
        experience_min=job.experience_min,
        experience_max=job.experience_max,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        job_type=job.job_type.value if job.job_type else None,
        work_mode=job.work_mode.value if job.work_mode else None,
        education_requirement=job.education_requirement,
        notice_period_requirement=job.notice_period_requirement,
        skills=[
            JobSkillOut(id=js.id, name=js.skill.name, required=js.required, minimum_years=js.minimum_years)
            for js in job.skills
        ],
        status=job.status.value,
        created_at=job.created_at,
        expires_at=job.expires_at,
    )


@router.post("/jobs/{job_id}/apply", response_model=ApplicationResponse, status_code=201)
def apply_to_job(job_id: UUID, req: ApplyRequest, user: CurrentStudent, db: DB):
    candidate = db.query(CandidateProfile).filter(CandidateProfile.user_id == user.id).first()
    if not candidate:
        raise not_found("CANDIDATE_PROFILE_NOT_FOUND", "Candidate profile not found")
    job = get_job_by_id(db, job_id)
    if not job:
        raise not_found("JOB_NOT_FOUND", "Job not found")
    if job.status != JobStatus.PUBLISHED:
        raise conflict("JOB_NOT_AVAILABLE", "This job is no longer accepting applications")
    existing = db.query(Application).filter(
        Application.candidate_id == candidate.id,
        Application.job_id == job_id,
    ).first()
    if existing:
        raise conflict("ALREADY_APPLIED", "You have already applied to this job")
    app = Application(
        candidate_id=candidate.id,
        job_id=job_id,
        status=ApplicationStatus.APPLIED,
        cover_letter=req.cover_letter,
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    job = get_job_by_id(db, job_id)
    return ApplicationResponse(
        id=app.id,
        candidate_id=app.candidate_id,
        job_id=app.job_id,
        status=app.status.value,
        cover_letter=app.cover_letter,
        created_at=app.created_at,
        job=_job_to_response(job),
    )


@router.get("/candidates/me/applications", response_model=PaginatedResponse[ApplicationResponse])
def get_my_applications(user: CurrentStudent, db: DB, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    candidate = db.query(CandidateProfile).filter(CandidateProfile.user_id == user.id).first()
    if not candidate:
        raise not_found("CANDIDATE_PROFILE_NOT_FOUND", "Candidate profile not found")
    query = (
        db.query(Application)
        .options(joinedload(Application.job).joinedload(Job.company), joinedload(Application.job).joinedload(Job.skills).joinedload(Job.skills.property.mapper.class_.skill))
        .filter(Application.candidate_id == candidate.id)
        .order_by(Application.created_at.desc())
    )
    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    apps = query.offset((page - 1) * page_size).limit(page_size).all()
    items = []
    for a in apps:
        job_resp = _job_to_response(a.job) if a.job else None
        items.append(ApplicationResponse(
            id=a.id, candidate_id=a.candidate_id, job_id=a.job_id,
            status=a.status.value, cover_letter=a.cover_letter,
            created_at=a.created_at, job=job_resp,
        ))
    return PaginatedResponse[ApplicationResponse](
        items=items, page=page, page_size=page_size, total=total, total_pages=total_pages,
    )


@router.get("/candidates/me/applications/{application_id}", response_model=ApplicationResponse)
def get_my_application(application_id: UUID, user: CurrentStudent, db: DB):
    candidate = db.query(CandidateProfile).filter(CandidateProfile.user_id == user.id).first()
    if not candidate:
        raise not_found("CANDIDATE_PROFILE_NOT_FOUND", "Candidate profile not found")
    app = (
        db.query(Application)
        .options(joinedload(Application.job).joinedload(Job.company), joinedload(Application.job).joinedload(Job.skills).joinedload(Job.skills.property.mapper.class_.skill))
        .filter(Application.id == application_id, Application.candidate_id == candidate.id)
        .first()
    )
    if not app:
        raise not_found("APPLICATION_NOT_FOUND", "Application not found")
    job_resp = _job_to_response(app.job) if app.job else None
    return ApplicationResponse(
        id=app.id, candidate_id=app.candidate_id, job_id=app.job_id,
        status=app.status.value, cover_letter=app.cover_letter,
        created_at=app.created_at, job=job_resp,
    )
