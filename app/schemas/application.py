import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.schemas.candidate import CandidateCardResponse
from app.schemas.job import JobResponse


class ApplyRequest(BaseModel):
    cover_letter: Optional[str] = None


class ApplicationResponse(BaseModel):
    id: uuid.UUID
    candidate_id: uuid.UUID
    job_id: uuid.UUID
    status: str
    cover_letter: Optional[str] = None
    created_at: datetime
    job: Optional[JobResponse] = None

    model_config = {"from_attributes": True}


class ApplicantResponse(BaseModel):
    id: uuid.UUID
    candidate_id: uuid.UUID
    job_id: uuid.UUID
    status: str
    cover_letter: Optional[str] = None
    created_at: datetime
    candidate: Optional[CandidateCardResponse] = None

    model_config = {"from_attributes": True}


class ApplicationStatusUpdate(BaseModel):
    status: str
