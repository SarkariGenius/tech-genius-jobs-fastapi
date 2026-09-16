import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from app.schemas.candidate import SkillOut


class JobSkillRequest(BaseModel):
    name: str
    required: bool = False
    minimum_years: Optional[int] = None


class JobSkillOut(BaseModel):
    id: uuid.UUID
    name: str
    required: bool
    minimum_years: Optional[int] = None

    model_config = {"from_attributes": True}


class CompanyBrief(BaseModel):
    id: uuid.UUID
    name: str
    logo_url: Optional[str] = None
    is_verified: bool

    model_config = {"from_attributes": True}


class JobCreateRequest(BaseModel):
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    city: Optional[str] = None
    experience_min: Optional[int] = None
    experience_max: Optional[int] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    job_type: Optional[str] = None
    work_mode: Optional[str] = None
    education_requirement: Optional[str] = None
    notice_period_requirement: Optional[int] = None
    skills: List[JobSkillRequest] = []


class JobUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    city: Optional[str] = None
    experience_min: Optional[int] = None
    experience_max: Optional[int] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    job_type: Optional[str] = None
    work_mode: Optional[str] = None
    education_requirement: Optional[str] = None
    notice_period_requirement: Optional[int] = None
    skills: Optional[List[JobSkillRequest]] = None
    status: Optional[str] = None


class JobResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str] = None
    company: CompanyBrief
    location: Optional[str] = None
    city: Optional[str] = None
    experience_min: Optional[int] = None
    experience_max: Optional[int] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    job_type: Optional[str] = None
    work_mode: Optional[str] = None
    education_requirement: Optional[str] = None
    notice_period_requirement: Optional[int] = None
    skills: List[JobSkillOut] = []
    status: str
    created_at: datetime
    expires_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
