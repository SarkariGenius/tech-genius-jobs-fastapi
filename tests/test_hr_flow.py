from tests.conftest import register_student, register_hr, auth_headers


def test_full_hr_flow(client):
    student_resp = register_student(client, email="hr_student@example.com")
    student_headers = auth_headers(student_resp)

    client.put("/api/v1/candidates/me/skills", headers=student_headers, json={
        "skills": [
            {"name": "Python", "proficiency": "ADVANCED", "years_of_experience": 2},
            {"name": "FastAPI", "proficiency": "INTERMEDIATE", "years_of_experience": 1},
            {"name": "SQL", "proficiency": "INTERMEDIATE", "years_of_experience": 1},
        ]
    })
    client.patch("/api/v1/candidates/me", headers=student_headers, json={
        "headline": "Python Developer",
        "current_city": "Indore",
        "total_experience_years": 2,
    })

    hr_resp = register_hr(client, email="hr_flow@example.com", company_name="Flow Corp")
    hr_headers = auth_headers(hr_resp)

    company = client.get("/api/v1/hr/company", headers=hr_headers)
    assert company.status_code == 200
    assert company.json()["name"] == "Flow Corp"

    job = client.post("/api/v1/hr/jobs", headers=hr_headers, json={
        "title": "Python Developer",
        "description": "Looking for a Python developer",
        "location": "Indore",
        "city": "Indore",
        "experience_min": 1,
        "experience_max": 3,
        "salary_min": 400000,
        "salary_max": 700000,
        "job_type": "FULL_TIME",
        "work_mode": "HYBRID",
        "education_requirement": "B.Tech",
        "notice_period_requirement": 30,
        "skills": [
            {"name": "Python", "required": True, "minimum_years": 1},
            {"name": "FastAPI", "required": True, "minimum_years": 1},
            {"name": "SQL", "required": True, "minimum_years": 1},
        ],
    })
    assert job.status_code == 201
    job_id = job.json()["id"]

    jobs = client.get("/api/v1/hr/jobs", headers=hr_headers)
    assert jobs.status_code == 200
    assert len(jobs.json()["items"]) >= 1

    candidates = client.get("/api/v1/hr/candidates", headers=hr_headers, params={"city": "Indore"})
    assert candidates.status_code == 200
    assert candidates.json()["total"] >= 1

    match = client.post("/api/v1/matching/candidates", headers=hr_headers, json={
        "title": "Python Developer",
        "skills": ["Python", "FastAPI", "SQL"],
        "experience_min": 1,
        "experience_max": 3,
        "location": "Indore",
        "work_mode": "HYBRID",
    })
    assert match.status_code == 200
    assert len(match.json()["items"]) >= 1
    assert match.json()["items"][0]["match_score"] > 0

    top = client.get("/api/v1/hr/top-candidates", headers=hr_headers, params={"job_id": job_id})
    assert top.status_code == 200
    assert len(top.json()["items"]) >= 1

    candidate_id = candidates.json()["items"][0]["id"]

    view = client.post(f"/api/v1/candidates/{candidate_id}/profile-view", headers=hr_headers)
    assert view.status_code == 200
    assert view.json()["recorded"] == True
    assert view.json()["profile_view_count"] >= 1

    shortlist = client.post(f"/api/v1/hr/candidates/{candidate_id}/shortlist", headers=hr_headers, json={"job_id": job_id})
    assert shortlist.status_code == 200
    assert shortlist.json()["status"] == "SHORTLISTED"

    shortlisted = client.get("/api/v1/hr/shortlisted", headers=hr_headers)
    assert shortlisted.status_code == 200
    assert shortlisted.json()["total"] >= 1

    dashboard = client.get("/api/v1/hr/dashboard", headers=hr_headers)
    assert dashboard.status_code == 200
    assert dashboard.json()["active_jobs"] >= 1

    notifs = client.get("/api/v1/notifications", headers=student_headers)
    assert notifs.status_code == 200
    assert notifs.json()["total"] >= 2

    apply = client.post(f"/api/v1/jobs/{job_id}/apply", headers=student_headers, json={})
    assert apply.status_code == 201
    application_id = apply.json()["id"]

    applicants = client.get(f"/api/v1/hr/jobs/{job_id}/applicants", headers=hr_headers)
    assert applicants.status_code == 200
    assert applicants.json()["total"] >= 1

    status_update = client.patch(f"/api/v1/hr/applications/{application_id}/status", headers=hr_headers, json={"status": "SHORTLISTED"})
    assert status_update.status_code == 200
    assert status_update.json()["status"] == "SHORTLISTED"

    my_apps = client.get("/api/v1/candidates/me/applications", headers=student_headers)
    assert my_apps.status_code == 200
    assert my_apps.json()["total"] >= 1

    dup = client.post(f"/api/v1/jobs/{job_id}/apply", headers=student_headers, json={})
    assert dup.status_code == 409

    saved = client.post(f"/api/v1/candidates/me/saved-jobs/{job_id}", headers=student_headers)
    assert saved.status_code == 201

    saved_list = client.get("/api/v1/candidates/me/saved-jobs", headers=student_headers)
    assert saved_list.status_code == 200
    assert saved_list.json()["total"] >= 1

    unsaved = client.delete(f"/api/v1/candidates/me/saved-jobs/{job_id}", headers=student_headers)
    assert unsaved.status_code == 204
