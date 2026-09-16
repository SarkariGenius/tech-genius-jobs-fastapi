from fastapi import APIRouter
from sqlalchemy.orm import Session, joinedload
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import CurrentStudent, CurrentUser, DB
from app.core.exceptions import not_found, bad_request, forbidden
from app.models.candidate import (
    CandidateProfile, CandidateSkill, CandidateEducation,
    CandidateExperience, CandidateProject, CandidatePreference,
    CandidateResume, ExperienceLevel, ProfileVisibility,
)
from app.models.user import User
from app.models.skill import Skill
from app.models.hr import HRProfile
from app.models.company import Company
from app.services.skill_service import get_or_create_skill
from app.services.profile_completion import calculate_profile_completion
from app.schemas.candidate import (
    CandidateResponse, CandidateProfileUpdate, CandidateCardResponse,
    SkillOut, EducationRequest, EducationOut, ExperienceRequest, ExperienceOut,
    ProjectRequest, ProjectOut, PreferenceRequest, PreferenceOut,
    SkillsUpdateRequest, ProfileCompletionResponse, ResumeRequest, ResumeResponse,
    ProfileViewResponse, ProfileViewHistoryResponse, ProfileViewHistoryItem,
    RecentlyViewedItem, ActivityItem, CandidateDashboardResponse,
)

router = APIRouter(prefix="/candidates", tags=["Candidates"])


def _candidate_to_response(c: CandidateProfile) -> CandidateResponse:
    skills = [SkillOut(id=cs.id, name=cs.skill.name, proficiency=cs.proficiency, years_of_experience=cs.years_of_experience) for cs in c.skills]
    education = [EducationOut.model_validate(e) for e in c.education]
    experience = [ExperienceOut.model_validate(e) for e in c.experience]
    projects = [ProjectOut.model_validate(p) for p in c.projects]
    preferences = PreferenceOut.model_validate(c.preferences) if c.preferences else None
    return CandidateResponse(
        id=c.id,
        user_id=c.user_id,
        full_name=c.user.full_name,
        headline=c.headline,
        bio=c.bio,
        profile_photo_url=c.profile_photo_url,
        email=c.user.email,
        phone=c.user.phone,
        current_city=c.current_city,
        preferred_location=c.preferred_location,
        experience_level=c.experience_level.value if c.experience_level else None,
        total_experience_years=c.total_experience_years,
        current_role=c.current_role,
        expected_salary_min=c.expected_salary_min,
        expected_salary_max=c.expected_salary_max,
        notice_period_days=c.notice_period_days,
        profile_visibility=c.profile_visibility.value,
        profile_completion_percentage=c.profile_completion_percentage,
        resume_url=c.resume_url,
        skills=skills,
        education=education,
        experience=experience,
        projects=projects,
        preferences=preferences,
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


def _get_or_create_candidate_profile(db: Session, user: User) -> CandidateProfile:
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user.id).first()
    if not profile:
        raise not_found("CANDIDATE_PROFILE_NOT_FOUND", "Candidate profile not found. Please complete your profile.")
    return profile


def _update_completion(db: Session, candidate: CandidateProfile):
    pct, _, _ = calculate_profile_completion(candidate)
    candidate.profile_completion_percentage = pct
    db.flush()


@router.get("/me", response_model=CandidateResponse)
def get_my_profile(user: CurrentStudent, db: DB):
    c = _get_or_create_candidate_profile(db, user)
    c = (
        db.query(CandidateProfile)
        .options(
            joinedload(CandidateProfile.user),
            joinedload(CandidateProfile.skills).joinedload(CandidateSkill.skill),
            joinedload(CandidateProfile.education),
            joinedload(CandidateProfile.experience),
            joinedload(CandidateProfile.projects),
            joinedload(CandidateProfile.preferences),
            joinedload(CandidateProfile.resume),
        )
        .filter(CandidateProfile.id == c.id)
        .first()
    )
    return _candidate_to_response(c)


