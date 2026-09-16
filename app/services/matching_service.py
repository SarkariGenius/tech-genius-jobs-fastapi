"""
Deterministic matching engine for Tech Genius.

Weights:
  Skills       = 40%
  Experience   = 20%
  Location     = 15%
  Education    = 10%
  Preference   = 10%
  Availability = 5%
  Total        = 100%

This module is isolated so it can be replaced/enhanced later
(e.g. with an AI-based engine) without touching the rest of the codebase.
"""

from typing import List, Optional
from app.models.candidate import CandidateProfile


WEIGHTS = {
    "skills": 40,
    "experience": 20,
    "location": 15,
    "education": 10,
    "preference": 10,
    "availability": 5,
}


def _normalize_skill(name: str) -> str:
    return name.strip().lower().replace("-", "").replace("_", "").replace(" ", "")


def calculate_skill_match(
    candidate_skills: List[str],
    required_skills: List[str],
) -> tuple[float, List[str], List[str]]:
    if not required_skills:
        return 1.0, [], []
    candidate_set = {_normalize_skill(s) for s in candidate_skills}
    matched = []
    missing = []
    for skill in required_skills:
        norm = _normalize_skill(skill)
        if norm in candidate_set:
            matched.append(skill)
        else:
            missing.append(skill)
    ratio = len(matched) / len(required_skills)
    return ratio, matched, missing


def calculate_experience_match(
    candidate_years: Optional[int],
    exp_min: Optional[int],
    exp_max: Optional[int],
) -> float:
    if exp_min is None and exp_max is None:
        return 1.0
    if candidate_years is None:
        candidate_years = 0
    if exp_min is not None and exp_max is not None:
        if exp_min <= candidate_years <= exp_max:
            return 1.0
        if candidate_years < exp_min:
            deficit = exp_min - candidate_years
            return max(0.0, 1.0 - deficit * 0.25)
        over = candidate_years - exp_max
        return max(0.5, 1.0 - over * 0.1)
    if exp_min is not None:
        return 1.0 if candidate_years >= exp_min else max(0.0, 1.0 - (exp_min - candidate_years) * 0.25)
    if exp_max is not None:
        return 1.0 if candidate_years <= exp_max else max(0.5, 1.0 - (candidate_years - exp_max) * 0.1)
    return 1.0


def calculate_location_match(
    candidate_city: Optional[str],
    required_location: Optional[str],
) -> float:
    if not required_location:
        return 1.0
    if not candidate_city:
        return 0.0
    if candidate_city.strip().lower() == required_location.strip().lower():
        return 1.0
    return 0.3


def calculate_education_match(
    candidate_education: list,
    education_requirement: Optional[str],
) -> float:
    if not education_requirement:
        return 1.0
    if not candidate_education:
        return 0.0
    req_lower = education_requirement.lower()
    for edu in candidate_education:
        degree = (edu.degree or "").lower()
        field = (edu.field_of_study or "").lower()
        if req_lower in degree or req_lower in field or degree in req_lower:
            return 1.0
    return 0.5


def calculate_preference_match(
    candidate_preferences,
    job_type: Optional[str],
    work_mode: Optional[str],
    salary_min: Optional[int],
    salary_max: Optional[int],
) -> float:
    if not candidate_preferences:
        return 0.5
    score = 0.0
    factors = 0
    if job_type:
        factors += 1
        preferred_types = candidate_preferences.preferred_job_types or []
        if not preferred_types or job_type in preferred_types:
            score += 1.0
    if work_mode:
        factors += 1
        preferred_modes = candidate_preferences.preferred_work_modes or []
        if not preferred_modes or work_mode in preferred_modes:
            score += 1.0
    if salary_min is not None and salary_max is not None:
        factors += 1
        min_pref = candidate_preferences.minimum_salary
        max_pref = candidate_preferences.maximum_salary
        if min_pref is not None and max_pref is not None:
            if not (max_pref < salary_min or min_pref > salary_max):
                score += 1.0
        else:
            score += 0.5
    if factors == 0:
        return 1.0
    return score / factors


def calculate_availability_match(
    candidate_notice_period: Optional[int],
    job_notice_period: Optional[int],
) -> float:
    if job_notice_period is None:
        return 1.0
    if candidate_notice_period is None:
        return 0.5
    if candidate_notice_period <= job_notice_period:
        return 1.0
    diff = candidate_notice_period - job_notice_period
    return max(0.0, 1.0 - diff * 0.02)


def calculate_match_score(
    candidate: CandidateProfile,
    required_skills: List[str],
    exp_min: Optional[int] = None,
    exp_max: Optional[int] = None,
    location: Optional[str] = None,
    work_mode: Optional[str] = None,
    education_requirement: Optional[str] = None,
    job_type: Optional[str] = None,
    salary_min: Optional[int] = None,
    salary_max: Optional[int] = None,
    notice_period: Optional[int] = None,
) -> tuple[int, List[str], List[str], List[str]]:
    candidate_skill_names = [cs.skill.name for cs in candidate.skills]
    skill_ratio, matched_skills, missing_skills = calculate_skill_match(
        candidate_skill_names, required_skills
    )
    skill_score = skill_ratio * WEIGHTS["skills"]

    exp_score = calculate_experience_match(candidate.total_experience_years, exp_min, exp_max) * WEIGHTS["experience"]
    loc_score = calculate_location_match(candidate.current_city, location) * WEIGHTS["location"]
    edu_score = calculate_education_match(candidate.education, education_requirement) * WEIGHTS["education"]
    pref_score = calculate_preference_match(candidate.preferences, job_type, work_mode, salary_min, salary_max) * WEIGHTS["preference"]
    avail_score = calculate_availability_match(candidate.notice_period_days, notice_period) * WEIGHTS["availability"]

    total = round(skill_score + exp_score + loc_score + edu_score + pref_score + avail_score)
    total = max(0, min(100, total))

    reasons: List[str] = []
    if skill_ratio >= 0.8:
        reasons.append("Strong skill match")
    elif skill_ratio >= 0.5:
        reasons.append("Partial skill match")
    if exp_min is not None and exp_max is not None:
        if candidate.total_experience_years and exp_min <= candidate.total_experience_years <= exp_max:
            reasons.append("Experience within required range")
    if location and candidate.current_city and candidate.current_city.lower() == location.lower():
        reasons.append(f"Candidate is located in {location}")
    if candidate.profile_completion_percentage >= 80:
        reasons.append("Well-completed profile")

    if not reasons:
        reasons.append("Profile matches job requirements")

    return total, matched_skills, missing_skills, reasons
