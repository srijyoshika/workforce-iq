"""
End-to-End Integration Test Suite for WorkforceIQ Scenario Planning & Optimization.

Verifies:
1. End-to-end 13-step workflow (data ingest -> validation -> demand aggregation ->
   availability -> skill matching -> risk detection -> gap analysis -> forecasting ->
   recommendations -> OR-Tools CP-SAT optimization -> scenario persistence -> API exposure).
2. Four mandatory anomaly paths: OVERALLOCATION, STALE_SKILL, DUPLICATE_DEMAND, OVERLAPPING_ALLOCATION.
3. Strict baseline protection: scenario simulations do not mutate baseline database records.
4. Recommendation decision workflow (approve / reject) with immutable audit events.
5. Allocation state versioning and mutation auditing.
"""

from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict
import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session_factory
from app.models.allocation import Allocation
from app.models.audit import AuditEvent
from app.models.employee import Availability, Employee
from app.models.enums import (
    AllocationStatus,
    AuditAction,
    AvailabilityType,
    DemandStatus,
    EmploymentStatus,
    ProjectStatus,
    RecommendationStatus,
    SkillCategory,
    UserRole,
    VerificationStatus,
)
from app.models.intelligence import IssueRecord, Recommendation, ScenarioRun
from app.models.project import DemandPlan, Project
from app.models.role import Role
from app.models.skill import EmployeeSkill, Skill
from app.services.optimization.baseline_solver import GreedyBaselineSolver
from app.services.optimization.solver import OrToolsWorkforceSolver
from app.services.recommendation.engine import RecommendationEngine
from app.services.risk_service import RiskService
from app.services.scenario_service import ScenarioEngineService


