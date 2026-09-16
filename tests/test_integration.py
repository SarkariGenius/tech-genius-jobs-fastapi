"""
End-to-end integration test covering the full Tech Genius flow:

1. Candidate registers and creates profile
2. Candidate adds Python, FastAPI, SQL skills
3. HR registers and creates a Python Developer job
4. Matching returns the candidate
5. HR opens candidate profile - view recorded
6. HR shortlists candidate - notification created
7. Candidate applies to job
8. HR sees applicant and changes status
9. Candidate receives notification
"""
from tests.conftest import register_student, register_hr, auth_headers


def test_full_integration_flow(client):
    # 1. Candidate registers
    student_resp = register_student(client, email="integration.student@example.com")
    assert student_resp.status_code == 200
    student_headers = auth_headers(student_resp)
    candidate_user_id = student_resp.json()["user"]["id"]

    # 2. Candidate creates profile
    client.patch("/api/v1/candidates/me", headers=student_headers, json={
        "headline": "Python Developer",
        "bio": "Backend developer from Indore",
        "current_city": "Indore",
        "experience_level": "JUNIOR",
        "total_experience_years": 2,
        "expected_salary_min": 400000,
        "expected_salary_max": 700000,
        "notice_period_days": 30,
    })

    client.post("/api/v1/candidates/me/education", headers=student_headers, json={
        "degree": "B.Tech",
        "field_of_study": "Computer Science",
        "college": "IIT Indore",
        "graduation_year": 2023,
        "cgpa": 8.5,
    })

    client.post("/api/v1/candidates/me/experience", headers=student_headers, json={
        "company_name": "Startup Inc",
        "job_title": "Backend Developer",
        "start_date": "2023-01-01",
        "is_current": True,
    })

    # Add skills: Python, FastAPI, SQL
    skills_resp = client.put("/api/v1/candidates/me/skills", headers=student_headers, json={
        "skills": [
            {"name": "Python", "proficiency": "ADVANCED", "years_of_experience": 2},
            {"name": "FastAPI", "proficiency": "INTERMEDIATE", "years_of_experience": 1},
            {"name": "SQL", "proficiency": "INTERMEDIATE", "years_of_experience": 1},
        ]
    })
    assert skills_resp.status_code == 200
    assert len(skills_resp.json()) == 3

    # 3. HR registers and creates job
    hr_resp = register_hr(client, email="integration.hr@example.com", company_name="Integration Corp")
    assert hr_resp.status_code == 200
    hr_headers = auth_headers(hr_resp)

    job_resp = client.post("/api/v1/hr/jobs", headers=hr_headers, json={
        "title": "Python Developer",
        "description": "We need a Python developer with FastAPI experience",
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
    assert job_resp.status_code == 201
    job_id = job_resp.json()["id"]

    # 4. Matching returns the candidate
    match_resp = client.post("/api/v1/matching/candidates", headers=hr_headers, json={
        "title": "Python Developer",
        "skills": ["Python", "FastAPI", "SQL"],
        "experience_min": 1,
        "experience_max": 3,
        "location": "Indore",
        "work_mode": "HYBRID",
    })
    assert match_resp.status_code == 200
    match_items = match_resp.json()["items"]
    assert len(match_items) >= 1

    found = False
    for item in match_items:
        if item["candidate"]["full_name"] == "Test Student":
            found = True
            assert item["match_score"] > 0
            assert "Python" in item["matched_skills"]
            assert "FastAPI" in item["matched_skills"]
            assert "SQL" in item["matched_skills"]
    assert found, "Candidate should appear in matching results"

    # 5. HR opens candidate profile - view recorded
    candidate_id = None
    for item in match_items:
        if item["candidate"]["full_name"] == "Test Student":
            candidate_id = item["candidate"]["id"]
            break

    view_resp = client.post(f"/api/v1/candidates/{candidate_id}/profile-view", headers=hr_headers)
    assert view_resp.status_code == 200
    assert view_resp.json()["recorded"] == True
    assert view_resp.json()["profile_view_count"] >= 1

    # Duplicate view within dedup window should not record
    dup_view = client.post(f"/api/v1/candidates/{candidate_id}/profile-view", headers=hr_headers)
    assert dup_view.json()["recorded"] == False

    # 6. HR shortlists candidate
    shortlist_resp = client.post(f"/api/v1/hr/candidates/{candidate_id}/shortlist", headers=hr_headers, json={"job_id": job_id})
    assert shortlist_resp.status_code == 200
    assert shortlist_resp.json()["status"] == "SHORTLISTED"

    # 7. Candidate applies to job
    apply_resp = client.post(f"/api/v1/jobs/{job_id}/apply", headers=student_headers, json={})
    assert apply_resp.status_code == 201
    application_id = apply_resp.json()["id"]
    assert apply_resp.json()["status"] == "APPLIED"

    # 8. HR sees applicant
    applicants_resp = client.get(f"/api/v1/hr/jobs/{job_id}/applicants", headers=hr_headers)
    assert applicants_resp.status_code == 200
    assert applicants_resp.json()["total"] >= 1

    # HR changes application status
    status_resp = client.patch(f"/api/v1/hr/applications/{application_id}/status", headers=hr_headers, json={"status": "INTERVIEW"})
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "INTERVIEW"

    # 9. Candidate receives notifications
    notif_resp = client.get("/api/v1/notifications", headers=student_headers)
    assert notif_resp.status_code == 200
    notifs = notif_resp.json()["items"]
    assert len(notifs) >= 2

    types = [n["type"] for n in notifs]
    assert "PROFILE_VIEWED" in types
    assert "SHORTLISTED" in types

    # Candidate sees profile views
    views_resp = client.get("/api/v1/candidates/me/profile-views", headers=student_headers)
    assert views_resp.status_code == 200
    assert views_resp.json()["total_views"] >= 1

    # Candidate sees activity
    activity_resp = client.get("/api/v1/candidates/me/activity", headers=student_headers)
    assert activity_resp.status_code == 200
    assert len(activity_resp.json()["items"]) >= 1

    # Candidate sees shortlisted
    shortlisted_resp = client.get("/api/v1/candidates/me/shortlisted", headers=student_headers)
    assert shortlisted_resp.status_code == 200

    # HR recently viewed
    recent_resp = client.get("/api/v1/hr/activity/recently-viewed", headers=hr_headers)
    assert recent_resp.status_code == 200
    assert len(recent_resp.json()["items"]) >= 1

    # Mark notifications as read
    unread = client.get("/api/v1/notifications/unread-count", headers=student_headers)
    assert unread.status_code == 200
    assert unread.json()["unread_count"] >= 2

    read_all = client.patch("/api/v1/notifications/read-all", headers=student_headers)
    assert read_all.status_code == 200

    unread_after = client.get("/api/v1/notifications/unread-count", headers=student_headers)
    assert unread_after.json()["unread_count"] == 0