@router.patch("/me", response_model=CandidateResponse)
def update_my_profile(req: CandidateProfileUpdate, user: CurrentStudent, db: DB):
    c = _get_or_create_candidate_profile(db, user)
    update_data = req.model_dump(exclude_unset=True)
    if "experience_level" in update_data and update_data["experience_level"]:
        try:
            update_data["experience_level"] = ExperienceLevel(update_data["experience_level"])
        except ValueError:
            raise bad_request("INVALID_EXPERIENCE_LEVEL", "Invalid experience level")
    if "profile_visibility" in update_data and update_data["profile_visibility"]:
        try:
            update_data["profile_visibility"] = ProfileVisibility(update_data["profile_visibility"])
        except ValueError:
            raise bad_request("INVALID_VISIBILITY", "Invalid profile visibility")
    for key, val in update_data.items():
        setattr(c, key, val)
    _update_completion(db, c)
    db.commit()
    db.refresh(c)
    c = (
        db.query(CandidateProfile)
        .options(
            joinedload(CandidateProfile.user),
            joinedload(CandidateProfile.skills).joinedload(CandidateSkill.skill),
            joinedload(CandidateProfile.education),
            joinedload(CandidateProfile.experience),
            joinedload(CandidateProfile.projects),
            joinedload(CandidateProfile.preferences),
            joinedload(CandidateProfile.resume),
        )
        .filter(CandidateProfile.id == c.id)
        .first()
    )
    return _candidate_to_response(c)


@router.get("/{candidate_id}", response_model=CandidateResponse)
def get_candidate(candidate_id: UUID, user: CurrentUser, db: DB):
    c = (
        db.query(CandidateProfile)
        .options(
            joinedload(CandidateProfile.user),
            joinedload(CandidateProfile.skills).joinedload(CandidateSkill.skill),
            joinedload(CandidateProfile.education),
            joinedload(CandidateProfile.experience),
            joinedload(CandidateProfile.projects),
            joinedload(CandidateProfile.preferences),
            joinedload(CandidateProfile.resume),
        )
        .filter(CandidateProfile.id == candidate_id)
        .first()
    )
    if not c:
        raise not_found("CANDIDATE_NOT_FOUND", "Candidate not found")
    if c.profile_visibility == ProfileVisibility.PRIVATE and user.role.value != "ADMIN":
        if user.id != c.user_id:
            raise forbidden("PROFILE_PRIVATE", "This candidate's profile is private")
    return _candidate_to_response(c)


@router.get("/me/profile-completion", response_model=ProfileCompletionResponse)
def get_profile_completion(user: CurrentStudent, db: DB):
    c = _get_or_create_candidate_profile(db, user)
    c = (
        db.query(CandidateProfile)
        .options(joinedload(CandidateProfile.user), joinedload(CandidateProfile.skills).joinedload(CandidateSkill.skill), joinedload(CandidateProfile.education), joinedload(CandidateProfile.experience), joinedload(CandidateProfile.projects), joinedload(CandidateProfile.resume))
        .filter(CandidateProfile.id == c.id)
        .first()
    )
    pct, completed, missing = calculate_profile_completion(c)
    return ProfileCompletionResponse(completion_percentage=pct, completed_sections=completed, missing_sections=missing)


@router.get("/me/skills", response_model=list[SkillOut])
def get_my_skills(user: CurrentStudent, db: DB):
    c = _get_or_create_candidate_profile(db, user)
    skills = db.query(CandidateSkill).filter(CandidateSkill.candidate_id == c.id).all()
    return [SkillOut(id=cs.id, name=cs.skill.name, proficiency=cs.proficiency, years_of_experience=cs.years_of_experience) for cs in skills]


@router.put("/me/skills", response_model=list[SkillOut])
def update_my_skills(req: SkillsUpdateRequest, user: CurrentStudent, db: DB):
    c = _get_or_create_candidate_profile(db, user)
    db.query(CandidateSkill).filter(CandidateSkill.candidate_id == c.id).delete()
    db.flush()
    result = []
    for item in req.skills:
        skill = get_or_create_skill(db, item.name)
        cs = CandidateSkill(
            candidate_id=c.id,
            skill_id=skill.id,
            proficiency=item.proficiency,
            years_of_experience=item.years_of_experience,
        )
        db.add(cs)
        db.flush()
        result.append(SkillOut(id=cs.id, name=skill.name, proficiency=cs.proficiency, years_of_experience=cs.years_of_experience))
    _update_completion(db, c)
    db.commit()
    return result


@router.get("/me/education", response_model=list[EducationOut])
def get_my_education(user: CurrentStudent, db: DB):
    c = _get_or_create_candidate_profile(db, user)
    return [EducationOut.model_validate(e) for e in c.education]


@router.post("/me/education", response_model=EducationOut, status_code=201)
def add_education(req: EducationRequest, user: CurrentStudent, db: DB):
    c = _get_or_create_candidate_profile(db, user)
    edu = CandidateEducation(candidate_id=c.id, **req.model_dump())
    db.add(edu)
    _update_completion(db, c)
    db.commit()
    db.refresh(edu)
    return EducationOut.model_validate(edu)


