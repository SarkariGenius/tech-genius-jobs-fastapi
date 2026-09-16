from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.router import api_router
from app.schemas.common import HealthResponse, HealthDatabaseResponse

# 👇 THIS LINE IS THE MAGIC — imports all models so Base knows them
import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    # create all tables on startup
    Base.metadata.create_all(bind=engine)
    print("database Created")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Indore-first recruitment platform connecting Students, HR, Companies, and Jobs.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,   # 👈 add this
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health():
    return HealthResponse(status="ok", service="tech-genius-api")


@app.get("/health/database", response_model=HealthDatabaseResponse, tags=["Health"])
def health_database():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return HealthDatabaseResponse(status="ok", service="tech-genius-api", database="connected")
    except Exception as e:
        print("❌ DB ERROR:", e)
        return HealthDatabaseResponse(status="degraded", service="tech-genius-api", database="disconnected")

# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from sqlalchemy import text

# from app.core.config import settings
# from app.core.database import engine
# from app.api.v1.router import api_router
# from app.schemas.common import HealthResponse, HealthDatabaseResponse

# app = FastAPI(
#     title=settings.APP_NAME,
#     description="Indore-first recruitment platform connecting Students, HR, Companies, and Jobs.",
#     version="1.0.0",
#     docs_url="/docs",
#     redoc_url="/redoc",
# )

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=settings.cors_origins_list,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# app.include_router(api_router)


# @app.get("/health", response_model=HealthResponse, tags=["Health"])
# def health():
#     return HealthResponse(status="ok", service="tech-genius-api")


# @app.get("/health/database", response_model=HealthDatabaseResponse, tags=["Health"])
# def health_database():
#     try:
#         with engine.connect() as conn:
#             conn.execute(text("SELECT 1"))
#         return HealthDatabaseResponse(status="ok", service="tech-genius-api", database="connected")
#     except Exception:
#         return HealthDatabaseResponse(status="degraded", service="tech-genius-api", database="disconnected")
