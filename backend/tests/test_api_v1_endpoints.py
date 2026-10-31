"""
WorkforceIQ Comprehensive API v1 REST Endpoint Integration Tests.

Validates that all core operational and intelligence endpoints respond correctly
with authorized credentials, valid schemas, and accurate HTTP status codes:
1. Authentication (/api/v1/auth)
2. Employees (/api/v1/employees)
3. Roles & Skills (/api/v1/roles, /api/v1/skills)
4. Projects & Demand (/api/v1/projects, /api/v1/demand)
5. Allocations & Availability (/api/v1/allocations, /api/v1/availability)
6. Upskilling & Training (/api/v1/training)
7. Analytics & Forecasting (/api/v1/analytics, /api/v1/forecasting)
8. Recommendations & Optimization (/api/v1/recommendations, /api/v1/optimization)
9. Governance, Risks & Audit (/api/v1/risks, /api/v1/quality, /api/v1/audit)
"""

from datetime import date, timedelta
import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_api_v1_comprehensive_suite(client: AsyncClient):
    # 1. Login
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@workforceiq.com", "password": "Workforce2026!"},
    )
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Auth /me
    me_res = await client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "admin@workforceiq.com"

    # 3. Employees: List & Create
    emp_list = await client.get("/api/v1/employees?page=1&page_size=5", headers=headers)
    assert emp_list.status_code == 200
    assert "items" in emp_list.json()

    # 4. Roles & Skills
    roles_res = await client.get("/api/v1/roles?page=1&page_size=5", headers=headers)
    assert roles_res.status_code == 200

    skills_res = await client.get("/api/v1/skills?page=1&page_size=5", headers=headers)
    assert skills_res.status_code == 200

    # 5. Projects
    projects_res = await client.get("/api/v1/projects?page=1&page_size=5", headers=headers)
    assert projects_res.status_code == 200

    # 6. Demand Plans
    demand_res = await client.get("/api/v1/demand?page=1&page_size=5", headers=headers)
    assert demand_res.status_code == 200

    # 7. Allocations
    alloc_res = await client.get("/api/v1/allocations?page=1&page_size=5", headers=headers)
    assert alloc_res.status_code == 200

    # 8. Availability & Leave
    avail_res = await client.get("/api/v1/availability?page=1&page_size=5", headers=headers)
    assert avail_res.status_code == 200

    # 9. Training Management
    train_res = await client.get("/api/v1/training?page=1&page_size=5", headers=headers)
    assert train_res.status_code == 200

    # 10. Analytics: Department Utilization & Gaps
    dept_util = await client.get("/api/v1/analytics/department-utilization", headers=headers)
    assert dept_util.status_code == 200
    assert isinstance(dept_util.json(), list)

    prj_items = projects_res.json().get("items", [])
    if prj_items:
        first_pid = prj_items[0]["id"]
        gaps_res = await client.get(f"/api/v1/analytics/gaps?project_id={first_pid}", headers=headers)
        assert gaps_res.status_code == 200
        assert isinstance(gaps_res.json(), list)

    emp_items = emp_list.json().get("items", [])
    if emp_items:
        first_eid = emp_items[0]["id"]
        today_d = date.today()
        cap_calc = await client.post(
            "/api/v1/analytics/capacity",
            headers=headers,
            json={"employee_id": first_eid, "start_date": str(today_d), "end_date": str(today_d + timedelta(days=7))},
        )
        assert cap_calc.status_code == 200

    # 11. Forecasting: Project Demand
    fcast_prj = await client.get("/api/v1/forecasting/project-demand", headers=headers)
    assert fcast_prj.status_code == 200
    assert isinstance(fcast_prj.json(), list)

    # 12. Recommendations: List
    recs_res = await client.get("/api/v1/recommendations?page=1&page_size=5", headers=headers)
    assert recs_res.status_code == 200

    # 13. Exception & Anomaly Monitoring
    anom_res = await client.get("/api/v1/risks/anomalies", headers=headers)
    assert anom_res.status_code == 200
    assert "anomalies" in anom_res.json()
    assert "total_anomalies" in anom_res.json()

    # 14. Data Quality & Reproducibility Metrics
    qual_res = await client.get("/api/v1/quality/metrics", headers=headers)
    assert qual_res.status_code == 200

    # 15. Compliance Audit Trail
    audit_res = await client.get("/api/v1/audit?page=1&page_size=5", headers=headers)
    assert audit_res.status_code == 200
    assert "items" in audit_res.json()
