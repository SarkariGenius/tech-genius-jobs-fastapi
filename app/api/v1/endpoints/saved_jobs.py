from fastapi import APIRouter, Query
from uuid import UUID
from typing import Optional

from app.core.dependencies import DB, CurrentStudent
from app.core.exceptions import not_found, conflict
from app.models.candidate import CandidateProfile
from app.models.saved_job import SavedJob
from app.models.job import Job
from app.repositories.job_repo import get_job_by_id
from app.schemas.job import JobResponse, JobSkillOut
from app.schemas.common import PaginatedResponse
from sqlalchemy.orm import joinedload

router = APIRouter(tags=["Saved Jobs"])


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


@router.post("/candidates/me/saved-jobs/{job_id}", status_code=201)
def save_job(job_id: UUID, user: CurrentStudent, db: DB):
    candidate = db.query(CandidateProfile).filter(CandidateProfile.user_id == user.id).first()
    if not candidate:
        raise not_found("CANDIDATE_PROFILE_NOT_FOUND", "Candidate profile not found")
    job = get_job_by_id(db, job_id)
    if not job:
        raise not_found("JOB_NOT_FOUND", "Job not found")
    existing = db.query(SavedJob).filter(SavedJob.candidate_id == candidate.id, SavedJob.job_id == job_id).first()
    if existing:
        raise conflict("ALREADY_SAVED", "Job already saved")
    saved = SavedJob(candidate_id=candidate.id, job_id=job_id)
    db.add(saved)
    db.commit()
    return {"message": "Job saved successfully"}


@router.delete("/candidates/me/saved-jobs/{job_id}", status_code=204)
def unsave_job(job_id: UUID, user: CurrentStudent, db: DB):
    candidate = db.query(CandidateProfile).filter(CandidateProfile.user_id == user.id).first()
    if not candidate:
        raise not_found("CANDIDATE_PROFILE_NOT_FOUND", "Candidate profile not found")
    saved = db.query(SavedJob).filter(SavedJob.candidate_id == candidate.id, SavedJob.job_id == job_id).first()
    if not saved:
        raise not_found("SAVED_JOB_NOT_FOUND", "Saved job not found")
    db.delete(saved)
    db.commit()


@router.get("/candidates/me/saved-jobs", response_model=PaginatedResponse[JobResponse])
def get_saved_jobs(user: CurrentStudent, db: DB, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    candidate = db.query(CandidateProfile).filter(CandidateProfile.user_id == user.id).first()
    if not candidate:
        raise not_found("CANDIDATE_PROFILE_NOT_FOUND", "Candidate profile not found")
    query = (
        db.query(SavedJob)
        .options(joinedload(SavedJob.job).joinedload(Job.company), joinedload(SavedJob.job).joinedload(Job.skills).joinedload(Job.skills.property.mapper.class_.skill))
        .filter(SavedJob.candidate_id == candidate.id)
        .order_by(SavedJob.created_at.desc())
    )
    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    saved = query.offset((page - 1) * page_size).limit(page_size).all()
    items = [_job_to_response(s.job) for s in saved if s.job]
    return PaginatedResponse[JobResponse](
        items=items, page=page, page_size=page_size, total=total, total_pages=total_pages,
    )
