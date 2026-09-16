import enum
import uuid
from datetime import date, datetime
from typing import List

from sqlalchemy import String, Text, Enum, Integer, Float, Date, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.types import GUID

from app.core.database import Base
from app.models.base import TimestampMixin


class ExperienceLevel(str, enum.Enum):
    FRESHER = "FRESHER"
    JUNIOR = "JUNIOR"
    MID_LEVEL = "MID_LEVEL"
    EXPERIENCED = "EXPERIENCED"
    SENIOR = "SENIOR"


class ProfileVisibility(str, enum.Enum):
    PUBLIC_TO_VERIFIED_HR = "PUBLIC_TO_VERIFIED_HR"
    MATCHED_HR_ONLY = "MATCHED_HR_ONLY"
    PRIVATE = "PRIVATE"


class CandidateProfile(Base, TimestampMixin):
    __tablename__ = "candidate_profiles"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    headline: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    profile_photo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    current_city: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    preferred_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    experience_level: Mapped[ExperienceLevel | None] = mapped_column(Enum(ExperienceLevel), nullable=True)
    total_experience_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    expected_salary_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    expected_salary_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notice_period_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    profile_visibility: Mapped[ProfileVisibility] = mapped_column(
        Enum(ProfileVisibility), default=ProfileVisibility.PUBLIC_TO_VERIFIED_HR, nullable=False
    )
    profile_completion_percentage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    resume_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    user = relationship("User", back_populates="candidate_profile")
    skills = relationship("CandidateSkill", back_populates="candidate", cascade="all, delete-orphan", order_by="CandidateSkill.created_at")
    education = relationship("CandidateEducation", back_populates="candidate", cascade="all, delete-orphan", order_by="CandidateEducation.graduation_year.desc()")
    experience = relationship("CandidateExperience", back_populates="candidate", cascade="all, delete-orphan", order_by="CandidateExperience.start_date.desc()")
    projects = relationship("CandidateProject", back_populates="candidate", cascade="all, delete-orphan", order_by="CandidateProject.created_at.desc()")
    preferences = relationship("CandidatePreference", back_populates="candidate", cascade="all, delete-orphan", uselist=False)
    resume = relationship("CandidateResume", back_populates="candidate", uselist=False, cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="candidate", cascade="all, delete-orphan")
    saved_jobs = relationship("SavedJob", back_populates="candidate", cascade="all, delete-orphan")
    shortlists = relationship("Shortlist", back_populates="candidate", cascade="all, delete-orphan")
    profile_views = relationship("ProfileView", back_populates="candidate", cascade="all, delete-orphan")


class CandidateSkill(Base, TimestampMixin):
    __tablename__ = "candidate_skills"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)
    skill_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("skills.id"), nullable=False)
    proficiency: Mapped[str | None] = mapped_column(String(50), nullable=True)
    years_of_experience: Mapped[int | None] = mapped_column(Integer, nullable=True)

    candidate = relationship("CandidateProfile", back_populates="skills")
    skill = relationship("Skill")


class CandidateEducation(Base, TimestampMixin):
    __tablename__ = "candidate_education"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)
    degree: Mapped[str | None] = mapped_column(String(255), nullable=True)
    field_of_study: Mapped[str | None] = mapped_column(String(255), nullable=True)
    college: Mapped[str | None] = mapped_column(String(255), nullable=True)
    university: Mapped[str | None] = mapped_column(String(255), nullable=True)
    graduation_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    percentage: Mapped[float | None] = mapped_column(Float, nullable=True)
    cgpa: Mapped[float | None] = mapped_column(Float, nullable=True)

    candidate = relationship("CandidateProfile", back_populates="education")


class CandidateExperience(Base, TimestampMixin):
    __tablename__ = "candidate_experience"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    job_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_current: Mapped[bool] = mapped_column(default=False, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    candidate = relationship("CandidateProfile", back_populates="experience")


class CandidateProject(Base, TimestampMixin):
    __tablename__ = "candidate_projects"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    technologies: Mapped[list | None] = mapped_column(JSON, nullable=True)
    project_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    candidate = relationship("CandidateProfile", back_populates="projects")


class CandidatePreference(Base, TimestampMixin):
    __tablename__ = "candidate_preferences"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("candidate_profiles.id", ondelete="CASCADE"), unique=True, nullable=False)
    preferred_roles: Mapped[list | None] = mapped_column(JSON, nullable=True)
    preferred_locations: Mapped[list | None] = mapped_column(JSON, nullable=True)
    preferred_job_types: Mapped[list | None] = mapped_column(JSON, nullable=True)
    preferred_work_modes: Mapped[list | None] = mapped_column(JSON, nullable=True)
    minimum_salary: Mapped[int | None] = mapped_column(Integer, nullable=True)
    maximum_salary: Mapped[int | None] = mapped_column(Integer, nullable=True)

    candidate = relationship("CandidateProfile", back_populates="preferences")


class CandidateResume(Base, TimestampMixin):
    __tablename__ = "candidate_resumes"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("candidate_profiles.id", ondelete="CASCADE"), unique=True, nullable=False)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)

    candidate = relationship("CandidateProfile", back_populates="resume")
