from fastapi import APIRouter, Query
from uuid import UUID
from typing import Optional, List

from app.core.dependencies import DB, CurrentHR
from app.core.exceptions import not_found, forbidden, bad_request, conflict
from app.models.user import User
from app.models.hr import HRProfile
from app.models.company import Company
from app.models.job import Job, JobSkill, JobStatus, JobType, WorkMode
from app.models.application import Application, ApplicationStatus
from app.models.shortlist import Shortlist, ShortlistStatus
from app.models.profile_view import ProfileView
from app.models.candidate import CandidateProfile, ProfileVisibility
from app.services.skill_service import get_or_create_skill
from app.services.matching_service import calculate_match_score
from app.services.notification_service import create_notification
from app.models.notification import NotificationType
from app.repositories.candidate_repo import search_candidates
from app.repositories.job_repo import search_jobs, get_job_by_id, get_jobs_by_hr
from app.schemas.job import JobCreateRequest, JobUpdateRequest, JobResponse, JobSkillOut
from app.schemas.candidate import CandidateCardResponse, SkillOut
from app.schemas.application import ApplicantResponse, ApplicationStatusUpdate
from app.schemas.shortlist import ShortlistRequest, ShortlistResponse, ShortlistDetailResponse
from app.schemas.company import CompanyResponse, CompanyUpdateRequest
from app.schemas.matching import HRDashboardResponse, MatchItem
from app.schemas.common import PaginatedResponse
from sqlalchemy.orm import joinedload
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/hr", tags=["HR"])


def _get_hr_profile(db, user) -> HRProfile:
    profile = db.query(HRProfile).filter(HRProfile.user_id == user.id).first()
    if not profile:
        raise not_found("HR_PROFILE_NOT_FOUND", "HR profile not found")
    return profile


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


def _candidate_to_card(c: CandidateProfile, match_score=None) -> CandidateCardResponse:
    skills = [SkillOut(id=cs.id, name=cs.skill.name, proficiency=cs.proficiency, years_of_experience=cs.years_of_experience) for cs in c.skills]
    edu = c.education[0] if c.education else None
    edu_dict = {
        "degree": edu.degree,
        "field_of_study": edu.field_of_study,
        "college": edu.college,
        "graduation_year": edu.graduation_year,
    } if edu else None
    return CandidateCardResponse(
        id=c.id,
        full_name=c.user.full_name,
        headline=c.headline,
        profile_photo_url=c.profile_photo_url,
        current_city=c.current_city,
        experience_level=c.experience_level.value if c.experience_level else None,
        total_experience_years=c.total_experience_years,
        skills=skills,
        education=edu_dict,
        expected_salary_min=c.expected_salary_min,
        expected_salary_max=c.expected_salary_max,
        notice_period_days=c.notice_period_days,
        profile_completion_percentage=c.profile_completion_percentage,
        match_score=match_score,
    )


# ---- Company ----

@router.get("/company", response_model=CompanyResponse)
def get_my_company(user: CurrentHR, db: DB):
    hr = _get_hr_profile(db, user)
    if not hr.company:
        raise not_found("COMPANY_NOT_FOUND", "Company not found")
    return CompanyResponse.model_validate(hr.company)


@router.patch("/company", response_model=CompanyResponse)
def update_my_company(req: CompanyUpdateRequest, user: CurrentHR, db: DB):
    hr = _get_hr_profile(db, user)
    if not hr.company:
        raise not_found("COMPANY_NOT_FOUND", "Company not found")
    for key, val in req.model_dump(exclude_unset=True).items():
        setattr(hr.company, key, val)
    db.commit()
    db.refresh(hr.company)
    return CompanyResponse.model_validate(hr.company)


# ---- Jobs ----

