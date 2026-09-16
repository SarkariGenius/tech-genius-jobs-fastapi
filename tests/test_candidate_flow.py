from tests.conftest import register_student, auth_headers


def test_full_candidate_flow(client):
    resp = register_student(client, email="candidate@example.com")
    headers = auth_headers(resp)

    profile = client.get("/api/v1/candidates/me", headers=headers)
    assert profile.status_code == 200
    assert profile.json()["email"] == "candidate@example.com"

    updated = client.patch("/api/v1/candidates/me", headers=headers, json={
        "headline": "Python Developer",
        "bio": "Passionate developer",
        "current_city": "Indore",
        "total_experience_years": 2,
        "expected_salary_min": 400000,
        "expected_salary_max": 700000,
        "notice_period_days": 30,
    })
    assert updated.status_code == 200
    assert updated.json()["headline"] == "Python Developer"

    skills = client.put("/api/v1/candidates/me/skills", headers=headers, json={
        "skills": [
            {"name": "Python", "proficiency": "ADVANCED", "years_of_experience": 2},
            {"name": "FastAPI", "proficiency": "INTERMEDIATE", "years_of_experience": 1},
            {"name": "SQL", "proficiency": "INTERMEDIATE", "years_of_experience": 1},
        ]
    })
    assert skills.status_code == 200
    assert len(skills.json()) == 3

    edu = client.post("/api/v1/candidates/me/education", headers=headers, json={
        "degree": "B.Tech",
        "field_of_study": "Computer Science",
        "college": "IIT Indore",
        "university": "IIT",
        "graduation_year": 2023,
        "cgpa": 8.5,
    })
    assert edu.status_code == 201
    assert edu.json()["degree"] == "B.Tech"

    exp = client.post("/api/v1/candidates/me/experience", headers=headers, json={
        "company_name": "Tech Corp",
        "job_title": "Junior Developer",
        "start_date": "2023-06-01",
        "is_current": True,
        "description": "Backend development",
    })
    assert exp.status_code == 201
    assert exp.json()["company_name"] == "Tech Corp"

    proj = client.post("/api/v1/candidates/me/projects", headers=headers, json={
        "name": "Job Portal",
        "description": "A recruitment platform",
        "technologies": ["Python", "FastAPI", "PostgreSQL"],
        "project_url": "https://github.com/example/job-portal",
    })
    assert proj.status_code == 201
    assert proj.json()["name"] == "Job Portal"

    prefs = client.patch("/api/v1/candidates/me/preferences", headers=headers, json={
        "preferred_roles": ["Backend Developer", "Full Stack Developer"],
        "preferred_locations": ["Indore", "Pune"],
        "preferred_job_types": ["FULL_TIME"],
        "preferred_work_modes": ["HYBRID", "REMOTE"],
        "minimum_salary": 400000,
        "maximum_salary": 800000,
    })
    assert prefs.status_code == 200
    assert "Indore" in prefs.json()["preferred_locations"]

    completion = client.get("/api/v1/candidates/me/profile-completion", headers=headers)
    assert completion.status_code == 200
    assert completion.json()["completion_percentage"] > 0

    dashboard = client.get("/api/v1/candidates/me/dashboard", headers=headers)
    assert dashboard.status_code == 200
    assert "profile_completion" in dashboard.json()


def test_skill_normalization(client):
    resp = register_student(client, email="norm@example.com")
    headers = auth_headers(resp)

    client.put("/api/v1/candidates/me/skills", headers=headers, json={
        "skills": [{"name": "Python", "proficiency": "ADVANCED"}]
    })
    client.put("/api/v1/candidates/me/skills", headers=headers, json={
        "skills": [{"name": "python", "proficiency": "ADVANCED"}]
    })
    skills = client.get("/api/v1/candidates/me/skills", headers=headers)
    assert len(skills.json()) == 1
