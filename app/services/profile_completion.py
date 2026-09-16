from app.models.candidate import CandidateProfile


def calculate_profile_completion(candidate: CandidateProfile) -> tuple[int, list[str], list[str]]:
    sections = [
        ("basic_information", _has_basic_info),
        ("contact_information", _has_contact_info),
        ("skills", _has_skills),
        ("education", _has_education),
        ("experience", _has_experience),
        ("projects", _has_projects),
        ("resume", _has_resume),
    ]
    completed = []
    missing = []
    for name, check in sections:
        if check(candidate):
            completed.append(name)
        else:
            missing.append(name)
    total = len(sections)
    pct = int((len(completed) / total) * 100) if total else 0
    return pct, completed, missing


def _has_basic_info(c: CandidateProfile) -> bool:
    return bool(c.headline and c.current_city and c.experience_level)


def _has_contact_info(c: CandidateProfile) -> bool:
    return bool(c.user and c.user.email and c.user.phone)


def _has_skills(c: CandidateProfile) -> bool:
    return len(c.skills) > 0


def _has_education(c: CandidateProfile) -> bool:
    return len(c.education) > 0


def _has_experience(c: CandidateProfile) -> bool:
    return len(c.experience) > 0


def _has_projects(c: CandidateProfile) -> bool:
    return len(c.projects) > 0


def _has_resume(c: CandidateProfile) -> bool:
    return bool(c.resume_url or (c.resume and c.resume.file_url))
