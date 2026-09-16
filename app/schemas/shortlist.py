import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.schemas.candidate import CandidateCardResponse
from app.schemas.job import JobResponse


class ShortlistRequest(BaseModel):
    job_id: str


class ShortlistResponse(BaseModel):
    id: uuid.UUID
    candidate_id: uuid.UUID
    job_id: uuid.UUID
    status: str

    model_config = {"from_attributes": True}


class ShortlistDetailResponse(BaseModel):
    id: uuid.UUID
    candidate_id: uuid.UUID
    job_id: uuid.UUID
    status: str
    created_at: datetime
    candidate: Optional[CandidateCardResponse] = None
    job: Optional[JobResponse] = None

    model_config = {"from_attributes": True}