@router.patch("/me/education/{education_id}", response_model=EducationOut)
def update_education(education_id: UUID, req: EducationRequest, user: CurrentStudent, db: DB):
    c = _get_or_create_candidate_profile(db, user)
    edu = db.query(CandidateEducation).filter(CandidateEducation.id == education_id, CandidateEducation.candidate_id == c.id).first()
    if not edu:
        raise not_found("EDUCATION_NOT_FOUND", "Education record not found")
    for key, val in req.model_dump(exclude_unset=True).items():
        setattr(edu, key, val)
    _update_completion(db, c)
    db.commit()
    db.refresh(edu)
    return EducationOut.model_validate(edu)


@router.delete("/me/education/{education_id}", status_code=204)
def delete_education(education_id: UUID, user: CurrentStudent, db: DB):
    c = _get_or_create_candidate_profile(db, user)
    edu = db.query(CandidateEducation).filter(CandidateEducation.id == education_id, CandidateEducation.candidate_id == c.id).first()
    if not edu:
        raise not_found("EDUCATION_NOT_FOUND", "Education record not found")
    db.delete(edu)
    _update_completion(db, c)
    db.commit()


@router.get("/me/experience", response_model=list[ExperienceOut])
def get_my_experience(user: CurrentStudent, db: DB):
    c = _get_or_create_candidate_profile(db, user)
    return [ExperienceOut.model_validate(e) for e in c.experience]


@router.post("/me/experience", response_model=ExperienceOut, status_code=201)
def add_experience(req: ExperienceRequest, user: CurrentStudent, db: DB):
    c = _get_or_create_candidate_profile(db, user)
    exp = CandidateExperience(candidate_id=c.id, **req.model_dump())
    db.add(exp)
    _update_completion(db, c)
    db.commit()
    db.refresh(exp)
    return ExperienceOut.model_validate(exp)


@router.patch("/me/experience/{experience_id}", response_model=ExperienceOut)
def update_experience(experience_id: UUID, req: ExperienceRequest, user: CurrentStudent, db: DB):
    c = _get_or_create_candidate_profile(db, user)
    exp = db.query(CandidateExperience).filter(CandidateExperience.id == experience_id, CandidateExperience.candidate_id == c.id).first()
    if not exp:
        raise not_found("EXPERIENCE_NOT_FOUND", "Experience record not found")
    for key, val in req.model_dump(exclude_unset=True).items():
        setattr(exp, key, val)
    _update_completion(db, c)
    db.commit()
    db.refresh(exp)
    return ExperienceOut.model_validate(exp)


@router.delete("/me/experience/{experience_id}", status_code=204)
def delete_experience(experience_id: UUID, user: CurrentStudent, db: DB):
    c = _get_or_create_candidate_profile(db, user)
    exp = db.query(CandidateExperience).filter(CandidateExperience.id == experience_id, CandidateExperience.candidate_id == c.id).first()
    if not exp:
        raise not_found("EXPERIENCE_NOT_FOUND", "Experience record not found")
    db.delete(exp)
    _update_completion(db, c)
    db.commit()


@router.get("/me/projects", response_model=list[ProjectOut])
def get_my_projects(user: CurrentStudent, db: DB):
    c = _get_or_create_candidate_profile(db, user)
    return [ProjectOut.model_validate(p) for p in c.projects]


@router.post("/me/projects", response_model=ProjectOut, status_code=201)
def add_project(req: ProjectRequest, user: CurrentStudent, db: DB):
    c = _get_or_create_candidate_profile(db, user)
    proj = CandidateProject(candidate_id=c.id, **req.model_dump())
    db.add(proj)
    _update_completion(db, c)
    db.commit()
    db.refresh(proj)
    return ProjectOut.model_validate(proj)


@router.patch("/me/projects/{project_id}", response_model=ProjectOut)
def update_project(project_id: UUID, req: ProjectRequest, user: CurrentStudent, db: DB):
    c = _get_or_create_candidate_profile(db, user)
    proj = db.query(CandidateProject).filter(CandidateProject.id == project_id, CandidateProject.candidate_id == c.id).first()
    if not proj:
        raise not_found("PROJECT_NOT_FOUND", "Project not found")
    for key, val in req.model_dump(exclude_unset=True).items():
        setattr(proj, key, val)
    _update_completion(db, c)
    db.commit()
    db.refresh(proj)
    return ProjectOut.model_validate(proj)


@router.delete("/me/projects/{project_id}", status_code=204)
def delete_project(project_id: UUID, user: CurrentStudent, db: DB):
    c = _get_or_create_candidate_profile(db, user)
    proj = db.query(CandidateProject).filter(CandidateProject.id == project_id, CandidateProject.candidate_id == c.id).first()
    if not proj:
        raise not_found("PROJECT_NOT_FOUND", "Project not found")
    db.delete(proj)
    _update_completion(db, c)
    db.commit()


