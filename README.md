# Tech Genius API

**Indore-first recruitment platform** connecting Students/Candidates, HR/Recruiters, Companies, and Jobs.

## 1. Tech Genius

Tech Genius is a recruitment platform built around the Indore tech ecosystem. It connects:

- **Students / Candidates** — create profiles, search jobs, apply, track applications
- **HR / Recruiters** — post jobs, search candidates, match, shortlist, manage applicants
- **Companies** — employer profiles with verification
- **Jobs** — searchable listings with skills, experience, salary, and location filters

## 2. Backend Architecture

```
tech-genius-backend/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── core/                # Config, database, security, dependencies, exceptions
│   ├── models/              # SQLAlchemy ORM models (18 tables)
│   ├── schemas/             # Pydantic v2 request/response schemas
│   ├── api/v1/              # Versioned API routers and endpoints
│   │   ├── router.py
│   │   └── endpoints/       # auth, candidates, hr, jobs, applications, etc.
│   ├── services/            # Business logic (matching engine, notifications, etc.)
│   ├── repositories/        # Database query layer
│   └── utils/
├── alembic/                 # Database migrations
├── tests/                   # pytest test suite
├── scripts/                 # Seed data script
├── .env.example
├── requirements.txt
├── alembic.ini
└── README.md
```

## 3. Technologies

| Technology | Purpose |
|---|---|
| Python 3.12+ | Runtime |
| FastAPI | Web framework |
| PostgreSQL | Database |
| SQLAlchemy 2.x | ORM |
| Alembic | Migrations |
| Pydantic v2 | Validation |
| pydantic-settings | Configuration |
| psycopg | PostgreSQL driver |
| python-jose | JWT |
| argon2-cffi | Password hashing |
| pytest | Testing |

## 4. PostgreSQL Setup

1. Install PostgreSQL 14+
2. Create a database:
   ```sql
   CREATE DATABASE tech_genius;
   CREATE USER techgenius WITH PASSWORD 'yourpassword';
   GRANT ALL PRIVILEGES ON DATABASE tech_genius TO techgenius;
   ```
3. Copy `.env.example` to `.env` and fill in your credentials:
   ```
   DATABASE_URL=postgresql+psycopg://techgenius:yourpassword@localhost:5432/tech_genius
   ```

## 5. Environment Variables

| Variable | Description | Default |
|---|---|---|
| `APP_NAME` | Application name | Tech Genius API |
| `APP_ENV` | Environment | development |
| `DATABASE_URL` | PostgreSQL connection string | — |
| `JWT_SECRET_KEY` | JWT signing secret | CHANGE_ME |
| `JWT_ALGORITHM` | JWT algorithm | HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL | 30 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL | 30 |
| `CORS_ORIGINS` | Comma-separated allowed origins | http://localhost:5173 |
| `PROFILE_VIEW_DEDUP_MINUTES` | Dedup window for profile views | 60 |

## 6. Alembic Migrations

```bash
# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# Create new migration (after model changes)
alembic revision --autogenerate -m "description"
```

## 7. Running the Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env from example
cp .env.example .env
# Edit .env with your PostgreSQL credentials

# Run migrations
alembic upgrade head

# (Optional) Seed demo data
python -m scripts.seed

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 8. API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health**: http://localhost:8000/health

API tags: Authentication, Candidates, HR, Jobs, Applications, Matching, Companies, Profile Views, Shortlists, Notifications, Admin

## 9. Authentication

- **Register Student**: `POST /api/v1/auth/register/student`
- **Register HR**: `POST /api/v1/auth/register/hr`
- **Login**: `POST /api/v1/auth/login`
- **Refresh**: `POST /api/v1/auth/refresh`
- **Logout**: `POST /api/v1/auth/logout`
- **Me**: `GET /api/v1/auth/me`

All protected endpoints require `Authorization: Bearer <access_token>` header.

Passwords are hashed with Argon2. JWT access tokens expire in 30 minutes; refresh tokens in 30 days.

## 10. Seed Data

```bash
python -m scripts.seed
```

Creates demo data (Indore-focused):
- 6 companies
- 4 HR accounts
- 10 candidates with skills, education, experience, projects, preferences
- 10 jobs with required skills
- Demo applications, profile views, and notifications

**Demo credentials:**
- Student: `aman@example.com` / `Password@123`
- HR: `rahul@techvision.com` / `Password@123`

## 11. Testing

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_integration.py -v