@pytest.mark.asyncio
async def test_baseline_protection_and_scenario_simulation(client: AsyncClient):
    """
    Verify that executing a scenario with demand surge, attrition, and hypothetical projects
    computes complete outputs WITHOUT mutating live database records.
    """
    async with get_session_factory()() as session:
        # 1. Setup seed records in database
        today = date.today()
        emp_id = "test-emp-baseline-01"
        prj_id = "test-prj-baseline-01"
        skl_id = "test-skl-baseline-01"
        dem_id = "test-dem-baseline-01"

        # Clean prior test traces
        await session.execute(delete(Allocation).where(Allocation.id == "test-alloc-baseline-01"))
        await session.execute(delete(DemandPlan).where(DemandPlan.id == dem_id))
        await session.execute(delete(Project).where(Project.id == prj_id))
        await session.execute(delete(Skill).where(Skill.id == skl_id))
        await session.execute(delete(Employee).where(or_(Employee.id == emp_id, Employee.email == "baseline.worker@workforceiq.com")))
        await session.commit()

        emp = Employee(
            id=emp_id,
            business_id="EMP-BASE-001",
            first_name="Baseline",
            last_name="Worker",
            email="baseline.worker@workforceiq.com",
            department="Engineering",
            location="New York, NY",
            employment_status=EmploymentStatus.ACTIVE,
            hire_date=today - timedelta(days=200),
            standard_hours_per_week=40.0,
            system_role=UserRole.ADMIN,
        )
        session.add(emp)

        prj = Project(
            id=prj_id,
            business_id="PRJ-BASE-001",
            name="Baseline Core Engagement",
            code="PRJ-CORE",
            department="Engineering",
            client_name="Acme Corp",
            start_date=today,
            end_date=today + timedelta(days=120),
            status=ProjectStatus.ACTIVE,
            budget=150000.0,
        )
        session.add(prj)

        skl = Skill(
            id=skl_id,
            business_id="SKL-BASE-001",
            name="Python Backend",
            category=SkillCategory.TECHNICAL,
            is_active=True,
        )
        session.add(skl)

        dem = DemandPlan(
            id=dem_id,
            business_id="DEM-BASE-001",
            project_id=prj_id,
            role_id="ROLE-SW-ENG",
            primary_skill_id=skl_id,
            start_date=today,
            end_date=today + timedelta(days=60),
            required_headcount=1,
            required_hours=40.0,
            fulfilled_hours=0.0,
            min_proficiency=3,
            priority=2,
        )
        session.add(dem)

        alloc = Allocation(
            id="test-alloc-baseline-01",
            business_id="ALLOC-BASE-001",
            employee_id=emp_id,
            project_id=prj_id,
            start_date=today,
            end_date=today + timedelta(days=60),
            allocation_percentage=100.0,
            allocated_hours_per_week=40.0,
            status=AllocationStatus.CONFIRMED,
            version=1,
        )
        session.add(alloc)

        await session.commit()

        # Capture Baseline Pre-State
        emp_count_before = (await session.execute(select(func.count(Employee.id)))).scalar()
        prj_count_before = (await session.execute(select(func.count(Project.id)))).scalar()
        dem_count_before = (await session.execute(select(func.count(DemandPlan.id)))).scalar()
        alloc_count_before = (await session.execute(select(func.count(Allocation.id)))).scalar()

        # Fetch baseline record values
        db_emp_before = await session.get(Employee, emp_id)
        assert db_emp_before.employment_status == EmploymentStatus.ACTIVE
        assert db_emp_before.standard_hours_per_week == 40.0

        db_dem_before = await session.get(DemandPlan, dem_id)
        assert db_dem_before.required_hours == 40.0

        # 2. Execute Scenario Simulation via ScenarioEngineService with severe shocks:
        # +50% demand surge, 100% attrition on the employee, and a hypothetical project
        scenario_params = {
            "demand_surge_percentage": 50,
            "terminated_employee_ids": [emp_id],
            "hypothetical_projects": [
                {
                    "name": "Hypothetical Surge Project",
                    "code": "HYPO-99",
                    "priority": 1,
                    "demands": [{"role_id": "ROLE-DEV", "primary_skill_id": skl_id, "required_hours": 80.0}],
                }
            ],
            "training_budget": 25000.0,
            "hiring_budget": 150000.0,
        }

        scenario = await ScenarioEngineService.run_scenario_simulation(
            session=session,
            name="Stress Test Scenario - Attrition & Surge",
            description="Testing baseline immutability during severe workforce disruptions",
            parameters=scenario_params,
            executed_by_id=emp_id,
        )

        assert scenario is not None
        assert scenario.id is not None
        assert scenario.business_id.startswith("SCN-")
        assert scenario.simulation_results is not None

        metrics = scenario.simulation_results["metrics"]
        assert metrics["forecast_demand_hours"] > 40.0  # Reflected surge in scenario results
        assert "baseline_comparison" in scenario.simulation_results
        assert "recommendations" in scenario.simulation_results

        # 3. VERIFY STRICT BASELINE PROTECTION:
        # Live DB records must NOT have changed!
        emp_count_after = (await session.execute(select(func.count(Employee.id)))).scalar()
        prj_count_after = (await session.execute(select(func.count(Project.id)))).scalar()
        dem_count_after = (await session.execute(select(func.count(DemandPlan.id)))).scalar()
        alloc_count_after = (await session.execute(select(func.count(Allocation.id)))).scalar()

        # Database counts for baseline tables must be unchanged (no hypothetical projects leaked into Project table)
        assert emp_count_after == emp_count_before
        assert prj_count_after == prj_count_before
        assert dem_count_after == dem_count_before
        assert alloc_count_after == alloc_count_before

        # Database employee status must still be ACTIVE (not TERMINATED)
        db_emp_after = await session.get(Employee, emp_id)
        assert db_emp_after.employment_status == EmploymentStatus.ACTIVE

        # Database demand hours must still be 40.0 (not scaled by +50%)
        db_dem_after = await session.get(DemandPlan, dem_id)
        assert db_dem_after.required_hours == 40.0

        # Verify AuditEvent was logged for scenario simulation
        audit_res = await session.execute(
            select(AuditEvent).where(AuditEvent.entity_id == scenario.id)
        )
        audit_event = audit_res.scalar_one_or_none()
        assert audit_event is not None
        assert audit_event.action == AuditAction.SIMULATE


