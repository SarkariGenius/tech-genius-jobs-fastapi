"""
Seed script for Tech Genius - creates demo data for development.
Run: python -m scripts.seed
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.models.candidate import (
    CandidateProfile, CandidateSkill, CandidateEducation,
    CandidateExperience, CandidateProject, CandidatePreference,
    ExperienceLevel, ProfileVisibility,
)
from app.models.hr import HRProfile
from app.models.company import Company
from app.models.skill import Skill
from app.models.job import Job, JobSkill, JobStatus, JobType, WorkMode
from app.models.application import Application, ApplicationStatus
from app.models.profile_view import ProfileView
from app.models.notification import Notification, NotificationType
from datetime import datetime, timezone, date, timedelta


def normalize(name: str) -> str:
    return name.strip().lower().replace("-", "").replace("_", "").replace(" ", "")


def get_or_create_skill(db, name: str) -> Skill:
    norm = normalize(name)
    skill = db.query(Skill).filter(Skill.normalized_name == norm).first()
    if not skill:
        skill = Skill(name=name.strip(), normalized_name=norm)
        db.add(skill)
        db.flush()
    return skill


def seed():
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            print("Database already has data. Skipping seed.")
            return

        print("Seeding Tech Genius demo data...")

        # Companies
        companies_data = [
            {"name": "TechVision Solutions", "industry": "IT", "city": "Indore", "is_verified": True},
            {"name": "CodeCraft Labs", "industry": "Software", "city": "Indore", "is_verified": True},
            {"name": "DataFlow Systems", "industry": "IT", "city": "Indore", "is_verified": True},
            {"name": "InnovateIndore", "industry": "Technology", "city": "Indore", "is_verified": True},
            {"name": "CloudNine Tech", "industry": "Cloud Services", "city": "Pune", "is_verified": True},
            {"name": "StartupHub Indore", "industry": "Startup", "city": "Indore", "is_verified": False},
        ]
        companies = []
        for cd in companies_data:
            c = Company(**cd, location=cd["city"])
            db.add(c)
            db.flush()
            companies.append(c)

        # HR users
        hr_data = [
            {"full_name": "Rahul Sharma", "email": "rahul@techvision.com", "company": companies[0], "designation": "HR Manager"},
            {"full_name": "Priya Patel", "email": "priya@codecraft.com", "company": companies[1], "designation": "Senior HR"},
            {"full_name": "Amit Verma", "email": "amit@dataflow.com", "company": companies[2], "designation": "Talent Acquisition"},
            {"full_name": "Sneha Gupta", "email": "sneha@innovateindore.com", "company": companies[3], "designation": "HR Executive"},
        ]
        hr_profiles = []
        for hd in hr_data:
            u = User(
                email=hd["email"],
                password_hash=hash_password("Password@123"),
                full_name=hd["full_name"],
                phone="9999999999",
                role=UserRole.HR,
            )
            db.add(u)
            db.flush()
            hr = HRProfile(user_id=u.id, company_id=hd["company"].id, designation=hd["designation"])
            db.add(hr)
            db.flush()
            hr_profiles.append(hr)

        # Candidate users
        candidate_data = [
            {"full_name": "Aman Sharma", "email": "aman@example.com", "headline": "Python Developer", "city": "Indore", "exp": "JUNIOR", "years": 2, "skills": [("Python", "ADVANCED", 2), ("FastAPI", "INTERMEDIATE", 1), ("SQL", "INTERMEDIATE", 1)]},
            {"full_name": "Neha Singh", "email": "neha@example.com", "headline": "Full Stack Developer", "city": "Indore", "exp": "MID_LEVEL", "years": 3, "skills": [("JavaScript", "ADVANCED", 3), ("React", "ADVANCED", 2), ("Node.js", "INTERMEDIATE", 2)]},
            {"full_name": "Karan Mehta", "email": "karan@example.com", "headline": "Data Scientist", "city": "Indore", "exp": "MID_LEVEL", "years": 3, "skills": [("Python", "ADVANCED", 3), ("SQL", "ADVANCED", 3), ("Machine Learning", "INTERMEDIATE", 2)]},
            {"full_name": "Pooja Jain", "email": "pooja@example.com", "headline": "Backend Developer", "city": "Indore", "exp": "FRESHER", "years": 0, "skills": [("Java", "INTERMEDIATE", 1), ("Spring", "BEGINNER", 0)]},
            {"full_name": "Vikram Rao", "email": "vikram@example.com", "headline": "DevOps Engineer", "city": "Indore", "exp": "EXPERIENCED", "years": 5, "skills": [("Docker", "ADVANCED", 3), ("Kubernetes", "ADVANCED", 2), ("AWS", "ADVANCED", 3)]},
            {"full_name": "Ananya Das", "email": "ananya@example.com", "headline": "Frontend Developer", "city": "Indore", "exp": "JUNIOR", "years": 2, "skills": [("React", "ADVANCED", 2), ("TypeScript", "INTERMEDIATE", 1), ("CSS", "ADVANCED", 3)]},
            {"full_name": "Rohit Kumar", "email": "rohit@example.com", "headline": "Python Developer", "city": "Indore", "exp": "JUNIOR", "years": 1, "skills": [("Python", "INTERMEDIATE", 1), ("Django", "INTERMEDIATE", 1)]},
            {"full_name": "Ishita Agarwal", "email": "ishita@example.com", "headline": "Software Engineer", "city": "Pune", "exp": "MID_LEVEL", "years": 4, "skills": [("Python", "ADVANCED", 4), ("FastAPI", "ADVANCED", 2), ("PostgreSQL", "INTERMEDIATE", 2)]},
            {"full_name": "Arjun Nair", "email": "arjun@example.com", "headline": "Backend Engineer", "city": "Indore", "exp": "SENIOR", "years": 7, "skills": [("Python", "ADVANCED", 7), ("SQL", "ADVANCED", 6), ("System Design", "ADVANCED", 5)]},
            {"full_name": "Divya Reddy", "email": "divya@example.com", "headline": "Junior Developer", "city": "Indore", "exp": "FRESHER", "years": 0, "skills": [("Python", "BEGINNER", 0), ("HTML", "INTERMEDIATE", 1)]},
        ]

        candidates = []
        for cd in candidate_data:
            u = User(
                email=cd["email"],
                password_hash=hash_password("Password@123"),
                full_name=cd["full_name"],
                phone="9999999999",
                role=UserRole.STUDENT,
            )
            db.add(u)
            db.flush()
            try:
                exp_level = ExperienceLevel(cd["exp"])
            except ValueError:
                exp_level = ExperienceLevel.FRESHER
            profile = CandidateProfile(
                user_id=u.id,
                headline=cd["headline"],
                bio=f"DEMO: {cd['full_name']} is a {cd['headline']} based in {cd['city']}.",
                current_city=cd["city"],
                experience_level=exp_level,
                total_experience_years=cd["years"],
                expected_salary_min=400000,
                expected_salary_max=800000,
                notice_period_days=30,
                profile_visibility=ProfileVisibility.PUBLIC_TO_VERIFIED_HR,
                profile_completion_percentage=85,
            )
            db.add(profile)
            db.flush()

            for skill_name, prof, years in cd["skills"]:
                skill = get_or_create_skill(db, skill_name)
                cs = CandidateSkill(
                    candidate_id=profile.id,
                    skill_id=skill.id,
                    proficiency=prof,
                    years_of_experience=years,
                )
                db.add(cs)

            edu = CandidateEducation(
                candidate_id=profile.id,
                degree="B.Tech",
                field_of_study="Computer Science",
                college="IIT Indore",
                university="IIT",
                graduation_year=2022,
                cgpa=8.5,
            )
            db.add(edu)

            if cd["years"] > 0:
                exp = CandidateExperience(
                    candidate_id=profile.id,
                    company_name="Previous Company",
                    job_title=cd["headline"],
                    start_date=date(2022, 1, 1),
                    is_current=True,
                    description="DEMO experience entry",
                )
                db.add(exp)

            proj = CandidateProject(
                candidate_id=profile.id,
                name="Demo Project",
                description="DEMO: A sample project",
                technologies=[s[0] for s in cd["skills"]],
            )
            db.add(proj)

            pref = CandidatePreference(
                candidate_id=profile.id,
                preferred_roles=[cd["headline"]],
                preferred_locations=["Indore", "Pune"],
                preferred_job_types=["FULL_TIME"],
                preferred_work_modes=["HYBRID", "REMOTE"],
                minimum_salary=400000,
                maximum_salary=800000,
            )
            db.add(pref)
            candidates.append(profile)

        db.flush()

        # Jobs
        jobs_data = [
            {"title": "Python Developer", "hr": hr_profiles[0], "city": "Indore", "exp_min": 1, "exp_max": 3, "skills": [("Python", True, 1), ("FastAPI", True, 1), ("SQL", True, 1)]},
            {"title": "Full Stack Developer", "hr": hr_profiles[1], "city": "Indore", "exp_min": 2, "exp_max": 5, "skills": [("JavaScript", True, 2), ("React", True, 2), ("Node.js", True, 1)]},
            {"title": "Data Scientist", "hr": hr_profiles[2], "city": "Indore", "exp_min": 2, "exp_max": 4, "skills": [("Python", True, 2), ("SQL", True, 2), ("Machine Learning", True, 1)]},
            {"title": "Junior Backend Developer", "hr": hr_profiles[0], "city": "Indore", "exp_min": 0, "exp_max": 1, "skills": [("Python", True, 0)]},
            {"title": "DevOps Engineer", "hr": hr_profiles[3], "city": "Indore", "exp_min": 3, "exp_max": 6, "skills": [("Docker", True, 2), ("Kubernetes", True, 1), ("AWS", True, 2)]},
            {"title": "Frontend Developer", "hr": hr_profiles[1], "city": "Indore", "exp_min": 1, "exp_max": 3, "skills": [("React", True, 1), ("TypeScript", True, 1)]},
            {"title": "Senior Python Developer", "hr": hr_profiles[0], "city": "Indore", "exp_min": 5, "exp_max": 10, "skills": [("Python", True, 5), ("SQL", True, 4), ("System Design", True, 3)]},
            {"title": "Software Engineer Intern", "hr": hr_profiles[2], "city": "Indore", "exp_min": 0, "exp_max": 0, "skills": [("Python", False, 0)]},
            {"title": "Backend Developer (Remote)", "hr": hr_profiles[3], "city": "Pune", "exp_min": 2, "exp_max": 5, "skills": [("Python", True, 2), ("FastAPI", True, 1)]},
            {"title": "Java Developer", "hr": hr_profiles[1], "city": "Indore", "exp_min": 1, "exp_max": 3, "skills": [("Java", True, 1), ("Spring", True, 1)]},
        ]
        jobs = []
        for jd in jobs_data:
            job = Job(
                title=jd["title"],
                description=f"DEMO: {jd['title']} position at {jd['hr'].company.name}",
                company_id=jd["hr"].company_id,
                hr_profile_id=jd["hr"].id,
                location=jd["city"],
                city=jd["city"],
                experience_min=jd["exp_min"],
                experience_max=jd["exp_max"],
                salary_min=400000,
                salary_max=800000,
                job_type=JobType.FULL_TIME,
                work_mode=WorkMode.HYBRID,
                education_requirement="B.Tech",
                notice_period_requirement=30,
                status=JobStatus.PUBLISHED,
            )
            db.add(job)
            db.flush()
            for skill_name, required, min_years in jd["skills"]:
                skill = get_or_create_skill(db, skill_name)
                js = JobSkill(job_id=job.id, skill_id=skill.id, required=required, minimum_years=min_years)
                db.add(js)
            jobs.append(job)

        db.flush()

        # Applications
        if len(candidates) >= 3 and len(jobs) >= 3:
            for i in range(3):
                app = Application(
                    candidate_id=candidates[i].id,
                    job_id=jobs[i].id,
                    status=ApplicationStatus.APPLIED,
                )
                db.add(app)

        # Profile views
        if candidates and hr_profiles:
            for i in range(min(5, len(candidates))):
                view = ProfileView(
                    candidate_id=candidates[i].id,
                    hr_profile_id=hr_profiles[0].id,
                    created_at=datetime.now(timezone.utc) - timedelta(days=i),
                )
                db.add(view)

        # Notifications
        if candidates:
            for i in range(min(3, len(candidates))):
                notif = Notification(
                    user_id=candidates[i].user_id,
                    type=NotificationType.PROFILE_VIEWED,
                    title="Your profile was viewed",
                    message="DEMO: TechVision Solutions viewed your profile.",
                    reference_type="PROFILE_VIEW",
                )
                db.add(notif)

        db.commit()
        print(f"Seed complete: {len(companies)} companies, {len(hr_profiles)} HR, {len(candidates)} candidates, {len(jobs)} jobs")
        print("\nDemo login credentials:")
        print("  Student: aman@example.com / Password@123")
        print("  HR:      rahul@techvision.com / Password@123")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