@router.get("/me/preferences", response_model=PreferenceOut)
def get_my_preferences(user: CurrentStudent, db: DB):
    c = _get_or_create_candidate_profile(db, user)
    if not c.preferences:
        return PreferenceOut(id=UUID("00000000-0000-0000-0000-000000000000"))
    return PreferenceOut.model_validate(c.preferences)


@router.patch("/me/preferences", response_model=PreferenceOut)
def update_my_preferences(req: PreferenceRequest, user: CurrentStudent, db: DB):
    c = _get_or_create_candidate_profile(db, user)
    if c.preferences:
        for key, val in req.model_dump(exclude_unset=True).items():
            setattr(c.preferences, key, val)
    else:
        pref = CandidatePreference(candidate_id=c.id, **req.model_dump())
        db.add(pref)
    db.commit()
    db.refresh(c)
    if c.preferences:
        return PreferenceOut.model_validate(c.preferences)
    return PreferenceOut(id=UUID("00000000-0000-0000-0000-000000000000"))


@router.get("/me/resume", response_model=ResumeResponse)
def get_my_resume(user: CurrentStudent, db: DB):
    c = _get_or_create_candidate_profile(db, user)
    if c.resume:
        return ResumeResponse.model_validate(c.resume)
    return ResumeResponse()


@router.post("/me/resume", response_model=ResumeResponse)
def upload_resume(req: ResumeRequest, user: CurrentStudent, db: DB):
    c = _get_or_create_candidate_profile(db, user)
    if c.resume:
        c.resume.file_name = req.file_name
        c.resume.file_url = req.file_url
        c.resume.file_size = req.file_size
    else:
        resume = CandidateResume(candidate_id=c.id, file_name=req.file_name, file_url=req.file_url, file_size=req.file_size)
        db.add(resume)
    c.resume_url = req.file_url
    _update_completion(db, c)
    db.commit()
    db.refresh(c)
    if c.resume:
        return ResumeResponse.model_validate(c.resume)
    return ResumeResponse()


@router.delete("/me/resume", status_code=204)
def delete_resume(user: CurrentStudent, db: DB):
    c = _get_or_create_candidate_profile(db, user)
    if c.resume:
        db.delete(c.resume)
    c.resume_url = None
    _update_completion(db, c)
    db.commit()


@router.get("/me/profile-views", response_model=ProfileViewHistoryResponse)
def get_my_profile_views(user: CurrentStudent, db: DB):
    from app.models.profile_view import ProfileView
    c = _get_or_create_candidate_profile(db, user)
    views = (
        db.query(ProfileView)
        .options(joinedload(ProfileView.hr_profile).joinedload(HRProfile.company), joinedload(ProfileView.job))
        .filter(ProfileView.candidate_id == c.id)
        .order_by(ProfileView.created_at.desc())
        .limit(50)
        .all()
    )
    recent = []
    for v in views:
        company_name = v.hr_profile.company.name if v.hr_profile and v.hr_profile.company else "Unknown"
        company_id = v.hr_profile.company_id if v.hr_profile else None
        job_title = v.job.title if v.job else None
        recent.append(ProfileViewHistoryItem(
            company_id=company_id,
            company_name=company_name,
            job_id=v.job_id,
            job_title=job_title,
            viewed_at=v.created_at,
        ))
    total = db.query(ProfileView).filter(ProfileView.candidate_id == c.id).count()
    return ProfileViewHistoryResponse(total_views=total, recent_views=recent)


