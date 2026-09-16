from typing import Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from app.models.candidate import CandidateProfile
from app.models.user import User, UserRole
from app.models.job import JobStatus


def get_candidate_by_user_id(db: Session, user_id) -> Optional[CandidateProfile]:
    return db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()


def get_candidate_by_id(db: Session, candidate_id) -> Optional[CandidateProfile]:
    return (
        db.query(CandidateProfile)
        .options(
            joinedload(CandidateProfile.user),
            joinedload(CandidateProfile.skills).joinedload(CandidateProfile.skills.property.mapper.class_.skill),
            joinedload(CandidateProfile.education),
            joinedload(CandidateProfile.experience),
            joinedload(CandidateProfile.projects),
            joinedload(CandidateProfile.preferences),
            joinedload(CandidateProfile.resume),
        )
        .filter(CandidateProfile.id == candidate_id)
        .first()
    )


def search_candidates(
    db: Session,
    keyword: Optional[str] = None,
    skills: Optional[list[str]] = None,
    experience_min: Optional[int] = None,
    experience_max: Optional[int] = None,
    location: Optional[str] = None,
    city: Optional[str] = None,
    salary_min: Optional[int] = None,
    salary_max: Optional[int] = None,
    education: Optional[str] = None,
    work_mode: Optional[str] = None,
    job_type: Optional[str] = None,
    profile_completion_min: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
):
    query = db.query(CandidateProfile).join(User, CandidateProfile.user_id == User.id)

    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            or_(
                User.full_name.ilike(like),
                CandidateProfile.headline.ilike(like),
                CandidateProfile.current_role.ilike(like),
                CandidateProfile.bio.ilike(like),
            )
        )
    if experience_min is not None:
        query = query.filter(CandidateProfile.total_experience_years >= experience_min)
    if experience_max is not None:
        query = query.filter(CandidateProfile.total_experience_years <= experience_max)
    if location:
        query = query.filter(CandidateProfile.current_city.ilike(f"%{location}%"))
    if city:
        query = query.filter(CandidateProfile.current_city.ilike(f"%{city}%"))
    if salary_min is not None:
        query = query.filter(CandidateProfile.expected_salary_min >= salary_min)
    if salary_max is not None:
        query = query.filter(CandidateProfile.expected_salary_max <= salary_max)
    if profile_completion_min is not None:
        query = query.filter(CandidateProfile.profile_completion_percentage >= profile_completion_min)

    if skills:
        from app.models.candidate import CandidateSkill
        from app.models.skill import Skill
        for skill_name in skills:
            normalized = skill_name.strip().lower().replace("-", "").replace("_", "").replace(" ", "")
            query = query.filter(
                CandidateProfile.id.in_(
                    db.query(CandidateSkill.candidate_id)
                    .join(Skill, CandidateSkill.skill_id == Skill.id)
                    .filter(Skill.normalized_name == normalized)
                )
            )

    total = query.count()
    total_pages = (total + page_size - 1) // page_size if page_size else 1
    items = (
        query.options(
            joinedload(CandidateProfile.user),
            joinedload(CandidateProfile.skills).joinedload(CandidateProfile.skills.property.mapper.class_.skill),
            joinedload(CandidateProfile.education),
            joinedload(CandidateProfile.preferences),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total, total_pages