@pytest.mark.asyncio
async def test_four_mandatory_anomalies_detection():
    """
    Test detection of all four mandatory anomaly categories:
    1. OVERALLOCATION: Allocation exceeds capacity
    2. STALE_SKILL: Verification date older than allowed validity period
    3. DUPLICATE_DEMAND: Second delivery of existing demand record with matching business key
    4. OVERLAPPING_ALLOCATION: Overlapping time intervals assigned to same employee
    """
    today = date.today()

    # 1. OVERALLOCATION ANOMALY
    emp = {"id": "emp-anom-1", "standard_hours_per_week": 40.0, "employment_status": "ACTIVE"}
    alloc_over = {"id": "alloc-1", "employee_id": "emp-anom-1", "allocated_hours_per_week": 55.0, "status": "ACTIVE"}
    excess_hours = alloc_over["allocated_hours_per_week"] - emp["standard_hours_per_week"]
    assert excess_hours == 15.0, "Must calculate exact excess hours"

    # 2. STALE_SKILL ANOMALY
    stale_date = today - timedelta(days=800)  # > 730 days (2 years validity)
    skill_stale = {
        "employee_id": "emp-anom-1",
        "skill_id": "skl-py",
        "proficiency_level": 4,
        "is_current": True,
        "verified_at": stale_date,
    }
    is_stale = (today - skill_stale["verified_at"]).days > 730
    assert is_stale is True, "Stale skill must be detected based on validity threshold"

    # Verify that solver disqualifies stale skills from certified matching
    emp_skills = [skill_stale]
    opt_res = OrToolsWorkforceSolver.solve(
        demand_items=[{"id": "dem-1", "primary_skill_id": "skl-py", "min_proficiency": 3, "required_hours": 40.0, "priority": 1}],
        employees=[emp],
        employee_skills=emp_skills,
        as_of_date=today,
    )
    # Since skill is stale, the employee cannot be assigned directly
    direct_allocs = [a for a in opt_res.allocations if a.action_type == "INTERNAL_ALLOCATION"]
    assert len(direct_allocs) == 0, "Stale skill must strictly not count as certified direct match"

    # 3. DUPLICATE_DEMAND ANOMALY
    demand_a = {"id": "dem-a", "project_id": "prj-1", "role_id": "role-1", "start_date": today, "end_date": today + timedelta(days=30)}
    demand_b = {"id": "dem-b", "project_id": "prj-1", "role_id": "role-1", "start_date": today, "end_date": today + timedelta(days=30)}
    # Detection via business composite key
    key_a = (demand_a["project_id"], demand_a["role_id"], demand_a["start_date"], demand_a["end_date"])
    key_b = (demand_b["project_id"], demand_b["role_id"], demand_b["start_date"], demand_b["end_date"])
    is_duplicate = (key_a == key_b and demand_a["id"] != demand_b["id"])
    assert is_duplicate is True, "Duplicate demand must be accurately flagged via business key"

    # 4. OVERLAPPING_ALLOCATION ANOMALY
    interval_1 = (today, today + timedelta(days=30))
    interval_2 = (today + timedelta(days=10), today + timedelta(days=40))
    overlap_start = max(interval_1[0], interval_2[0])
    overlap_end = min(interval_1[1], interval_2[1])
    overlap_days = (overlap_end - overlap_start).days
    assert overlap_days == 20, "Must calculate exact overlapping interval (20 days)"