@router.get("/me/activity", response_model=dict)
def get_my_activity(user: CurrentStudent, db: DB):
    from app.models.profile_view import ProfileView
    from app.models.shortlist import Shortlist, ShortlistStatus
    from app.models.application import Application
    c = _get_or_create_candidate_profile(db, user)
    items: list[ActivityItem] = []

    views = (
        db.query(ProfileView)
        .options(joinedload(ProfileView.hr_profile).joinedload(HRProfile.company))

        .filter(ProfileView.candidate_id == c.id)
        .order_by(ProfileView.created_at.desc())
        .limit(10)
        .all()
    )
    for v in views:
        company_name = v.hr_profile.company.name if v.hr_profile and v.hr_profile.company else "Unknown"
        items.append(ActivityItem(
            type="PROFILE_VIEWED",
            title="Your profile was viewed",
            description=f"{company_name} viewed your profile.",
            created_at=v.created_at,
        ))

    shortlists = (
        db.query(Shortlist)
        .options(
            joinedload(Shortlist.job),
            joinedload(Shortlist.hr_profile).joinedload(HRProfile.company),
        )
        .filter(Shortlist.candidate_id == c.id, Shortlist.status == ShortlistStatus.SHORTLISTED)
        .order_by(Shortlist.created_at.desc())
        .limit(10)
        .all()
    )
    for s in shortlists:
        company_name = s.hr_profile.company.name if s.hr_profile and s.hr_profile.company else "Unknown"
        job_title = s.job.title if s.job else "a position"
        items.append(ActivityItem(
            type="SHORTLISTED",
            title="Your profile was shortlisted",
            description=f"{company_name} shortlisted your profile for {job_title}.",
            created_at=s.created_at,
        ))

    apps = (
        db.query(Application)
        .filter(Application.candidate_id == c.id)
        .order_by(Application.updated_at.desc())
        .limit(10)
        .all()
    )
    for a in apps:
        items.append(ActivityItem(
            type="APPLICATION_STATUS",
            title="Application status updated",
            description=f"Your application status changed to {a.status.value}.",
            created_at=a.updated_at,
        ))

    items.sort(key=lambda x: x.created_at, reverse=True)
    return {"items": [item.model_dump() for item in items[:20]]}


@router.get("/me/dashboard", response_model=CandidateDashboardResponse)
def get_candidate_dashboard(user: CurrentStudent, db: DB):
    from app.models.profile_view import ProfileView
    from app.models.shortlist import Shortlist, ShortlistStatus
    from app.models.application import Application
    from app.models.saved_job import SavedJob
    from app.models.notification import Notification
    from app.services.matching_service import calculate_match_score
    from app.repositories.job_repo import search_jobs

    c = _get_or_create_candidate_profile(db, user)
    pct, _, missing = calculate_profile_completion(c)

    apps_count = db.query(Application).filter(Application.candidate_id == c.id).count()
    views_count = db.query(ProfileView).filter(ProfileView.candidate_id == c.id).count()
    shortlist_count = db.query(Shortlist).filter(Shortlist.candidate_id == c.id, Shortlist.status == ShortlistStatus.SHORTLISTED).count()
    saved_count = db.query(SavedJob).filter(SavedJob.candidate_id == c.id).count()

    job_items, _, _ = search_jobs(db, city=c.current_city or "Indore", page=1, page_size=5)
    recommended = []
    for job in job_items:
        required_skills = [js.skill.name for js in job.skills]
        score, _, _, _ = calculate_match_score(
            c, required_skills,
            exp_min=job.experience_min, exp_max=job.experience_max,
            location=job.city, work_mode=job.work_mode.value if job.work_mode else None,
            education_requirement=job.education_requirement,
            job_type=job.job_type.value if job.job_type else None,
            salary_min=job.salary_min, salary_max=job.salary_max,
            notice_period=job.notice_period_requirement,
        )
        recommended.append({
            "id": str(job.id),
            "title": job.title,
            "company_name": job.company.name if job.company else None,
            "match_score": score,
        })
    recommended.sort(key=lambda x: x["match_score"], reverse=True)

    notifs = (
        db.query(Notification)
        .filter(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
        .limit(5)
        .all()
    )

    activity_items = []
    for n in notifs:
        activity_items.append({
            "type": n.type.value,
            "title": n.title,
            "description": n.message,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        })

    return CandidateDashboardResponse(
        profile_completion={"percentage": pct, "missing_sections": missing},
        applications_count=apps_count,
        profile_views=views_count,
        shortlisted_count=shortlist_count,
        saved_jobs_count=saved_count,
        recommended_jobs=recommended,
        recent_activity=activity_items,
        notifications=[],
    )


@router.get("/me/shortlisted", response_model=dict)
def get_my_shortlisted(user: CurrentStudent, db: DB):
    from app.models.shortlist import Shortlist, ShortlistStatus
    from app.models.job import Job
    c = _get_or_create_candidate_profile(db, user)
    items = (
        db.query(Shortlist)
        .options(
            joinedload(Shortlist.job).joinedload(Job.company),
            joinedload(Shortlist.hr_profile).joinedload(HRProfile.company),
        )
        .filter(Shortlist.candidate_id == c.id, Shortlist.status == ShortlistStatus.SHORTLISTED)
        .order_by(Shortlist.created_at.desc())
        .all()
    )
    result = []
    for s in items:
        result.append({
            "id": str(s.id),
            "candidate_id": str(s.candidate_id),
            "job_id": str(s.job_id),
            "status": s.status.value,
            "company_name": s.hr_profile.company.name if s.hr_profile and s.hr_profile.company else None,
            "job_title": s.job.title if s.job else None,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        })
    return {"items": result, "total": len(result)}
