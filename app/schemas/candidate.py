import uuid
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class SkillItem(BaseModel):
    name: str
    proficiency: Optional[str] = None
    years_of_experience: Optional[int] = None


class SkillOut(BaseModel):
    id: uuid.UUID
    name: str
    proficiency: Optional[str] = None
    years_of_experience: Optional[int] = None

    model_config = {"from_attributes": True}


class EducationRequest(BaseModel):
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    college: Optional[str] = None
    university: Optional[str] = None
    graduation_year: Optional[int] = None
    percentage: Optional[float] = None
    cgpa: Optional[float] = None


class EducationOut(BaseModel):
    id: uuid.UUID
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    college: Optional[str] = None
    university: Optional[str] = None
    graduation_year: Optional[int] = None
    percentage: Optional[float] = None
    cgpa: Optional[float] = None

    model_config = {"from_attributes": True}


class ExperienceRequest(BaseModel):
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: bool = False
    description: Optional[str] = None


class ExperienceOut(BaseModel):
    id: uuid.UUID
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: bool
    description: Optional[str] = None

    model_config = {"from_attributes": True}


class ProjectRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    technologies: Optional[List[str]] = None
    project_url: Optional[str] = None


class ProjectOut(BaseModel):
    id: uuid.UUID
    name: Optional[str] = None
    description: Optional[str] = None
    technologies: Optional[List[str]] = None
    project_url: Optional[str] = None

    model_config = {"from_attributes": True}


class PreferenceRequest(BaseModel):
    preferred_roles: Optional[List[str]] = None
    preferred_locations: Optional[List[str]] = None
    preferred_job_types: Optional[List[str]] = None
    preferred_work_modes: Optional[List[str]] = None
    minimum_salary: Optional[int] = None
    maximum_salary: Optional[int] = None


class PreferenceOut(BaseModel):
    id: uuid.UUID
    preferred_roles: Optional[List[str]] = None
    preferred_locations: Optional[List[str]] = None
    preferred_job_types: Optional[List[str]] = None
    preferred_work_modes: Optional[List[str]] = None
    minimum_salary: Optional[int] = None
    maximum_salary: Optional[int] = None

    model_config = {"from_attributes": True}


class CandidateProfileUpdate(BaseModel):
    headline: Optional[str] = None
    bio: Optional[str] = None
    profile_photo_url: Optional[str] = None
    current_city: Optional[str] = None
    preferred_location: Optional[str] = None
    experience_level: Optional[str] = None
    total_experience_years: Optional[int] = None
    current_role: Optional[str] = None
    expected_salary_min: Optional[int] = None
    expected_salary_max: Optional[int] = None
    notice_period_days: Optional[int] = None
    profile_visibility: Optional[str] = None


class CandidateResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    full_name: str
    headline: Optional[str] = None
    bio: Optional[str] = None
    profile_photo_url: Optional[str] = None
    email: str
    phone: Optional[str] = None
    current_city: Optional[str] = None
    preferred_location: Optional[str] = None
    experience_level: Optional[str] = None
    total_experience_years: Optional[int] = None
    current_role: Optional[str] = None
    expected_salary_min: Optional[int] = None
    expected_salary_max: Optional[int] = None
    notice_period_days: Optional[int] = None
    profile_visibility: str
    profile_completion_percentage: int
    resume_url: Optional[str] = None
    skills: List[SkillOut] = []
    education: List[EducationOut] = []
    experience: List[ExperienceOut] = []
    projects: List[ProjectOut] = []
    preferences: Optional[PreferenceOut] = None

    model_config = {"from_attributes": True}


class CandidateCardResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    headline: Optional[str] = None
    profile_photo_url: Optional[str] = None
    current_city: Optional[str] = None
    experience_level: Optional[str] = None
    total_experience_years: Optional[int] = None
    skills: List[SkillOut] = []
    education: Optional[dict] = None
    expected_salary_min: Optional[int] = None
    expected_salary_max: Optional[int] = None
    notice_period_days: Optional[int] = None
    profile_completion_percentage: int
    match_score: Optional[int] = None

    model_config = {"from_attributes": True}


class ProfileCompletionResponse(BaseModel):
    completion_percentage: int
    completed_sections: List[str]
    missing_sections: List[str]


class SkillsUpdateRequest(BaseModel):
    skills: List[SkillItem]


class ResumeRequest(BaseModel):
    file_name: str
    file_url: str
    file_size: Optional[int] = None


class ResumeResponse(BaseModel):
    file_name: Optional[str] = None
    file_url: Optional[str] = None
    file_size: Optional[int] = None

    model_config = {"from_attributes": True}


class ProfileViewResponse(BaseModel):
    profile_view_count: int
    recorded: bool


class ProfileViewHistoryItem(BaseModel):
    company_id: Optional[uuid.UUID] = None
    company_name: str
    job_id: Optional[uuid.UUID] = None
    job_title: Optional[str] = None
    viewed_at: datetime


class ProfileViewHistoryResponse(BaseModel):
    total_views: int
    recent_views: List[ProfileViewHistoryItem]


class RecentlyViewedItem(BaseModel):
    candidate: CandidateCardResponse
    job_id: Optional[uuid.UUID] = None
    job_title: Optional[str] = None
    viewed_at: datetime


class ActivityItem(BaseModel):
    type: str
    title: str
    description: str
    created_at: datetime


class CandidateDashboardResponse(BaseModel):
    profile_completion: dict
    applications_count: int
    profile_views: int
    shortlisted_count: int
    saved_jobs_count: int
    recommended_jobs: List[dict] = []
    recent_activity: List[ActivityItem] = []
    notifications: List[dict] = []
