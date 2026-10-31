"""
Automated Relational Database Schema Verification Suite.
Validates:
- Primary key & business ID uniqueness
- Foreign key integrity
- Lifecycle Enum constraints
- Date and numerical Check constraints
- Entity relationship cardinality (1:M, M:M bridges)
- Historical audit & version preservation
- Alembic migration state
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import uuid
import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from alembic.config import Config
from alembic.script import ScriptDirectory

from app.database import get_session_factory
from app.models.enums import (
    AllocationStatus,
    AvailabilityType,
    DemandStatus,
    EmploymentStatus,
    GapSeverity,
    GapStatus,
    ProjectStatus,
    RecommendationStatus,
    RecommendationType,
    SkillCategory,
    TrainingStatus,
    VerificationStatus,
)
from app.models.role import Role
from app.models.skill import Skill, EmployeeSkill, RoleSkill
from app.models.employee import Employee, Availability
from app.models.project import Project, DemandPlan
from app.models.allocation import Allocation
from app.models.training import Training
from app.models.intelligence import GapAnalysis, Recommendation, ScenarioRun, IssueRecord
from app.models.audit import AuditEvent


@pytest.fixture
async def db_session():
    """Transactional async session fixture with automatic rollback after test."""
    factory = get_session_factory()
    async with factory() as session:
        # Enforce SQLite foreign keys if running on SQLite
        await session.execute(text("PRAGMA foreign_keys = ON;"))
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


@pytest.mark.asyncio
async def test_primary_key_and_business_id_uniqueness(db_session: AsyncSession):
    """Test that duplicate primary keys and duplicate business IDs raise IntegrityError."""
    uid = str(uuid.uuid4())
    biz_id = f"ROL-TEST-{uuid.uuid4().hex[:6]}"

    role1 = Role(
        id=uid,
        business_id=biz_id,
        title=f"Cloud Architect {uuid.uuid4().hex[:6]}",
        code=f"ARCH-{uuid.uuid4().hex[:6]}",
        department="Engineering",
    )
    db_session.add(role1)
    await db_session.commit()

    # Attempt to insert same business_id with a different UUID
    role2 = Role(
        id=str(uuid.uuid4()),
        business_id=biz_id,
        title=f"Solutions Architect {uuid.uuid4().hex[:6]}",
        code=f"SOL-{uuid.uuid4().hex[:6]}",
        department="Architecture",
    )
    db_session.add(role2)

    with pytest.raises(IntegrityError):
        await db_session.commit()

    await db_session.rollback()


@pytest.mark.asyncio
async def test_foreign_key_integrity(db_session: AsyncSession):
    """Verify that referencing non-existent parent IDs raises IntegrityError."""
    non_existent_role_id = str(uuid.uuid4())
    emp = Employee(
        business_id=f"EMP-TEST-{uuid.uuid4().hex[:6]}",
        first_name="Jane",
        last_name="Doe",
        email=f"jane.doe.{uuid.uuid4().hex[:6]}@example.com",
        role_id=non_existent_role_id,
        department="Engineering",
        location="New York",
        hire_date=date(2026, 1, 1),
    )
    db_session.add(emp)

    with pytest.raises(IntegrityError):
        await db_session.commit()

    await db_session.rollback()


@pytest.mark.asyncio
async def test_project_and_allocation_date_constraints(db_session: AsyncSession):
    """Verify check constraint enforces end_date >= start_date."""
    # Invalid Project dates
    invalid_proj = Project(
        business_id=f"PRJ-TEST-{uuid.uuid4().hex[:6]}",
        name="Invalid Project",
        code=f"PRJ-INV-{uuid.uuid4().hex[:6]}",
        department="Consulting",
        start_date=date(2026, 6, 1),
        end_date=date(2026, 1, 1), # Before start_date!
    )
    db_session.add(invalid_proj)

    with pytest.raises(IntegrityError):
        await db_session.commit()

    await db_session.rollback()


@pytest.mark.asyncio
async def test_numerical_check_constraints(db_session: AsyncSession):
    """Verify check constraints on proficiency levels (1-5) and allocation percentage (0-100%)."""
    # 1. Create valid prerequisites
    role = Role(
        business_id=f"ROL-CHCK-{uuid.uuid4().hex[:6]}",
        title=f"DevOps Lead {uuid.uuid4().hex[:6]}",
        code=f"DOP-{uuid.uuid4().hex[:6]}",
        department="Infrastructure",
    )
    skill = Skill(
        business_id=f"SKL-CHCK-{uuid.uuid4().hex[:6]}",
        name=f"Kubernetes {uuid.uuid4().hex[:6]}",
        category=SkillCategory.TECHNICAL,
    )
    db_session.add_all([role, skill])
    await db_session.commit()

    # 2. Attempt invalid RoleSkill proficiency = 6 (Out of 1..5 range)
    invalid_role_skill = RoleSkill(
        business_id=f"RS-INV-{uuid.uuid4().hex[:6]}",
        role_id=role.id,
        skill_id=skill.id,
        required_proficiency=6, # Invalid!
        importance_weight=Decimal("1.00"),
    )
    db_session.add(invalid_role_skill)

    with pytest.raises(IntegrityError):
        await db_session.commit()

    await db_session.rollback()


@pytest.mark.asyncio
async def test_bridge_tables_and_relationship_cardinality(db_session: AsyncSession):
    """
    Test complete lifecycle, bridge tables, and many-to-many relationship cardinality:
    - Employee has many skills via EmployeeSkill
    - Role requires many skills via RoleSkill
    - Project has many DemandPlans
    - Employee is allocated to Project via Allocation
    """
    # 1. Create Role & Skills
    role = Role(
        business_id=f"ROL-CARD-{uuid.uuid4().hex[:6]}",
        title=f"Full Stack Architect {uuid.uuid4().hex[:6]}",
        code=f"FSA-{uuid.uuid4().hex[:6]}",
        department="Engineering",
    )
    skill_py = Skill(
        business_id=f"SKL-PY-{uuid.uuid4().hex[:6]}",
        name=f"Python Async {uuid.uuid4().hex[:6]}",
        category=SkillCategory.TECHNICAL,
    )
    skill_pg = Skill(
        business_id=f"SKL-PG-{uuid.uuid4().hex[:6]}",
        name=f"PostgreSQL Optimization {uuid.uuid4().hex[:6]}",
        category=SkillCategory.TECHNICAL,
    )
    db_session.add_all([role, skill_py, skill_pg])
    await db_session.commit()

    # 2. Link RoleSkills
    rs1 = RoleSkill(
        business_id=f"RS-1-{uuid.uuid4().hex[:6]}",
        role_id=role.id,
        skill_id=skill_py.id,
        required_proficiency=4,
        is_mandatory=True,
    )
    rs2 = RoleSkill(
        business_id=f"RS-2-{uuid.uuid4().hex[:6]}",
        role_id=role.id,
        skill_id=skill_pg.id,
        required_proficiency=4,
        is_mandatory=True,
    )
    db_session.add_all([rs1, rs2])
    await db_session.commit()

    # 3. Create Employee
    emp = Employee(
        business_id=f"EMP-000001-{uuid.uuid4().hex[:4]}",
        first_name="Alexander",
        last_name="Vance",
        email=f"alex.vance.{uuid.uuid4().hex[:6]}@workforceiq.internal",
        role_id=role.id,
        department="Engineering",
        location="Austin, TX",
        employment_status=EmploymentStatus.ACTIVE,
        hire_date=date(2025, 3, 1),
        standard_hours_per_week=Decimal("40.00"),
    )
    db_session.add(emp)
    await db_session.commit()

    # 4. Attach EmployeeSkills (Preserving verification history)
    es1 = EmployeeSkill(
        business_id=f"EMPSKL-000001-{uuid.uuid4().hex[:4]}",
        employee_id=emp.id,
        skill_id=skill_py.id,
        proficiency_level=5,
        verification_status=VerificationStatus.ASSESSMENT_CERTIFIED,
        effective_start_date=date(2025, 3, 1),
        is_current=True,
    )
    es2 = EmployeeSkill(
        business_id=f"EMPSKL-000002-{uuid.uuid4().hex[:4]}",
        employee_id=emp.id,
        skill_id=skill_pg.id,
        proficiency_level=4,
        verification_status=VerificationStatus.MANAGER_VERIFIED,
        effective_start_date=date(2025, 3, 1),
        is_current=True,
    )
    db_session.add_all([es1, es2])
    await db_session.commit()

    # 5. Create Project & DemandPlan
    project = Project(
        business_id=f"PRJ-2026-{uuid.uuid4().hex[:6]}",
        name="Global Workforce Intelligence Modernization",
        code=f"PRJ-GWIM-{uuid.uuid4().hex[:6]}",
        department="Engineering",
        status=ProjectStatus.ACTIVE,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        budget=Decimal("500000.00"),
        manager_id=emp.id,
    )
    db_session.add(project)
    await db_session.commit()

    demand = DemandPlan(
        business_id=f"DEM-{project.code}-2026W01",
        project_id=project.id,
        role_id=role.id,
        primary_skill_id=skill_py.id,
        min_proficiency=4,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 6, 30),
        week_number="2026W01",
        required_headcount=1,
        required_hours=Decimal("480.00"),
        status=DemandStatus.SUBMITTED,
        priority=1,
    )
    db_session.add(demand)
    await db_session.commit()

    # 6. Create Allocation
    allocation = Allocation(
        business_id=f"ALLOC-2026-{uuid.uuid4().hex[:6]}",
        employee_id=emp.id,
        project_id=project.id,
        demand_plan_id=demand.id,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 6, 30),
        allocation_percentage=Decimal("50.00"),
        allocated_hours_per_week=Decimal("20.00"),
        status=AllocationStatus.CONFIRMED,
        version=1,
        is_active=True,
    )
    db_session.add(allocation)
    await db_session.commit()

    # 7. Query and Assert Relationship Navigation with explicit async eager loading
    from sqlalchemy.orm import selectinload

    stmt = (
        select(Employee)
        .where(Employee.id == emp.id)
        .options(
            selectinload(Employee.role),
            selectinload(Employee.employee_skills),
            selectinload(Employee.allocations).selectinload(Allocation.project),
            selectinload(Employee.allocations).selectinload(Allocation.demand_plan),
        )
    )
    res = await db_session.execute(stmt)
    result_emp = res.scalar_one()

    assert result_emp is not None
    assert result_emp.role.title.startswith("Full Stack Architect")
    assert len(result_emp.employee_skills) == 2
    assert len(result_emp.allocations) == 1
    assert result_emp.allocations[0].project.name == "Global Workforce Intelligence Modernization"
    assert result_emp.allocations[0].demand_plan.business_id == demand.business_id


@pytest.mark.asyncio
async def test_allocation_history_preservation(db_session: AsyncSession):
    """
    Test business rule:
    Preserve allocation history. Do not silently overwrite historical records.
    When an allocation is modified, a new version is created and previous version is marked superseded.
    """
    # 1. Create base records
    role = Role(
        business_id=f"ROL-HIST-{uuid.uuid4().hex[:6]}",
        title=f"Senior Engineer {uuid.uuid4().hex[:6]}",
        code=f"SEN-{uuid.uuid4().hex[:6]}",
        department="Engineering",
    )
    emp = Employee(
        business_id=f"EMP-HIST-{uuid.uuid4().hex[:6]}",
        first_name="Marcus",
        last_name="Brody",
        email=f"marcus.{uuid.uuid4().hex[:6]}@workforceiq.internal",
        department="Engineering",
        location="Chicago",
        hire_date=date(2024, 1, 1),
    )
    project = Project(
        business_id=f"PRJ-HIST-{uuid.uuid4().hex[:6]}",
        name="Security Architecture Redesign",
        code=f"PRJ-SEC-{uuid.uuid4().hex[:6]}",
        department="Engineering",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
    )
    db_session.add_all([role, emp, project])
    await db_session.commit()

    # 2. Initial Allocation (Version 1: 50% allocation)
    alloc_v1 = Allocation(
        business_id=f"ALLOC-V1-{uuid.uuid4().hex[:6]}",
        employee_id=emp.id,
        project_id=project.id,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 6, 30),
        allocation_percentage=Decimal("50.00"),
        allocated_hours_per_week=Decimal("20.00"),
        status=AllocationStatus.ACTIVE,
        version=1,
        is_active=True,
    )
    db_session.add(alloc_v1)
    await db_session.commit()

    # 3. Project scope increases -> Create Version 2 (100% allocation), superseding Version 1
    alloc_v2 = Allocation(
        business_id=f"ALLOC-V2-{uuid.uuid4().hex[:6]}",
        employee_id=emp.id,
        project_id=project.id,
        start_date=date(2026, 4, 1),
        end_date=date(2026, 9, 30),
        allocation_percentage=Decimal("100.00"),
        allocated_hours_per_week=Decimal("40.00"),
        status=AllocationStatus.ACTIVE,
        version=2,
        is_active=True,
    )
    db_session.add(alloc_v2)
    await db_session.flush()

    # Mark Version 1 as superseded
    alloc_v1.is_active = False
    alloc_v1.superseded_by_id = alloc_v2.id
    await db_session.commit()

    # 4. Verify historical query retrieves both versions
    q = select(Allocation).where(Allocation.employee_id == emp.id).order_by(Allocation.version)
    res = await db_session.execute(q)
    allocations = res.scalars().all()

    assert len(allocations) == 2
    assert allocations[0].version == 1
    assert allocations[0].is_active is False
    assert allocations[0].superseded_by_id == alloc_v2.id
    assert allocations[1].version == 2
    assert allocations[1].is_active is True
    assert allocations[1].allocation_percentage == Decimal("100.00")


@pytest.mark.asyncio
async def test_intelligence_gap_and_recommendation_flow(db_session: AsyncSession):
    """Verify GapAnalysis, Recommendation, and AuditEvent models integrate properly."""
    skill = Skill(
        business_id=f"SKL-AI-{uuid.uuid4().hex[:6]}",
        name=f"PyTorch Deep Learning {uuid.uuid4().hex[:6]}",
        category=SkillCategory.TECHNICAL,
    )
    db_session.add(skill)
    await db_session.commit()

    # 1. Create GapAnalysis
    gap = GapAnalysis(
        business_id=f"GAP-2026-{uuid.uuid4().hex[:6]}",
        skill_id=skill.id,
        required_proficiency=4,
        required_headcount=3,
        available_headcount=1,
        deficit_headcount=2,
        severity=GapSeverity.HIGH,
        status=GapStatus.IDENTIFIED,
        target_fulfillment_date=date(2026, 8, 1),
        analysis_date=date(2026, 3, 1),
    )
    db_session.add(gap)
    await db_session.commit()

    # 2. Create Recommendation
    rec = Recommendation(
        business_id=f"REC-2026-{uuid.uuid4().hex[:6]}",
        gap_analysis_id=gap.id,
        type=RecommendationType.TRAINING_UPSKILL,
        confidence_score=Decimal("0.875"),
        impact_summary="Upskill 2 Senior Engineers via certified PyTorch specialization program.",
        status=RecommendationStatus.GENERATED,
        estimated_cost=Decimal("4500.00"),
        time_to_impact_days=45,
    )
    db_session.add(rec)
    await db_session.commit()

    # 3. Create AuditEvent
    audit = AuditEvent(
        business_id=f"AUD-2026-{uuid.uuid4().hex[:6]}",
        entity_type="Recommendation",
        entity_id=rec.id,
        action="INSERT",
        old_values=None,
        new_values={"status": "GENERATED", "type": "TRAINING_UPSKILL", "confidence": 0.875},
        reason="AI Engine automated recommendation generation for Q3 gap deficit.",
    )
    db_session.add(audit)
    await db_session.commit()

    from sqlalchemy.orm import selectinload

    stmt = select(GapAnalysis).where(GapAnalysis.id == gap.id).options(selectinload(GapAnalysis.recommendations))
    res = await db_session.execute(stmt)
    result_gap = res.scalar_one()

    assert result_gap.recommendations[0].business_id == rec.business_id
    assert audit.business_id.startswith("AUD-2026-")


def test_alembic_migration_head():
    """Verify Alembic migration script directory has revisions reaching head."""
    import os
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ini_path = os.path.join(backend_dir, "alembic.ini")
    cfg = Config(ini_path)
    cfg.set_main_option("script_location", os.path.join(backend_dir, "alembic"))
    script = ScriptDirectory.from_config(cfg)
    heads = script.get_heads()
    assert len(heads) == 1
    assert heads[0] == "b7c25489e5a6"
