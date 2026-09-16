import enum
import uuid
from sqlalchemy import Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from app.models.base import TimestampMixin


class ShortlistStatus(str, enum.Enum):
    SHORTLISTED = "SHORTLISTED"
    REMOVED = "REMOVED"


class Shortlist(Base, TimestampMixin):
    __tablename__ = "shortlists"
    __table_args__ = (UniqueConstraint("candidate_id", "job_id", name="uq_candidate_job_shortlist"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    hr_profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("hr_profiles.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[ShortlistStatus] = mapped_column(Enum(ShortlistStatus), default=ShortlistStatus.SHORTLISTED, nullable=False)

    candidate = relationship("CandidateProfile", back_populates="shortlists")
    job = relationship("Job", back_populates="shortlists")
    hr_profile = relationship("HRProfile", back_populates="shortlists")
