from sqlalchemy.orm import Session
from app.models.skill import Skill


def normalize_skill_name(name: str) -> str:
    return name.strip().lower().replace("-", "").replace("_", "").replace(" ", "")


def get_or_create_skill(db: Session, name: str) -> Skill:
    normalized = normalize_skill_name(name)
    skill = db.query(Skill).filter(Skill.normalized_name == normalized).first()
    if not skill:
        skill = Skill(name=name.strip(), normalized_name=normalized)
        db.add(skill)
        db.flush()
    return skill