@router.get("/jobs", response_model=PaginatedResponse[JobResponse])
def list_hr_jobs(user: CurrentHR, db: DB, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    hr = _get_hr_profile(db, user)
    items, total, total_pages = get_jobs_by_hr(db, hr.id, page, page_size)
    return PaginatedResponse[JobResponse](
        items=[_job_to_response(j) for j in items],
        page=page, page_size=page_size, total=total, total_pages=total_pages,
    )


@router.post("/jobs", response_model=JobResponse, status_code=201)
def create_job(req: JobCreateRequest, user: CurrentHR, db: DB):
    hr = _get_hr_profile(db, user)
    if not hr.company:
        raise not_found("COMPANY_NOT_FOUND", "You must be associated with a company to create jobs")
    job_type = None
    if req.job_type:
        try:
            job_type = JobType(req.job_type)
        except ValueError:
            raise bad_request("INVALID_JOB_TYPE", "Invalid job type")
    work_mode = None
    if req.work_mode:
        try:
            work_mode = WorkMode(req.work_mode)
        except ValueError:
            raise bad_request("INVALID_WORK_MODE", "Invalid work mode")
    job = Job(
        title=req.title,
        description=req.description,
        company_id=hr.company_id,
        hr_profile_id=hr.id,
        location=req.location,
        city=req.city or "Indore",
        experience_min=req.experience_min,
        experience_max=req.experience_max,
        salary_min=req.salary_min,
        salary_max=req.salary_max,
        job_type=job_type,
        work_mode=work_mode,
        education_requirement=req.education_requirement,
        notice_period_requirement=req.notice_period_requirement,
        status=JobStatus.PUBLISHED,
    )
    db.add(job)
    db.flush()
    for skill_req in req.skills:
        skill = get_or_create_skill(db, skill_req.name)
        js = JobSkill(
            job_id=job.id,
            skill_id=skill.id,
            required=skill_req.required,
            minimum_years=skill_req.minimum_years,
        )
        db.add(js)
    db.commit()
    db.refresh(job)
    job = get_job_by_id(db, job.id)
    return _job_to_response(job)


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_hr_job(job_id: UUID, user: CurrentHR, db: DB):
    hr = _get_hr_profile(db, user)
    job = get_job_by_id(db, job_id)
    if not job:
        raise not_found("JOB_NOT_FOUND", "Job not found")
    if job.hr_profile_id != hr.id:
        raise forbidden("JOB_ACCESS_DENIED", "You can only access your own company jobs")
    return _job_to_response(job)


@router.patch("/jobs/{job_id}", response_model=JobResponse)
def update_hr_job(job_id: UUID, req: JobUpdateRequest, user: CurrentHR, db: DB):
    hr = _get_hr_profile(db, user)
    job = get_job_by_id(db, job_id)
    if not job:
        raise not_found("JOB_NOT_FOUND", "Job not found")
    if job.hr_profile_id != hr.id:
        raise forbidden("JOB_ACCESS_DENIED", "You can only update your own company jobs")
    update_data = req.model_dump(exclude_unset=True)
    skills_data = update_data.pop("skills", None)
    if "job_type" in update_data and update_data["job_type"]:
        update_data["job_type"] = JobType(update_data["job_type"])
    if "work_mode" in update_data and update_data["work_mode"]:
        update_data["work_mode"] = WorkMode(update_data["work_mode"])
    if "status" in update_data and update_data["status"]:
        update_data["status"] = JobStatus(update_data["status"])
    for key, val in update_data.items():
        setattr(job, key, val)
    if skills_data is not None:
        db.query(JobSkill).filter(JobSkill.job_id == job.id).delete()
        db.flush()
        for skill_req in skills_data:
            skill = get_or_create_skill(db, skill_req["name"])
            js = JobSkill(
                job_id=job.id,
                skill_id=skill.id,
                required=skill_req.get("required", False),
                minimum_years=skill_req.get("minimum_years"),
            )
            db.add(js)
    db.commit()
    job = get_job_by_id(db, job.id)
    return _job_to_response(job)


@router.delete("/jobs/{job_id}", status_code=204)
def delete_hr_job(job_id: UUID, user: CurrentHR, db: DB):
    hr = _get_hr_profile(db, user)
    job = get_job_by_id(db, job_id)
    if not job:
        raise not_found("JOB_NOT_FOUND", "Job not found")
    if job.hr_profile_id != hr.id:
        raise forbidden("JOB_ACCESS_DENIED", "You can only delete your own company jobs")
    db.delete(job)
    db.commit()


# ---- Applicants ----

@router.get("/jobs/{job_id}/applicants", response_model=PaginatedResponse[ApplicantResponse])
def get_job_applicants(job_id: UUID, user: CurrentHR, db: DB, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    hr = _get_hr_profile(db, user)
    job = get_job_by_id(db, job_id)
    if not job:
        raise not_found("JOB_NOT_FOUND", "Job not found")
    if job.hr_profile_id != hr.id:
        raise forbidden("JOB_ACCESS_DENIED", "You can only view applicants for your own jobs")
    query = (
        db.query(Application)
        .options(
            joinedload(Application.candidate).joinedload(CandidateProfile.user),
            joinedload(Application.candidate).joinedload(CandidateProfile.skills).joinedload(CandidateProfile.skills.property.mapper.class_.skill),
            joinedload(Application.candidate).joinedload(CandidateProfile.education),
        )
        .filter(Application.job_id == job_id)
        .order_by(Application.created_at.desc())
    )
    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    apps = query.offset((page - 1) * page_size).limit(page_size).all()
    items = []
    for a in apps:
        card = _candidate_to_card(a.candidate)
        items.append(ApplicantResponse(
            id=a.id,
            candidate_id=a.candidate_id,
            job_id=a.job_id,
            status=a.status.value,
            cover_letter=a.cover_letter,
            created_at=a.created_at,
            candidate=card,
        ))
    return PaginatedResponse[ApplicantResponse](
        items=items, page=page, page_size=page_size, total=total, total_pages=total_pages,
    )


@router.patch("/applications/{application_id}/status")
def update_application_status(application_id: UUID, req: ApplicationStatusUpdate, user: CurrentHR, db: DB):
    hr = _get_hr_profile(db, user)
    app = (
        db.query(Application)
        .options(joinedload(Application.job))
        .filter(Application.id == application_id)
        .first()
    )
    if not app:
        raise not_found("APPLICATION_NOT_FOUND", "Application not found")
    if app.job.hr_profile_id != hr.id:
        raise forbidden("APPLICATION_ACCESS_DENIED", "You can only update applications for your own jobs")
    try:
        new_status = ApplicationStatus(req.status)
    except ValueError:
        raise bad_request("INVALID_STATUS", "Invalid application status")
    old_status = app.status
    app.status = new_status
    db.commit()
    if new_status != old_status:
        create_notification(
            db, app.candidate.user_id, NotificationType.APPLICATION_STATUS,
            "Application status updated",
            f"Your application status changed to {new_status.value}.",
            reference_type="APPLICATION",
            reference_id=app.id,
        )
        db.commit()
    return {"id": str(app.id), "status": new_status.value}


# ---- Candidate Search ----

@router.get("/candidates", response_model=PaginatedResponse[CandidateCardResponse])
def search_hr_candidates(
    user: CurrentHR, db: DB,
    keyword: Optional[str] = Query(None),
    skills: Optional[List[str]] = Query(None),
    experience_min: Optional[int] = Query(None),
    experience_max: Optional[int] = Query(None),
    location: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    salary_min: Optional[int] = Query(None),
    salary_max: Optional[int] = Query(None),
    education: Optional[str] = Query(None),
    work_mode: Optional[str] = Query(None),
    job_type: Optional[str] = Query(None),
    profile_completion_min: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    items, total, total_pages = search_candidates(
        db, keyword=keyword, skills=skills, experience_min=experience_min,
        experience_max=experience_max, location=location, city=city,
        salary_min=salary_min, salary_max=salary_max, education=education,
        work_mode=work_mode, job_type=job_type,
        profile_completion_min=profile_completion_min,
        page=page, page_size=page_size,
    )
    cards = [_candidate_to_card(c) for c in items]
    return PaginatedResponse[CandidateCardResponse](
        items=cards, page=page, page_size=page_size, total=total, total_pages=total_pages,
    )


# ---- Top Candidates ----

@router.get("/top-candidates", response_model=PaginatedResponse[MatchItem])
def get_top_candidates(
    user: CurrentHR, db: DB,
    job_id: Optional[UUID] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    hr = _get_hr_profile(db, user)
    if not job_id:
        items, total, total_pages = search_candidates(db, city="Indore", page=page, page_size=page_size)
        match_items = []
        for c in items:
            score, matched, missing, reasons = calculate_match_score(c, [])
            match_items.append(MatchItem(
                candidate=_candidate_to_card(c, score),
                match_score=score,
                matched_skills=matched,
                missing_skills=missing,
                reasons=reasons,
            ))
        match_items.sort(key=lambda x: x.match_score, reverse=True)
        return PaginatedResponse[MatchItem](
            items=match_items, page=page, page_size=page_size, total=total, total_pages=total_pages,
        )
    job = get_job_by_id(db, job_id)
    if not job:
        raise not_found("JOB_NOT_FOUND", "Job not found")
    required_skills = [js.skill.name for js in job.skills]
    items, total, total_pages = search_candidates(
        db, city=job.city, page=page, page_size=page_size,
    )
    match_items = []
    for c in items:
        score, matched, missing, reasons = calculate_match_score(
            c, required_skills,
            exp_min=job.experience_min, exp_max=job.experience_max,
            location=job.city, work_mode=job.work_mode.value if job.work_mode else None,
            education_requirement=job.education_requirement,
            job_type=job.job_type.value if job.job_type else None,
            salary_min=job.salary_min, salary_max=job.salary_max,
            notice_period=job.notice_period_requirement,
        )
        match_items.append(MatchItem(
            candidate=_candidate_to_card(c, score),
            match_score=score,
            matched_skills=matched,
            missing_skills=missing,
            reasons=reasons,
        ))
    match_items.sort(key=lambda x: x.match_score, reverse=True)
    return PaginatedResponse[MatchItem](
        items=match_items, page=page, page_size=page_size, total=total, total_pages=total_pages,
    )


# ---- Shortlist ----

@router.post("/candidates/{candidate_id}/shortlist", response_model=ShortlistResponse)
def shortlist_candidate(candidate_id: UUID, req: ShortlistRequest, user: CurrentHR, db: DB):
    hr = _get_hr_profile(db, user)
    candidate = db.query(CandidateProfile).filter(CandidateProfile.id == candidate_id).first()
    if not candidate:
        raise not_found("CANDIDATE_NOT_FOUND", "Candidate not found")
    job = get_job_by_id(db, UUID(req.job_id))
    if not job:
        raise not_found("JOB_NOT_FOUND", "Job not found")
    if job.hr_profile_id != hr.id:
        raise forbidden("JOB_ACCESS_DENIED", "You can only shortlist for your own jobs")
    existing = db.query(Shortlist).filter(
        Shortlist.candidate_id == candidate_id,
        Shortlist.job_id == UUID(req.job_id),
    ).first()
    if existing:
        existing.status = ShortlistStatus.SHORTLISTED
        db.commit()
        db.refresh(existing)
        return ShortlistResponse.model_validate(existing)
    shortlist = Shortlist(
        candidate_id=candidate_id,
        job_id=UUID(req.job_id),
        hr_profile_id=hr.id,
        status=ShortlistStatus.SHORTLISTED,
    )
    db.add(shortlist)
    db.commit()
    db.refresh(shortlist)
    company_name = hr.company.name if hr.company else "A company"
    create_notification(
        db, candidate.user_id, NotificationType.SHORTLISTED,
        "Your profile was shortlisted",
        f"{company_name} shortlisted your profile for {job.title}.",
        reference_type="SHORTLIST",
        reference_id=shortlist.id,
    )
    db.commit()
    return ShortlistResponse.model_validate(shortlist)


@router.delete("/candidates/{candidate_id}/shortlist", status_code=204)
def remove_shortlist(candidate_id: UUID, user: CurrentHR, db: DB, job_id: str = Query(...)):
    hr = _get_hr_profile(db, user)
    shortlist = db.query(Shortlist).filter(
        Shortlist.candidate_id == candidate_id,
        Shortlist.job_id == UUID(job_id),
        Shortlist.hr_profile_id == hr.id,
    ).first()
    if not shortlist:
        raise not_found("SHORTLIST_NOT_FOUND", "Shortlist not found")
    shortlist.status = ShortlistStatus.REMOVED
    db.commit()


@router.get("/shortlisted", response_model=PaginatedResponse[ShortlistDetailResponse])
def get_hr_shortlisted(user: CurrentHR, db: DB, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    hr = _get_hr_profile(db, user)
    query = (
        db.query(Shortlist)
        .options(
            joinedload(Shortlist.candidate).joinedload(CandidateProfile.user),
            joinedload(Shortlist.candidate).joinedload(CandidateProfile.skills).joinedload(CandidateProfile.skills.property.mapper.class_.skill),
            joinedload(Shortlist.candidate).joinedload(CandidateProfile.education),
            joinedload(Shortlist.job).joinedload(Job.company),
            joinedload(Shortlist.job).joinedload(Job.skills).joinedload(Job.skills.property.mapper.class_.skill),
        )
        .filter(Shortlist.hr_profile_id == hr.id, Shortlist.status == ShortlistStatus.SHORTLISTED)
        .order_by(Shortlist.created_at.desc())
    )
    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for s in items:
        card = _candidate_to_card(s.candidate)
        job_resp = _job_to_response(s.job) if s.job else None
        result.append(ShortlistDetailResponse(
            id=s.id, candidate_id=s.candidate_id, job_id=s.job_id,
            status=s.status.value, created_at=s.created_at,
            candidate=card, job=job_resp,
        ))
    return PaginatedResponse[ShortlistDetailResponse](
        items=result, page=page, page_size=page_size, total=total, total_pages=total_pages,
    )


# ---- Recently Viewed ----

@router.get("/activity/recently-viewed", response_model=dict)
def get_recently_viewed(user: CurrentHR, db: DB):
    hr = _get_hr_profile(db, user)
    views = (
        db.query(ProfileView)
        .options(
            joinedload(ProfileView.candidate).joinedload(CandidateProfile.user),
            joinedload(ProfileView.candidate).joinedload(CandidateProfile.skills).joinedload(CandidateProfile.skills.property.mapper.class_.skill),
            joinedload(ProfileView.candidate).joinedload(CandidateProfile.education),
            joinedload(ProfileView.job),
        )
        .filter(ProfileView.hr_profile_id == hr.id)
        .order_by(ProfileView.created_at.desc())
        .limit(20)
        .all()
    )
    items = []
    for v in views:
        card = _candidate_to_card(v.candidate)
        items.append({
            "candidate": card.model_dump(),
            "job_id": str(v.job_id) if v.job_id else None,
            "job_title": v.job.title if v.job else None,
            "viewed_at": v.created_at.isoformat() if v.created_at else None,
        })
    return {"items": items}


# ---- Dashboard ----

@router.get("/dashboard", response_model=HRDashboardResponse)
def get_hr_dashboard(user: CurrentHR, db: DB):
    hr = _get_hr_profile(db, user)
    active_jobs = db.query(Job).filter(Job.hr_profile_id == hr.id, Job.status == JobStatus.PUBLISHED).count()
    total_applicants = (
        db.query(Application)
        .join(Job, Application.job_id == Job.id)
        .filter(Job.hr_profile_id == hr.id)
        .count()
    )
    shortlisted = (
        db.query(Shortlist)
        .filter(Shortlist.hr_profile_id == hr.id, Shortlist.status == ShortlistStatus.SHORTLISTED)
        .count()
    )
    candidate_views = db.query(ProfileView).filter(ProfileView.hr_profile_id == hr.id).count()
    new_matches = 0
    return HRDashboardResponse(
        active_jobs=active_jobs,
        total_applicants=total_applicants,
        shortlisted=shortlisted,
        candidate_views=candidate_views,
        new_matches=new_matches,
    )
