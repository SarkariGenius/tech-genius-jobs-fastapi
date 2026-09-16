import uuid
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.types import GUID

from app.core.database import Base
from app.models.base import TimestampMixin


class HRProfile(Base, TimestampMixin):
    __tablename__ = "hr_profiles"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    company_id: Mapped[uuid.UUID | None] = mapped_column(GUID, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)
    designation: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user = relationship("User", back_populates="hr_profile")
    company = relationship("Company", back_populates="hr_profiles")
    jobs = relationship("Job", back_populates="hr_profile")
    profile_views = relationship("ProfileView", back_populates="hr_profile")
    shortlists = relationship("Shortlist", back_populates="hr_profile")
