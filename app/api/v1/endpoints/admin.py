from fastapi import APIRouter, Query
from uuid import UUID

from app.core.dependencies import DB, CurrentAdmin
from app.core.exceptions import not_found
from app.models.user import User, UserRole
from app.models.candidate import CandidateProfile
from app.models.hr import HRProfile
from app.models.company import Company
from app.models.job import Job, JobStatus
from app.models.application import Application
from app.models.shortlist import Shortlist, ShortlistStatus
from app.models.profile_view import ProfileView
from app.schemas.matching import AdminDashboardResponse, AdminStatisticsResponse
from app.schemas.candidate import CandidateCardResponse, SkillOut
from app.schemas.company import CompanyResponse
from app.schemas.job import JobResponse, JobSkillOut
from app.schemas.application import ApplicationResponse
from app.schemas.common import PaginatedResponse
from sqlalchemy.orm import joinedload

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/dashboard", response_model=AdminDashboardResponse)
def get_admin_dashboard(user: CurrentAdmin, db: DB):
    total_candidates = db.query(CandidateProfile).count()
    total_hr = db.query(HRProfile).count()
    total_companies = db.query(Company).count()
    total_jobs = db.query(Job).count()
    total_applications = db.query(Application).count()
    return AdminDashboardResponse(
        total_candidates=total_candidates,
        total_hr=total_hr,
        total_companies=total_companies,
        total_jobs=total_jobs,
        total_applications=total_applications,
    )


@router.get("/statistics", response_model=AdminStatisticsResponse)
def get_admin_statistics(user: CurrentAdmin, db: DB):
    return AdminStatisticsResponse(
        total_candidates=db.query(CandidateProfile).count(),
        total_hr=db.query(HRProfile).count(),
        total_companies=db.query(Company).count(),
        total_jobs=db.query(Job).count(),
        total_applications=db.query(Application).count(),
        total_shortlists=db.query(Shortlist).filter(Shortlist.status == ShortlistStatus.SHORTLISTED).count(),
        total_profile_views=db.query(ProfileView).count(),
        active_jobs=db.query(Job).filter(Job.status == JobStatus.PUBLISHED).count(),
    )


@router.get("/candidates", response_model=PaginatedResponse[CandidateCardResponse])
def admin_list_candidates(user: CurrentAdmin, db: DB, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    query = (
        db.query(CandidateProfile)
        .options(
            joinedload(CandidateProfile.user),
            joinedload(CandidateProfile.skills).joinedload(CandidateProfile.skills.property.mapper.class_.skill),
            joinedload(CandidateProfile.education),
        )
        .order_by(CandidateProfile.created_at.desc())
    )
    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    cards = []
    for c in items:
        skills = [SkillOut(id=cs.id, name=cs.skill.name, proficiency=cs.proficiency, years_of_experience=cs.years_of_experience) for cs in c.skills]
        edu = c.education[0] if c.education else None
        edu_dict = {"degree": edu.degree, "field_of_study": edu.field_of_study, "college": edu.college, "graduation_year": edu.graduation_year} if edu else None
        cards.append(CandidateCardResponse(
            id=c.id, full_name=c.user.full_name, headline=c.headline,
            profile_photo_url=c.profile_photo_url, current_city=c.current_city,
            experience_level=c.experience_level.value if c.experience_level else None,
            total_experience_years=c.total_experience_years, skills=skills,
            education=edu_dict, expected_salary_min=c.expected_salary_min,
            expected_salary_max=c.expected_salary_max, notice_period_days=c.notice_period_days,
            profile_completion_percentage=c.profile_completion_percentage,
        ))
    return PaginatedResponse[CandidateCardResponse](
        items=cards, page=page, page_size=page_size, total=total, total_pages=total_pages,
    )


@router.get("/hr", response_model=PaginatedResponse[dict])
def admin_list_hr(user: CurrentAdmin, db: DB, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    query = (
        db.query(HRProfile)
        .options(joinedload(HRProfile.user), joinedload(HRProfile.company))
        .order_by(HRProfile.created_at.desc())
    )
    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for h in items:
        result.append({
            "id": str(h.id),
            "full_name": h.user.full_name,
            "email": h.user.email,
            "designation": h.designation,
            "company_name": h.company.name if h.company else None,
        })
    return PaginatedResponse[dict](
        items=result, page=page, page_size=page_size, total=total, total_pages=total_pages,
    )


@router.get("/companies", response_model=PaginatedResponse[CompanyResponse])
def admin_list_companies(user: CurrentAdmin, db: DB, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    query = db.query(Company).order_by(Company.created_at.desc())
    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse[CompanyResponse](
        items=[CompanyResponse.model_validate(c) for c in items],
        page=page, page_size=page_size, total=total, total_pages=total_pages,
    )


@router.get("/jobs", response_model=PaginatedResponse[JobResponse])
def admin_list_jobs(user: CurrentAdmin, db: DB, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    query = (
        db.query(Job)
        .options(joinedload(Job.company), joinedload(Job.skills).joinedload(Job.skills.property.mapper.class_.skill))
        .order_by(Job.created_at.desc())
    )
    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for job in items:
        result.append(JobResponse(
            id=job.id, title=job.title, description=job.description,
            company={"id": job.company.id, "name": job.company.name, "logo_url": job.company.logo_url, "is_verified": job.company.is_verified},
            location=job.location, city=job.city, experience_min=job.experience_min,
            experience_max=job.experience_max, salary_min=job.salary_min, salary_max=job.salary_max,
            job_type=job.job_type.value if job.job_type else None,
            work_mode=job.work_mode.value if job.work_mode else None,
            education_requirement=job.education_requirement,
            notice_period_requirement=job.notice_period_requirement,
            skills=[JobSkillOut(id=js.id, name=js.skill.name, required=js.required, minimum_years=js.minimum_years) for js in job.skills],
            status=job.status.value, created_at=job.created_at, expires_at=job.expires_at,
        ))
    return PaginatedResponse[JobResponse](
        items=result, page=page, page_size=page_size, total=total, total_pages=total_pages,
    )


@router.get("/applications", response_model=PaginatedResponse[ApplicationResponse])
def admin_list_applications(user: CurrentAdmin, db: DB, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    query = db.query(Application).order_by(Application.created_at.desc())
    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse[ApplicationResponse](
        items=[ApplicationResponse(
            id=a.id, candidate_id=a.candidate_id, job_id=a.job_id,
            status=a.status.value, cover_letter=a.cover_letter, created_at=a.created_at,
        ) for a in items],
        page=page, page_size=page_size, total=total, total_pages=total_pages,
    )
