"""
Skill Matching and Candidate Scoring Service for WorkforceIQ.

Matches employee competency profiles against project workforce demand requirements:
1. Assesses proficiency rating (1 to 5) against demanded benchmark.
2. Enforces skill validity: Stale certifications (>730 days) are disqualified from certified status.
3. Evaluates real-time availability and remaining capacity in the required interval.
4. Computes composite suitability match score (0.0% to 100.0%) and ranks candidates.
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Sequence, Union
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.allocation import Allocation
from app.models.employee import Availability, Employee
from app.models.enums import EmploymentStatus, VerificationStatus
from app.models.project import DemandPlan, Project
from app.models.skill import EmployeeSkill, Skill
from app.services.capacity_service import CapacityService
from app.services.thresholds import DEFAULT_THRESHOLDS, PlanningThresholds
from app.services.utilization_service import UtilizationService


@dataclass(frozen=True)
class CandidateMatch:
    """Detailed candidate matching and qualification score for a project demand line."""
    employee_id: str
    business_id: str
    employee_name: str
    role_id: Optional[str]
    department: str
    skill_id: str
    skill_name: str
    assessed_proficiency: int
    effective_certified_proficiency: int
    required_proficiency: int
    proficiency_gap: int
    verification_status: str
    verified_at: Optional[str]
    is_stale: bool
    available_hours: float
    allocated_hours: float
    remaining_capacity_hours: float
    is_fully_qualified: bool
    match_score: float
    calculated_at: str
    rule_version: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "employee_id": self.employee_id,
            "business_id": self.business_id,
            "employee_name": self.employee_name,
            "role_id": self.role_id,
            "department": self.department,
            "skill_id": self.skill_id,
            "skill_name": self.skill_name,
            "assessed_proficiency": self.assessed_proficiency,
            "effective_certified_proficiency": self.effective_certified_proficiency,
            "required_proficiency": self.required_proficiency,
            "proficiency_gap": self.proficiency_gap,
            "verification_status": self.verification_status,
            "verified_at": self.verified_at,
            "is_stale": self.is_stale,
            "available_hours": self.available_hours,
            "allocated_hours": self.allocated_hours,
            "remaining_capacity_hours": self.remaining_capacity_hours,
            "is_fully_qualified": self.is_fully_qualified,
            "match_score": self.match_score,
            "calculated_at": self.calculated_at,
            "rule_version": self.rule_version,
        }


class SkillMatchingService:
    """Canonical engine for skill matching, candidate scoring, and suitability ranking."""

    @classmethod
    def evaluate_candidate(
        cls,
        employee: Union[Employee, Dict[str, Any]],
        employee_skill: Optional[Union[EmployeeSkill, Dict[str, Any]]],
        required_proficiency: int,
        start_date: date,
        end_date: date,
        required_hours: float = 40.0,
        demanded_role_id: Optional[str] = None,
        as_of_date: Optional[date] = None,
        allocations: Optional[Sequence[Union[Allocation, Dict[str, Any]]]] = None,
        availabilities: Optional[Sequence[Union[Availability, Dict[str, Any]]]] = None,
        skill_name: str = "Target Skill",
        thresholds: PlanningThresholds = DEFAULT_THRESHOLDS,
    ) -> CandidateMatch:
        """
        Evaluate and score an employee candidate against a specific skill demand requirement.
        Canonical implementation for single and batch candidate ranking.
        """
        ref_date = as_of_date or date.today()

        if isinstance(employee, dict):
            emp_id = employee.get("id")
            biz_id = employee.get("business_id", "EMP-UNKNOWN")
            first_name = employee.get("first_name", "")
            last_name = employee.get("last_name", "")
            role_id = employee.get("role_id")
            dept = employee.get("department", "Engineering")
            emp_status = employee.get("employment_status", "ACTIVE")
        else:
            emp_id = getattr(employee, "id", None)
            biz_id = getattr(employee, "business_id", "EMP-UNKNOWN")
            first_name = getattr(employee, "first_name", "")
            last_name = getattr(employee, "last_name", "")
            role_id = getattr(employee, "role_id", None)
            dept = getattr(employee, "department", "Engineering")
            emp_status = getattr(employee, "employment_status", "ACTIVE")

        emp_name = f"{first_name} {last_name}".strip()
        if isinstance(emp_status, EmploymentStatus):
            emp_status_val = emp_status.value
        else:
            emp_status_val = str(emp_status)

        # 1. Lifecycle Status Eligibility Check
        eligible_statuses = {EmploymentStatus.ACTIVE.value, EmploymentStatus.CONTRACTOR.value, EmploymentStatus.PROBATION.value, "ACTIVE", "CONTRACTOR", "PROBATION"}
        is_status_eligible = (emp_status_val in eligible_statuses)

        # 2. Competency and Verification Freshness
        assessed_prof = 0
        effective_prof = 0
        verif_status_val = "UNVERIFIED"
        verified_at_str = None
        is_stale = False
        s_id = "UNKNOWN"

        if employee_skill:
            if isinstance(employee_skill, dict):
                s_id = employee_skill.get("skill_id", "UNKNOWN")
                assessed_prof = int(employee_skill.get("proficiency_level") or 0)
                raw_v_status = employee_skill.get("verification_status")
                raw_verified_at = employee_skill.get("verified_at")
            else:
                s_id = getattr(employee_skill, "skill_id", "UNKNOWN")
                assessed_prof = int(getattr(employee_skill, "proficiency_level", 0) or 0)
                raw_v_status = getattr(employee_skill, "verification_status", None)
                raw_verified_at = getattr(employee_skill, "verified_at", None)

            if isinstance(raw_v_status, VerificationStatus):
                verif_status_val = raw_v_status.value
            else:
                verif_status_val = str(raw_v_status or "SELF_REPORTED")
            if raw_verified_at:
                if isinstance(raw_verified_at, str):
                    v_dt = datetime.fromisoformat(raw_verified_at)
                    v_date = v_dt.date()
                    verified_at_str = raw_verified_at
                elif isinstance(raw_verified_at, datetime):
                    v_date = raw_verified_at.date()
                    verified_at_str = raw_verified_at.isoformat()
                elif isinstance(raw_verified_at, date):
                    v_date = raw_verified_at
                    verified_at_str = str(raw_verified_at)
                else:
                    v_date = None

                if v_date:
                    elapsed = (ref_date - v_date).days
                    if elapsed > thresholds.stale_skill_validity_days:
                        is_stale = True

            # Business Rule: A stale skill must not count as verified current
            if is_stale or verif_status_val == VerificationStatus.EXPIRED.value:
                effective_prof = 0  # Disqualified from verified current status
            else:
                effective_prof = assessed_prof

        prof_gap = max(0, required_proficiency - effective_prof)

        # 3. Capacity & Availability Evaluation
        util_result = UtilizationService.calculate_utilization(
            employee=employee,
            start_date=start_date,
            end_date=end_date,
            allocations=allocations,
            availabilities=availabilities,
            thresholds=thresholds,
        )

        avail_hours = util_result.available_hours
        alloc_hours = util_result.allocated_hours
        remaining_hours = max(0.0, util_result.remaining_hours)

        # 4. Multi-Factor Match Score (0.0 to 100.0%)
        if not is_status_eligible:
            match_score = 0.0
            is_qualified = False
        else:
            # Factor A: Proficiency Fit (45% weight)
            if required_proficiency > 0:
                prof_score = min(1.0, effective_prof / required_proficiency)
            else:
                prof_score = 1.0 if effective_prof > 0 else 0.0

            # Factor B: Capacity / Availability Fit (35% weight)
            if required_hours > 0.0:
                avail_score = min(1.0, remaining_hours / required_hours)
            else:
                avail_score = 1.0

            # Factor C: Role Match (15% weight)
            if demanded_role_id and role_id:
                role_score = 1.0 if role_id == demanded_role_id else 0.75
            else:
                role_score = 0.85

            # Factor D: Verification Confidence (5% weight)
            if is_stale:
                verif_score = 0.0
            elif verif_status_val == VerificationStatus.ASSESSMENT_CERTIFIED.value:
                verif_score = 1.0
            elif verif_status_val == VerificationStatus.MANAGER_VERIFIED.value:
                verif_score = 0.85
            elif verif_status_val == VerificationStatus.SELF_REPORTED.value:
                verif_score = 0.50
            else:
                verif_score = 0.20

            # Composite weighted calculation
            composite = (
                (prof_score * 0.45)
                + (avail_score * 0.35)
                + (role_score * 0.15)
                + (verif_score * 0.05)
            )
            match_score = round(composite * 100.0, 2)

            # Qualification threshold: meets or exceeds proficiency, not stale, has capacity
            is_qualified = (
                effective_prof >= required_proficiency
                and not is_stale
                and remaining_hours >= (required_hours * 0.50)  # At least 50% capacity available
            )

        return CandidateMatch(
            employee_id=emp_id,
            business_id=biz_id,
            employee_name=emp_name,
            role_id=role_id,
            department=dept,
            skill_id=s_id,
            skill_name=skill_name,
            assessed_proficiency=assessed_prof,
            effective_certified_proficiency=effective_prof,
            required_proficiency=required_proficiency,
            proficiency_gap=prof_gap,
            verification_status=verif_status_val,
            verified_at=verified_at_str,
            is_stale=is_stale,
            available_hours=avail_hours,
            allocated_hours=alloc_hours,
            remaining_capacity_hours=remaining_hours,
            is_fully_qualified=is_qualified,
            match_score=match_score,
            calculated_at=datetime.now(timezone.utc).isoformat(),
            rule_version=thresholds.rule_version,
        )

    @classmethod
    async def match_candidates_for_demand_async(
        cls,
        session: AsyncSession,
        demand_plan_id: str,
        as_of_date: Optional[date] = None,
        top_n: int = 10,
        thresholds: PlanningThresholds = DEFAULT_THRESHOLDS,
    ) -> List[CandidateMatch]:
        """Query database and rank top candidate employees for a project demand requirement."""
        # 1. Fetch DemandPlan with primary skill
        d_stmt = select(DemandPlan).options(selectinload(DemandPlan.project)).where(DemandPlan.id == demand_plan_id)
        d_res = await session.execute(d_stmt)
        demand = d_res.scalar_one_or_none()
        if not demand:
            return []

        skill_id = demand.primary_skill_id
        req_prof = demand.min_proficiency
        start_date = demand.start_date
        end_date = demand.end_date
        req_hours = float(demand.required_hours)

        # 2. Query skill details
        skill_name = "Required Skill"
        if skill_id:
            s_stmt = select(Skill).where(Skill.id == skill_id)
            s_res = await session.execute(s_stmt)
            skl = s_res.scalar_one_or_none()
            if skl:
                skill_name = skl.name

        # 3. Query all active employees possessing this skill
        es_stmt = (
            select(EmployeeSkill, Employee)
            .join(Employee, Employee.id == EmployeeSkill.employee_id)
            .where(
                and_(
                    EmployeeSkill.skill_id == skill_id,
                    EmployeeSkill.is_current == True,
                    Employee.employment_status.in_([EmploymentStatus.ACTIVE, EmploymentStatus.CONTRACTOR, EmploymentStatus.PROBATION]),
                )
            )
        )
        es_res = await session.execute(es_stmt)
        records = es_res.all()

        if not records:
            return []

        candidate_emp_ids = [emp.id for (_, emp) in records]

        # Batch fetch allocations
        alloc_stmt = select(Allocation).where(
            and_(
                Allocation.employee_id.in_(candidate_emp_ids),
                Allocation.is_active == True,
                Allocation.start_date <= end_date,
                Allocation.end_date >= start_date,
            )
        )
        alloc_res = await session.execute(alloc_stmt)
        all_allocs = alloc_res.scalars().all()
        allocs_by_emp: Dict[str, List[Allocation]] = {}
        for a in all_allocs:
            allocs_by_emp.setdefault(a.employee_id, []).append(a)

        # Batch fetch availability
        av_stmt = select(Availability).where(
            and_(
                Availability.employee_id.in_(candidate_emp_ids),
                Availability.is_approved == True,
                Availability.start_date <= end_date,
                Availability.end_date >= start_date,
            )
        )
        av_res = await session.execute(av_stmt)
        all_avs = av_res.scalars().all()
        avs_by_emp: Dict[str, List[Availability]] = {}
        for av in all_avs:
            avs_by_emp.setdefault(av.employee_id, []).append(av)

        # Score candidates
        matches = []
        for emp_skill, emp in records:
            match = cls.evaluate_candidate(
                employee=emp,
                employee_skill=emp_skill,
                required_proficiency=req_prof,
                start_date=start_date,
                end_date=end_date,
                required_hours=req_hours,
                demanded_role_id=demand.role_id,
                as_of_date=as_of_date,
                allocations=allocs_by_emp.get(emp.id, []),
                availabilities=avs_by_emp.get(emp.id, []),
                skill_name=skill_name,
                thresholds=thresholds,
            )
            matches.append(match)

        # Rank deterministically by match_score DESC, proficiency_gap ASC, remaining_capacity DESC
        matches.sort(key=lambda m: (-m.match_score, m.proficiency_gap, -m.remaining_capacity_hours, m.business_id))
        return matches[:top_n]

