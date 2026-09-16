import uuid
from typing import List, Optional
from pydantic import BaseModel

from app.schemas.candidate import CandidateCardResponse


class MatchingRequest(BaseModel):
    title: Optional[str] = None
    skills: List[str] = []
    experience_min: Optional[int] = None
    experience_max: Optional[int] = None
    location: Optional[str] = None
    work_mode: Optional[str] = None


class MatchItem(BaseModel):
    candidate: CandidateCardResponse
    match_score: int
    matched_skills: List[str]
    missing_skills: List[str]
    reasons: List[str]


class HRDashboardResponse(BaseModel):
    active_jobs: int
    total_applicants: int
    shortlisted: int
    candidate_views: int
    new_matches: int


class AdminDashboardResponse(BaseModel):
    total_candidates: int
    total_hr: int
    total_companies: int
    total_jobs: int
    total_applications: int


class AdminStatisticsResponse(BaseModel):
    total_candidates: int
    total_hr: int
    total_companies: int
    total_jobs: int
    total_applications: int
    total_shortlists: int
    total_profile_views: int
    active_jobs: int