# Run with coverage
pytest --cov=app
```

Tests cover:
- Auth: registration, login, duplicate detection, password mismatch
- Candidate flow: profile, skills, education, experience, projects, preferences, dashboard
- HR flow: company, jobs, candidate search, matching, top candidates, profile views, shortlist, applicants, application status
- Integration: full end-to-end flow from registration through application status update and notifications

## 12. Frontend Integration

The API is designed to map directly to the frontend service layer:

| Frontend Service | API Endpoints |
|---|---|
| `authService` | `/api/v1/auth/*` |
| `candidateService` | `/api/v1/candidates/*` |
| `jobService` | `/api/v1/jobs/*` |
| `companyService` | `/api/v1/companies/*` |
| `applicationService` | `/api/v1/jobs/{job_id}/apply`, `/api/v1/candidates/me/applications`, `/api/v1/hr/jobs/{job_id}/applicants`, `/api/v1/hr/applications/{id}/status` |
| `profileViewService` | `/api/v1/candidates/{id}/profile-view`, `/api/v1/candidates/me/profile-views`, `/api/v1/hr/activity/recently-viewed` |
| `shortlistService` | `/api/v1/hr/candidates/{id}/shortlist`, `/api/v1/hr/shortlisted`, `/api/v1/candidates/me/shortlisted` |
| `notificationService` | `/api/v1/notifications/*` |
| `matchingService` | `/api/v1/matching/candidates`, `/api/v1/hr/top-candidates`, `/api/v1/candidates/me/recommended-jobs` |

To integrate: replace mock service implementations with HTTP calls to these endpoints. The response shapes match the frontend's expected data structures.

## 13. API Endpoint List

### Authentication
| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/auth/register/student` | Register a student |
| POST | `/api/v1/auth/register/hr` | Register an HR user |
| POST | `/api/v1/auth/login` | Login |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/auth/logout` | Logout |
| GET | `/api/v1/auth/me` | Get current user |

### Candidates
| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/candidates/me` | Get own profile |
| PATCH | `/api/v1/candidates/me` | Update profile |
| GET | `/api/v1/candidates/{id}` | Get candidate by ID |
| GET | `/api/v1/candidates/me/profile-completion` | Profile completion % |
| GET/PUT | `/api/v1/candidates/me/skills` | Get/update skills |
| GET/POST/PATCH/DELETE | `/api/v1/candidates/me/education` | Education CRUD |
| GET/POST/PATCH/DELETE | `/api/v1/candidates/me/experience` | Experience CRUD |
| GET/POST/PATCH/DELETE | `/api/v1/candidates/me/projects` | Projects CRUD |
| GET/PATCH | `/api/v1/candidates/me/preferences` | Job preferences |
| GET/POST/DELETE | `/api/v1/candidates/me/resume` | Resume metadata |
| GET | `/api/v1/candidates/me/profile-views` | Profile view history |
| GET | `/api/v1/candidates/me/activity` | Activity feed |
| GET | `/api/v1/candidates/me/dashboard` | Candidate dashboard |
| GET | `/api/v1/candidates/me/applications` | My applications |
| GET | `/api/v1/candidates/me/saved-jobs` | Saved jobs |
| GET | `/api/v1/candidates/me/recommended-jobs` | Recommended jobs |

### HR
| Method | Path | Description |
|---|---|---|
| GET/PATCH | `/api/v1/hr/company` | Company profile |
| GET/POST | `/api/v1/hr/jobs` | List/create jobs |
| GET/PATCH/DELETE | `/api/v1/hr/jobs/{id}` | Job CRUD |
| GET | `/api/v1/hr/jobs/{id}/applicants` | Job applicants |
| PATCH | `/api/v1/hr/applications/{id}/status` | Update application status |
| GET | `/api/v1/hr/candidates` | Search candidates |
| GET | `/api/v1/hr/top-candidates` | Top candidates by match |
| POST/DELETE | `/api/v1/hr/candidates/{id}/shortlist` | Shortlist candidate |
| GET | `/api/v1/hr/shortlisted` | Shortlisted candidates |
| GET | `/api/v1/hr/activity/recently-viewed` | Recently viewed |
| GET | `/api/v1/hr/dashboard` | HR dashboard |

### Jobs
| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/jobs` | Search jobs |
| GET | `/api/v1/jobs/{id}` | Get job details |
| POST | `/api/v1/jobs/{id}/apply` | Apply to job |

### Matching
| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/matching/candidates` | Match candidates to requirements |

### Companies
| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/companies` | List companies |
| GET | `/api/v1/companies/{id}` | Get company |

### Profile Views
| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/candidates/{id}/profile-view` | Record profile view |

### Notifications
| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/notifications` | List notifications |
| GET | `/api/v1/notifications/unread-count` | Unread count |
| PATCH | `/api/v1/notifications/{id}/read` | Mark read |
| PATCH | `/api/v1/notifications/read-all` | Mark all read |

### Admin
| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/admin/dashboard` | Admin dashboard |
| GET | `/api/v1/admin/statistics` | Platform statistics |
| GET | `/api/v1/admin/candidates` | All candidates |
| GET | `/api/v1/admin/hr` | All HR |
| GET | `/api/v1/admin/companies` | All companies |
| GET | `/api/v1/admin/jobs` | All jobs |
| GET | `/api/v1/admin/applications` | All applications |

### Matching Algorithm

The matching engine uses weighted scoring:

| Factor | Weight |
|---|---|
| Skills | 40% |
| Experience | 20% |
| Location | 15% |
| Education | 10% |
| Job Preference | 10% |
| Availability | 5% |

The engine is isolated in `app/services/matching_service.py` for future enhancement.
