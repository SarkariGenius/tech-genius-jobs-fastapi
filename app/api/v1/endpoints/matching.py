from fastapi import APIRouter, Query
from uuid import UUID
from typing import Optional

from app.core.dependencies import DB, CurrentHR, CurrentStudent
from app.core.exceptions import not_found
from app.models.candidate import CandidateProfile
from app.models.job import Job
from app.services.matching_service import calculate_match_score
from app.repositories.candidate_repo import search_candidates
from app.repositories.job_repo import search_jobs
from app.schemas.matching import MatchingRequest, MatchItem
from app.schemas.candidate import CandidateCardResponse, SkillOut
from app.schemas.job import JobResponse, JobSkillOut
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/matching", tags=["Matching"])


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


@router.post("/candidates", response_model=PaginatedResponse[MatchItem])
def match_candidates(req: MatchingRequest, user: CurrentHR, db: DB, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    items, total, total_pages = search_candidates(
        db, skills=req.skills or None, location=req.location, city=req.location,
        experience_min=req.experience_min, experience_max=req.experience_max,
        page=page, page_size=page_size,
    )
    match_items = []
    for c in items:
        score, matched, missing, reasons = calculate_match_score(
            c, req.skills,
            exp_min=req.experience_min, exp_max=req.experience_max,
            location=req.location, work_mode=req.work_mode,
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


@router.get("/candidates/me/recommended-jobs", response_model=PaginatedResponse[JobResponse])
def get_recommended_jobs(user: CurrentStudent, db: DB, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    candidate = db.query(CandidateProfile).filter(CandidateProfile.user_id == user.id).first()
    if not candidate:
        raise not_found("CANDIDATE_PROFILE_NOT_FOUND", "Candidate profile not found")

    candidate_skills = [cs.skill.name for cs in candidate.skills]
    city = candidate.current_city or "Indore"
    job_items, total, total_pages = search_jobs(
        db, skills=candidate_skills or None, city=city, page=1, page_size=100,
    )

    scored = []
    for job in job_items:
        required_skills = [js.skill.name for js in job.skills]
        score, _, _, _ = calculate_match_score(
            candidate, required_skills,
            exp_min=job.experience_min, exp_max=job.experience_max,
            location=job.city,
            work_mode=job.work_mode.value if job.work_mode else None,
            education_requirement=job.education_requirement,
            job_type=job.job_type.value if job.job_type else None,
            salary_min=job.salary_min, salary_max=job.salary_max,
            notice_period=job.notice_period_requirement,
        )
        scored.append((job, score))
    scored.sort(key=lambda x: x[1], reverse=True)

    start = (page - 1) * page_size
    end = start + page_size
    paged = scored[start:end]

    items = []
    for job, _ in paged:
        items.append(JobResponse(
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
        ))

    return PaginatedResponse[JobResponse](
        items=items, page=page, page_size=page_size, total=total, total_pages=total_pages,
    )