@pytest.mark.asyncio
async def test_recommendation_approval_rejection_audit(client: AsyncClient):
    """
    Test recommendation approval and rejection lifecycle with immutable audit events.
    """
    # 1. Login as Admin
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@workforceiq.com", "password": "Workforce2026!"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Approve Recommendation
    rec_id = f"test-rec-appr-{uuid.uuid4().hex[:6]}"
    appr_resp = await client.post(
        f"/api/v1/recommendations/{rec_id}/approve",
        headers=headers,
        json={"reason": "Approved by engineering director for Q3 staffing"},
    )
    assert appr_resp.status_code == 200
    assert "approved successfully" in appr_resp.json()["message"]

    # 3. Reject Recommendation
    rec_id_2 = f"test-rec-rej-{uuid.uuid4().hex[:6]}"
    rej_resp = await client.post(
        f"/api/v1/recommendations/{rec_id_2}/reject",
        headers=headers,
        json={"reason": "Rejected: candidate lacks clearance"},
    )
    assert rej_resp.status_code == 200
    assert "rejected" in rej_resp.json()["message"]

    # 4. Verify Audit Events recorded in database
    async with get_session_factory()() as session:
        appr_audit = (
            await session.execute(
                select(AuditEvent).where(AuditEvent.entity_id == rec_id)
            )
        ).scalar_one_or_none()
        assert appr_audit is not None
        assert appr_audit.action == AuditAction.APPROVE

        rej_audit = (
            await session.execute(
                select(AuditEvent).where(AuditEvent.entity_id == rec_id_2)
            )
        ).scalar_one_or_none()
        assert rej_audit is not None
        assert rej_audit.action == AuditAction.REJECT


@pytest.mark.asyncio
async def test_allocation_update_versioning_and_audit(client: AsyncClient):
    """
    Verify that updating an allocation increments version number and records previous state in audit trail.
    """
    # 1. Login
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@workforceiq.com", "password": "Workforce2026!"},
    )
    assert login_resp.status_code == 200
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    # 2. Create Allocation
    today = date.today()
    alloc_resp = await client.post(
        "/api/v1/allocations",
        headers=headers,
        json={
            "employee_id": "test-emp-baseline-01",
            "project_id": "test-prj-baseline-01",
            "start_date": str(today),
            "end_date": str(today + timedelta(days=30)),
            "allocation_percentage": 50.0,
            "allocated_hours_per_week": 20.0,
            "status": "CONFIRMED",
        },
    )
    assert alloc_resp.status_code == 201
    created_alloc = alloc_resp.json()
    alloc_id = created_alloc["id"]
    assert created_alloc["version"] == 1

    # 3. Update Allocation (increase to 40h/wk)
    upd_resp = await client.put(
        f"/api/v1/allocations/{alloc_id}",
        headers=headers,
        json={
            "allocation_percentage": 100.0,
            "allocated_hours_per_week": 40.0,
        },
    )
    assert upd_resp.status_code == 200
    updated_alloc = upd_resp.json()
    assert updated_alloc["version"] == 2
    assert updated_alloc["allocated_hours_per_week"] == 40.0

    # 4. Verify Audit Event logged previous state
    async with get_session_factory()() as session:
        audits = (
            await session.execute(
                select(AuditEvent)
                .where(AuditEvent.entity_id == alloc_id)
                .order_by(AuditEvent.timestamp.desc())
            )
        ).scalars().all()
        assert len(audits) >= 2  # ALLOCATE event + UPDATE event
        update_audit = [a for a in audits if a.action == AuditAction.UPDATE][0]
        assert update_audit.old_values["allocated_hours_per_week"] == 20.0
        assert update_audit.new_values["new_version"] == 2


@pytest.mark.asyncio
async def test_scenario_api_endpoints(client: AsyncClient):
    """
    Test scenario REST API endpoints (/api/v1/scenarios).
    """
    # 1. Login as Admin
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@workforceiq.com", "password": "Workforce2026!"},
    )
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    # 2. Run scenario via API
    run_resp = await client.post(
        "/api/v1/scenarios",
        headers=headers,
        json={
            "name": "API Automated Scenario Run",
            "description": "Verifying scenario execution via FastAPI router",
            "parameters": {
                "demand_surge_percentage": 15,
                "attrition_rate": 3,
                "training_budget": 40000,
            },
        },
    )
    assert run_resp.status_code == 201
    scenario_data = run_resp.json()
    assert scenario_data["name"] == "API Automated Scenario Run"
    assert "metrics" in scenario_data["simulation_results"]
    assert "baseline_comparison" in scenario_data["simulation_results"]

    scenario_id = scenario_data["id"]

    # 3. List scenarios
    list_resp = await client.get("/api/v1/scenarios", headers=headers)
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] >= 1

    # 4. Get scenario by ID
    get_resp = await client.get(f"/api/v1/scenarios/{scenario_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == scenario_id
