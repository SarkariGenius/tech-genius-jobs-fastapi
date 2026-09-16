from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    candidates,
    hr,
    jobs,
    applications,
    saved_jobs,
    profile_views,
    notifications,
    matching,
    companies,
    admin,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(candidates.router)
api_router.include_router(hr.router)
api_router.include_router(jobs.router)
api_router.include_router(applications.router)
api_router.include_router(saved_jobs.router)
api_router.include_router(profile_views.router)
api_router.include_router(notifications.router)
api_router.include_router(matching.router)
api_router.include_router(companies.router)
api_router.include_router(admin.router)
