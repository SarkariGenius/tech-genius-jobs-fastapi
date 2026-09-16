from fastapi import APIRouter, Query
from uuid import UUID
from typing import Optional, List

from app.core.dependencies import DB, CurrentUser
from app.core.exceptions import not_found
from app.repositories.job_repo import search_jobs, get_job_by_id
from app.schemas.job import JobResponse, JobSkillOut
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("", response_model=PaginatedResponse[JobResponse])
def list_jobs(
    db: DB,
    keyword: Optional[str] = Query(None),
    skills: Optional[List[str]] = Query(None),
    location: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    experience_min: Optional[int] = Query(None),
    experience_max: Optional[int] = Query(None),
    salary_min: Optional[int] = Query(None),
    salary_max: Optional[int] = Query(None),
    job_type: Optional[str] = Query(None),
    work_mode: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    if not city and not location:
        city = "Indore"
    items, total, total_pages = search_jobs(
        db, keyword=keyword, skills=skills, location=location, city=city,
        experience_min=experience_min, experience_max=experience_max,
        salary_min=salary_min, salary_max=salary_max,
        job_type=job_type, work_mode=work_mode,
        page=page, page_size=page_size,
    )
    return PaginatedResponse[JobResponse](
        items=[_job_to_response(j) for j in items],
        page=page, page_size=page_size, total=total, total_pages=total_pages,
    )


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: UUID, db: DB):
    job = get_job_by_id(db, job_id)
    if not job:
        raise not_found("JOB_NOT_FOUND", "Job not found")
    return _job_to_response(job)


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
