from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from app.models.job import Job, JobStatus
from app.models.skill import Skill


def search_jobs(
    db: Session,
    keyword: Optional[str] = None,
    skills: Optional[List[str]] = None,
    location: Optional[str] = None,
    city: Optional[str] = None,
    experience_min: Optional[int] = None,
    experience_max: Optional[int] = None,
    salary_min: Optional[int] = None,
    salary_max: Optional[int] = None,
    job_type: Optional[str] = None,
    work_mode: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
):
    query = db.query(Job).filter(Job.status == JobStatus.PUBLISHED)

    if keyword:
        like = f"%{keyword}%"
        query = query.filter(or_(Job.title.ilike(like), Job.description.ilike(like)))
    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))
    if city:
        query = query.filter(Job.city.ilike(f"%{city}%"))
    if experience_min is not None:
        query = query.filter(Job.experience_min >= experience_min)
    if experience_max is not None:
        query = query.filter(Job.experience_max <= experience_max)
    if salary_min is not None:
        query = query.filter(Job.salary_min >= salary_min)
    if salary_max is not None:
        query = query.filter(Job.salary_max <= salary_max)
    if job_type:
        query = query.filter(Job.job_type == job_type)
    if work_mode:
        query = query.filter(Job.work_mode == work_mode)

    if skills:
        from app.models.job import JobSkill
        for skill_name in skills:
            normalized = skill_name.strip().lower().replace("-", "").replace("_", "").replace(" ", "")
            query = query.filter(
                Job.id.in_(
                    db.query(JobSkill.job_id)
                    .join(Skill, JobSkill.skill_id == Skill.id)
                    .filter(Skill.normalized_name == normalized)
                )
            )

    total = query.count()
    total_pages = (total + page_size - 1) // page_size if page_size else 1
    items = (
        query.options(joinedload(Job.company), joinedload(Job.skills).joinedload(Job.skills.property.mapper.class_.skill))
        .order_by(Job.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total, total_pages


def get_job_by_id(db: Session, job_id) -> Optional[Job]:
    return (
        db.query(Job)
        .options(joinedload(Job.company), joinedload(Job.skills).joinedload(Job.skills.property.mapper.class_.skill))
        .filter(Job.id == job_id)
        .first()
    )


def get_jobs_by_hr(db: Session, hr_profile_id, page=1, page_size=20):
    query = (
        db.query(Job)
        .options(joinedload(Job.company), joinedload(Job.skills).joinedload(Job.skills.property.mapper.class_.skill))
        .filter(Job.hr_profile_id == hr_profile_id)
        .order_by(Job.created_at.desc())
    )
    total = query.count()
    total_pages = (total + page_size - 1) // page_size if page_size else 1
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return items, total, total_pages
