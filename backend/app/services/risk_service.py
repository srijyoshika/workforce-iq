"""
Workforce Risk Detection and Operational Conflict Service for WorkforceIQ.

Detects critical operational risks, capacity overloads, and skill deficits:
1. OVERALLOCATION:
   Identifies allocations causing employee total active hours to exceed capacity (>100%).
   Calculates exact excess hours and utilization rate.
2. STALE SKILLS:
   Detects skills marked current whose last verification exceeds the validity threshold (730 days).
   Enforces that stale skills do not count as verified current talent.
3. DUPLICATE DEMAND:
   Identifies duplicate deliveries of demand plan lines using delivery identity:
   (project_id, role_id, start_date, end_date, primary_skill_id).
4. OVERLAPPING ASSIGNMENTS:
   Detects concurrent overlapping project allocations across distinct projects.
   Calculates exact overlap window, overlap days, and overlapping hours.
5. PROJECT STAFFING SHORTAGE:
   Detects imminent unfulfilled project demand lines starting within the warning horizon (60 days).

Maintains complete traceability, configurable governance thresholds, and provides
both in-memory calculation routines and asynchronous database synchronization.
"""

from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union
import uuid

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.allocation import Allocation
from app.models.employee import Employee
from app.models.skill import EmployeeSkill
from app.models.enums import (
    AllocationStatus,
    EmploymentStatus,
    IssueSeverity,
    IssueStatus,
    IssueType,
    ProjectStatus,
    VerificationStatus,
)
from app.models.intelligence import IssueRecord
from app.models.project import DemandPlan, Project
from app.services.thresholds import DEFAULT_THRESHOLDS, PlanningThresholds


@dataclass(frozen=True)
class RiskDetectionItem:
    """Individual detected workforce risk or operational conflict record."""
    issue_type: str                   # IssueType enum value
    severity: str                     # IssueSeverity enum value
    entity_type: str                  # e.g. "Allocation", "EmployeeSkill", "DemandPlan", "Project"
    entity_id: str                    # Target entity primary key
    business_id: Optional[str]        # Target entity business ID (e.g. ALLOC-..., EMP-...)
    employee_id: Optional[str]        # Affected employee ID (if applicable)
    project_id: Optional[str]         # Affected project ID (if applicable)
    title: str                        # Concise summary
    description: str                  # Detailed explanation and metrics
    action: str                       # Recommended mitigating operational action
    details: Dict[str, Any]           # Structured calculation metrics
    rule_version: str = "1.0.0"
    detected_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RiskService:
    """
    Canonical Workforce Risk Engine.
    Evaluates in-memory dataset records or live SQLAlchemy queries to detect operational risks.
    """

    # -------------------------------------------------------------------------
    # 1. OVERALLOCATION DETECTION
    # -------------------------------------------------------------------------
    @classmethod
    def detect_overallocations(
        cls,
        allocations: Sequence[Union[Allocation, Dict[str, Any]]],
        employees: Sequence[Union[Employee, Dict[str, Any]]],
        thresholds: PlanningThresholds = DEFAULT_THRESHOLDS,
    ) -> List[RiskDetectionItem]:
        """
        Detect allocations causing an employee's total active hours to exceed contract capacity.
        Identifies the specific breaching allocation and calculates exact excess hours.
        """
        # Map employee capacities
        emp_cap_map: Dict[str, float] = {}
        for emp in employees:
            e_id = emp["id"] if isinstance(emp, dict) else emp.id
            hours = float(emp["standard_hours_per_week"]) if isinstance(emp, dict) else float(emp.standard_hours_per_week)
            emp_cap_map[e_id] = hours

        # Group active allocations by employee
        allocs_by_emp: Dict[str, List[Union[Allocation, Dict[str, Any]]]] = {}
        for a in allocations:
            is_active = a.get("is_active", True) if isinstance(a, dict) else a.is_active
            status = a.get("status") if isinstance(a, dict) else (a.status.value if hasattr(a.status, "value") else str(a.status))
            if is_active and status not in ("CANCELLED", "RELEASED", "COMPLETED"):
                emp_id = a["employee_id"] if isinstance(a, dict) else a.employee_id
                allocs_by_emp.setdefault(emp_id, []).append(a)

        detected: List[RiskDetectionItem] = []

        for emp_id, emp_allocs in allocs_by_emp.items():
            cap = emp_cap_map.get(emp_id, thresholds.default_standard_hours)
            if cap <= 0:
                continue

            def sort_key(x):
                s_date = x["start_date"] if isinstance(x, dict) else x.start_date
                c_at = str(x.get("created_at", "")) if isinstance(x, dict) else str(getattr(x, "created_at", ""))
                return (s_date, c_at)

            sorted_allocs = sorted(emp_allocs, key=sort_key)

            for idx, alloc in enumerate(sorted_allocs):
                a_id = alloc["id"] if isinstance(alloc, dict) else alloc.id
                a_biz_id = alloc.get("business_id", "") if isinstance(alloc, dict) else alloc.business_id
                a_proj_id = alloc.get("project_id") if isinstance(alloc, dict) else alloc.project_id
                a_start = alloc["start_date"] if isinstance(alloc, dict) else alloc.start_date
                a_end = alloc["end_date"] if isinstance(alloc, dict) else alloc.end_date
                a_hours = float(alloc["allocated_hours_per_week"]) if isinstance(alloc, dict) else float(alloc.allocated_hours_per_week)

                # Prior overlapping hours established by allocations chronologically ordered before this one
                prior_overlapping_hours = 0.0
                for other in sorted_allocs[:idx]:
                    o_start = other["start_date"] if isinstance(other, dict) else other.start_date
                    o_end = other["end_date"] if isinstance(other, dict) else other.end_date
                    o_hours = float(other["allocated_hours_per_week"]) if isinstance(other, dict) else float(other.allocated_hours_per_week)

                    # Overlap check
                    if not (a_end < o_start or a_start > o_end):
                        prior_overlapping_hours += o_hours

                total_hours = prior_overlapping_hours + a_hours

                # Flag allocation whose addition breached available capacity
                if total_hours > cap and prior_overlapping_hours <= cap:
                    excess_hours = round(total_hours - cap, 2)
                    utilization_pct = round((total_hours / cap) * 100.0, 1)

                    detected.append(
                        RiskDetectionItem(
                            issue_type=IssueType.CAPACITY_OVERLOAD.value,
                            severity=IssueSeverity.CRITICAL.value,
                            entity_type="Allocation",
                            entity_id=a_id,
                            business_id=a_biz_id,
                            employee_id=emp_id,
                            project_id=a_proj_id,
                            title=f"Capacity Overload: Allocation {a_biz_id} exceeds capacity by {excess_hours}h/week",
                            description=(
                                f"Employee total assigned workload reaches {total_hours:.1f}h/week "
                                f"against standard capacity of {cap:.1f}h/week ({utilization_pct}% utilization). "
                                f"Allocation breaches limit by {excess_hours:.1f}h/week during {a_start} to {a_end}."
                            ),
                            action="REDUCE_ALLOCATION_HOURS",
                            details={
                                "employee_id": emp_id,
                                "allocation_id": a_id,
                                "business_id": a_biz_id,
                                "capacity_hours": cap,
                                "total_allocated_hours": round(total_hours, 2),
                                "excess_hours": excess_hours,
                                "utilization_pct": utilization_pct,
                                "window_start": str(a_start),
                                "window_end": str(a_end),
                            },
                            rule_version=thresholds.rule_version,
                        )
                    )

        return detected

    # -------------------------------------------------------------------------
    # 2. STALE SKILL DETECTION
    # -------------------------------------------------------------------------
    @classmethod
    def detect_stale_skills(
        cls,
        employee_skills: Sequence[Union[EmployeeSkill, Dict[str, Any]]],
        as_of_date: Optional[date] = None,
        thresholds: PlanningThresholds = DEFAULT_THRESHOLDS,
    ) -> List[RiskDetectionItem]:
        """
        Detect employee skill records marked as current (is_current = True) whose verification
        date is older than the allowed validity period (default 730 days).
        Ensures stale skills are flagged and prevented from counting as verified talent.
        """
        ref_date = as_of_date or date.today()
        detected: List[RiskDetectionItem] = []

        for sk in employee_skills:
            is_current = sk.get("is_current", False) if isinstance(sk, dict) else sk.is_current
            if not is_current:
                continue

            verified_at = sk.get("verified_at") if isinstance(sk, dict) else sk.verified_at
            if not verified_at:
                continue

            if isinstance(verified_at, str):
                v_date = datetime.fromisoformat(verified_at).date()
            elif isinstance(verified_at, datetime):
                v_date = verified_at.date()
            elif isinstance(verified_at, date):
                v_date = verified_at
            else:
                continue

            elapsed_days = (ref_date - v_date).days
            if elapsed_days > thresholds.stale_skill_validity_days:
                days_overdue = elapsed_days - thresholds.stale_skill_validity_days
                s_id = sk["id"] if isinstance(sk, dict) else sk.id
                s_biz_id = sk.get("business_id", "") if isinstance(sk, dict) else sk.business_id
                emp_id = sk["employee_id"] if isinstance(sk, dict) else sk.employee_id
                skill_id = sk["skill_id"] if isinstance(sk, dict) else sk.skill_id
                prof = sk.get("proficiency_level") if isinstance(sk, dict) else sk.proficiency_level

                detected.append(
                    RiskDetectionItem(
                        issue_type=IssueType.SKILL_SHORTAGE.value,
                        severity=IssueSeverity.HIGH.value,
                        entity_type="EmployeeSkill",
                        entity_id=s_id,
                        business_id=s_biz_id,
                        employee_id=emp_id,
                        project_id=None,
                        title=f"Stale Skill Certification: Skill {skill_id} overdue by {days_overdue} days",
                        description=(
                            f"Employee skill profile was last verified on {v_date} ({elapsed_days} days ago). "
                            f"Exceeds max validity threshold of {thresholds.stale_skill_validity_days} days by {days_overdue} days. "
                            f"Skill cannot be counted as verified talent until re-evaluated."
                        ),
                        action="REVERIFY_EMPLOYEE_SKILL",
                        details={
                            "employee_id": emp_id,
                            "skill_id": skill_id,
                            "business_id": s_biz_id,
                            "proficiency_level": prof,
                            "verified_at": v_date.isoformat(),
                            "as_of_date": ref_date.isoformat(),
                            "elapsed_days": elapsed_days,
                            "threshold_days": thresholds.stale_skill_validity_days,
                            "days_overdue": days_overdue,
                        },
                        rule_version=thresholds.rule_version,
                    )
                )

        return detected

    # -------------------------------------------------------------------------
    # 3. DUPLICATE DEMAND DETECTION
    # -------------------------------------------------------------------------
    @classmethod
    def detect_duplicate_demand(
        cls,
        demand_plans: Sequence[Union[DemandPlan, Dict[str, Any]]],
        thresholds: PlanningThresholds = DEFAULT_THRESHOLDS,
    ) -> List[RiskDetectionItem]:
        """
        Detect duplicate deliveries of existing demand requirements using core delivery identity:
        (project_id, role_id, start_date, end_date, primary_skill_id).
        Retains original requirement and flags subsequent duplicate lines.
        """
        delivery_groups: Dict[Tuple, List[Union[DemandPlan, Dict[str, Any]]]] = {}

        for d in demand_plans:
            proj_id = d["project_id"] if isinstance(d, dict) else d.project_id
            role_id = d["role_id"] if isinstance(d, dict) else d.role_id
            s_date = str(d["start_date"] if isinstance(d, dict) else d.start_date)
            e_date = str(d["end_date"] if isinstance(d, dict) else d.end_date)
            skill_id = d.get("primary_skill_id") if isinstance(d, dict) else d.primary_skill_id

            sig = (proj_id, role_id, s_date, e_date, skill_id)
            delivery_groups.setdefault(sig, []).append(d)

        detected: List[RiskDetectionItem] = []

        for sig, items in delivery_groups.items():
            if len(items) > 1:
                # First line is original; subsequent lines are duplicates
                orig = items[0]
                orig_id = orig["id"] if isinstance(orig, dict) else orig.id
                orig_biz = orig.get("business_id", "") if isinstance(orig, dict) else orig.business_id

                for dup in items[1:]:
                    dup_id = dup["id"] if isinstance(dup, dict) else dup.id
                    dup_biz = dup.get("business_id", "") if isinstance(dup, dict) else dup.business_id
                    proj_id = sig[0]
                    role_id = sig[1]
                    s_date = sig[2]
                    e_date = sig[3]

                    detected.append(
                        RiskDetectionItem(
                            issue_type=IssueType.UNFULFILLED_DEMAND.value,
                            severity=IssueSeverity.MEDIUM.value,
                            entity_type="DemandPlan",
                            entity_id=dup_id,
                            business_id=dup_biz,
                            employee_id=None,
                            project_id=proj_id,
                            title=f"Duplicate Demand Line: {dup_biz} duplicates existing demand {orig_biz}",
                            description=(
                                f"Demand requirement {dup_biz} shares identical delivery identity "
                                f"(Role: {role_id}, Period: {s_date} to {e_date}, Skill: {sig[4]}) "
                                f"with baseline demand line {orig_biz}. Risk of double-counting staffing requirements."
                            ),
                            action="DE_DUPLICATE_DEMAND_LINE",
                            details={
                                "original_demand_id": orig_id,
                                "duplicate_demand_id": dup_id,
                                "original_business_id": orig_biz,
                                "duplicate_business_id": dup_biz,
                                "project_id": proj_id,
                                "role_id": role_id,
                                "start_date": s_date,
                                "end_date": e_date,
                                "primary_skill_id": sig[4],
                                "delivery_identity": f"{proj_id}:{role_id}:{s_date}:{e_date}:{sig[4]}",
                            },
                            rule_version=thresholds.rule_version,
                        )
                    )

        return detected

    # -------------------------------------------------------------------------
    # 4. OVERLAPPING ALLOCATION DETECTION
    # -------------------------------------------------------------------------
    @classmethod
    def detect_overlapping_allocations(
        cls,
        allocations: Sequence[Union[Allocation, Dict[str, Any]]],
        thresholds: PlanningThresholds = DEFAULT_THRESHOLDS,
        min_overlap_days: int = 14,
        min_individual_pct: float = 40.0,
    ) -> List[RiskDetectionItem]:
        """
        Detect employees assigned to concurrent project allocations across distinct projects
        with significant overlap (e.g. >= 14 days and both >= 40% commitment).
        Calculates exact overlap start, end, days, and overlapping hours.
        """
        allocs_by_emp: Dict[str, List[Union[Allocation, Dict[str, Any]]]] = {}
        for a in allocations:
            is_active = a.get("is_active", True) if isinstance(a, dict) else a.is_active
            status = a.get("status") if isinstance(a, dict) else (a.status.value if hasattr(a.status, "value") else str(a.status))
            if is_active and status not in ("CANCELLED", "RELEASED", "COMPLETED"):
                emp_id = a["employee_id"] if isinstance(a, dict) else a.employee_id
                allocs_by_emp.setdefault(emp_id, []).append(a)

        detected: List[RiskDetectionItem] = []

        for emp_id, emp_allocs in allocs_by_emp.items():
            if len(emp_allocs) < 2:
                continue

            def sort_key(x):
                s_date = x["start_date"] if isinstance(x, dict) else x.start_date
                c_at = str(x.get("created_at", "")) if isinstance(x, dict) else str(getattr(x, "created_at", ""))
                return (s_date, c_at)

            sorted_allocs = sorted(emp_allocs, key=sort_key)
            seen_conflict_ids: Set[str] = set()

            for i in range(len(sorted_allocs)):
                for j in range(i + 1, len(sorted_allocs)):
                    a1 = sorted_allocs[i]
                    a2 = sorted_allocs[j]

                    p1 = a1["project_id"] if isinstance(a1, dict) else a1.project_id
                    p2 = a2["project_id"] if isinstance(a2, dict) else a2.project_id
                    id2 = a2["id"] if isinstance(a2, dict) else a2.id

                    # Only check cross-project conflicts and avoid duplicate flags on the same secondary allocation
                    if p1 == p2 or id2 in seen_conflict_ids:
                        continue

                    s1 = a1["start_date"] if isinstance(a1, dict) else a1.start_date
                    e1 = a1["end_date"] if isinstance(a1, dict) else a1.end_date
                    s2 = a2["start_date"] if isinstance(a2, dict) else a2.start_date
                    e2 = a2["end_date"] if isinstance(a2, dict) else a2.end_date

                    o_start = max(s1, s2)
                    o_end = min(e1, e2)

                    if o_start <= o_end:
                        overlap_days = (o_end - o_start).days + 1
                        pct1 = float(a1["allocation_percentage"] if isinstance(a1, dict) else a1.allocation_percentage)
                        pct2 = float(a2["allocation_percentage"] if isinstance(a2, dict) else a2.allocation_percentage)

                        if overlap_days >= min_overlap_days and pct1 >= min_individual_pct and pct2 >= min_individual_pct:
                            hours1 = float(a1["allocated_hours_per_week"] if isinstance(a1, dict) else a1.allocated_hours_per_week)
                            hours2 = float(a2["allocated_hours_per_week"] if isinstance(a2, dict) else a2.allocated_hours_per_week)
                            combined_hours = hours1 + hours2
                            overlap_hours = round((overlap_days / 7.0) * hours2, 2)
                            seen_conflict_ids.add(id2)

                            biz1 = a1.get("business_id", "") if isinstance(a1, dict) else a1.business_id
                            biz2 = a2.get("business_id", "") if isinstance(a2, dict) else a2.business_id

                            detected.append(
                                RiskDetectionItem(
                                    issue_type=IssueType.ALLOCATION_CONFLICT.value,
                                    severity=IssueSeverity.HIGH.value,
                                    entity_type="Allocation",
                                    entity_id=id2,
                                    business_id=biz2,
                                    employee_id=emp_id,
                                    project_id=p2,
                                    title=f"Conflicting Overlapping Allocation: {biz2} collides with {biz1}",
                                    description=(
                                        f"Employee is concurrently committed across Project {p1} ({pct1:.0f}%) "
                                        f"and Project {p2} ({pct2:.0f}%) for {overlap_days} days ({o_start} to {o_end}). "
                                        f"Combined commitment reaches {combined_hours:.1f}h/week."
                                    ),
                                    action="RESOLVE_SCHEDULE_OVERLAP",
                                    details={
                                        "employee_id": emp_id,
                                        "primary_allocation_id": a1["id"] if isinstance(a1, dict) else a1.id,
                                        "conflicting_allocation_id": id2,
                                        "primary_business_id": biz1,
                                        "conflicting_business_id": biz2,
                                        "overlap_start": str(o_start),
                                        "overlap_end": str(o_end),
                                        "overlap_days": overlap_days,
                                        "overlap_hours": overlap_hours,
                                        "combined_weekly_hours": round(combined_hours, 2),
                                    },
                                    rule_version=thresholds.rule_version,
                                )
                            )

        return detected

    # -------------------------------------------------------------------------
    # 5. PROJECT STAFFING SHORTAGE DETECTION
    # -------------------------------------------------------------------------
    @classmethod
    def detect_project_staffing_shortages(
        cls,
        projects: Sequence[Union[Project, Dict[str, Any]]],
        demand_plans: Sequence[Union[DemandPlan, Dict[str, Any]]],
        allocations: Sequence[Union[Allocation, Dict[str, Any]]],
        as_of_date: Optional[date] = None,
        thresholds: PlanningThresholds = DEFAULT_THRESHOLDS,
    ) -> List[RiskDetectionItem]:
        """
        Detect projects with unfulfilled staffing requirements starting within
        the shortage warning horizon (default 60 days).
        Flags critical or high deficits in active projects.
        """
        ref_date = as_of_date or date.today()
        warning_horizon = ref_date + timedelta(days=thresholds.shortage_warning_days)

        # Build map of active projects
        active_projects: Dict[str, Union[Project, Dict[str, Any]]] = {}
        for p in projects:
            p_id = p["id"] if isinstance(p, dict) else p.id
            status = p.get("status") if isinstance(p, dict) else (p.status.value if hasattr(p.status, "value") else str(p.status))
            if status in (ProjectStatus.PIPELINE.value, ProjectStatus.APPROVED.value, ProjectStatus.ACTIVE.value, "PIPELINE", "APPROVED", "ACTIVE"):
                active_projects[p_id] = p

        # Map active allocated hours per demand plan
        allocated_hours_by_demand: Dict[str, float] = {}
        allocated_count_by_demand: Dict[str, int] = {}
        for a in allocations:
            is_active = a.get("is_active", True) if isinstance(a, dict) else a.is_active
            status = a.get("status") if isinstance(a, dict) else (a.status.value if hasattr(a.status, "value") else str(a.status))
            d_id = a.get("demand_plan_id") if isinstance(a, dict) else a.demand_plan_id
            if is_active and d_id and status not in ("CANCELLED", "RELEASED", "COMPLETED"):
                h = float(a["allocated_hours_per_week"] if isinstance(a, dict) else a.allocated_hours_per_week)
                allocated_hours_by_demand[d_id] = allocated_hours_by_demand.get(d_id, 0.0) + h
                allocated_count_by_demand[d_id] = allocated_count_by_demand.get(d_id, 0) + 1

        detected: List[RiskDetectionItem] = []

        for d in demand_plans:
            proj_id = d["project_id"] if isinstance(d, dict) else d.project_id
            if proj_id not in active_projects:
                continue

            s_date = d["start_date"] if isinstance(d, dict) else d.start_date
            if isinstance(s_date, str):
                s_date = date.fromisoformat(s_date)

            # Check if demand starts within shortage warning horizon and not already past
            if s_date < ref_date or s_date > warning_horizon:
                continue

            d_id = d["id"] if isinstance(d, dict) else d.id
            d_biz = d.get("business_id", "") if isinstance(d, dict) else d.business_id
            req_headcount = int(d["required_headcount"] if isinstance(d, dict) else d.required_headcount)
            req_hours = float(d.get("required_hours", req_headcount * thresholds.default_standard_hours)
                              if isinstance(d, dict)
                              else (getattr(d, "required_hours", None) or (req_headcount * thresholds.default_standard_hours)))
            priority = int(d.get("priority", 2) if isinstance(d, dict) else getattr(d, "priority", 2))

            assigned_count = allocated_count_by_demand.get(d_id, 0)
            assigned_hours = allocated_hours_by_demand.get(d_id, 0.0)

            unfilled_count = max(0, req_headcount - assigned_count)
            unfilled_hours = max(0.0, req_hours - assigned_hours)

            if unfilled_count > 0 or unfilled_hours > 0:
                days_until_start = (s_date - ref_date).days
                is_critical_priority = priority <= thresholds.critical_priority_level
                pct_unfilled = (unfilled_hours / req_hours * 100.0) if req_hours > 0 else 100.0

                if is_critical_priority or pct_unfilled >= thresholds.critical_gap_unfilled_pct:
                    severity = IssueSeverity.CRITICAL.value
                elif pct_unfilled >= thresholds.high_gap_unfilled_pct:
                    severity = IssueSeverity.HIGH.value
                else:
                    severity = IssueSeverity.MEDIUM.value

                proj_obj = active_projects[proj_id]
                proj_name = proj_obj.get("name", proj_id) if isinstance(proj_obj, dict) else proj_obj.name

                detected.append(
                    RiskDetectionItem(
                        issue_type=IssueType.UNFULFILLED_DEMAND.value,
                        severity=severity,
                        entity_type="DemandPlan",
                        entity_id=d_id,
                        business_id=d_biz,
                        employee_id=None,
                        project_id=proj_id,
                        title=f"Imminent Staffing Shortage: {proj_name} needs {unfilled_count} headcount in {days_until_start} days",
                        description=(
                            f"Demand {d_biz} requires {req_headcount} staff ({req_hours:.1f}h/week) starting on {s_date}. "
                            f"Currently only {assigned_count} staff ({assigned_hours:.1f}h/week) allocated. "
                            f"Unfilled deficit: {unfilled_count} headcount ({unfilled_hours:.1f}h/week, {pct_unfilled:.1f}% unfilled)."
                        ),
                        action="ALLOCATE_RESOURCES_OR_HIRE",
                        details={
                            "project_id": proj_id,
                            "project_name": proj_name,
                            "demand_plan_id": d_id,
                            "business_id": d_biz,
                            "start_date": str(s_date),
                            "days_until_start": days_until_start,
                            "required_headcount": req_headcount,
                            "allocated_headcount": assigned_count,
                            "headcount_deficit": unfilled_count,
                            "required_hours": req_hours,
                            "allocated_hours": assigned_hours,
                            "unfilled_hours": unfilled_hours,
                            "pct_unfilled": round(pct_unfilled, 1),
                            "priority": priority,
                        },
                        rule_version=thresholds.rule_version,
                    )
                )

        return detected

    # -------------------------------------------------------------------------
    # 6. MASTER RISK DETECTION RUNNER
    # -------------------------------------------------------------------------
    @classmethod
    def detect_all_risks(
        cls,
        dataset: Dict[str, List[Dict[str, Any]]],
        as_of_date: Optional[date] = None,
        thresholds: PlanningThresholds = DEFAULT_THRESHOLDS,
    ) -> List[RiskDetectionItem]:
        """
        Evaluate all 5 risk categories across an in-memory dataset dictionary.
        Useful for simulations, pipeline validations, and automated anomaly auditing.
        """
        all_risks: List[RiskDetectionItem] = []

        # 1. Overallocation
        all_risks.extend(
            cls.detect_overallocations(
                allocations=dataset.get("allocations", []),
                employees=dataset.get("employees", []),
                thresholds=thresholds,
            )
        )

        # 2. Stale Skills
        all_risks.extend(
            cls.detect_stale_skills(
                employee_skills=dataset.get("employee_skills", []),
                as_of_date=as_of_date,
                thresholds=thresholds,
            )
        )

        # 3. Duplicate Demand
        all_risks.extend(
            cls.detect_duplicate_demand(
                demand_plans=dataset.get("demand_plans", []),
                thresholds=thresholds,
            )
        )

        # 4. Overlapping Allocations
        all_risks.extend(
            cls.detect_overlapping_allocations(
                allocations=dataset.get("allocations", []),
                thresholds=thresholds,
            )
        )

        # 5. Project Staffing Shortages
        all_risks.extend(
            cls.detect_project_staffing_shortages(
                projects=dataset.get("projects", []),
                demand_plans=dataset.get("demand_plans", []),
                allocations=dataset.get("allocations", []),
                as_of_date=as_of_date,
                thresholds=thresholds,
            )
        )

        return all_risks

    # -------------------------------------------------------------------------
    # 7. ASYNC DATABASE EVALUATION & PERSISTENCE
    # -------------------------------------------------------------------------
    @classmethod
    async def detect_workforce_risks_async(
        cls,
        session: AsyncSession,
        project_id: Optional[str] = None,
        as_of_date: Optional[date] = None,
        thresholds: PlanningThresholds = DEFAULT_THRESHOLDS,
    ) -> List[RiskDetectionItem]:
        """
        Asynchronously evaluate live database records to detect operational risks.
        Applies batch loading and targeted SQL filtering.
        """
        # Load active projects
        proj_stmt = select(Project)
        if project_id:
            proj_stmt = proj_stmt.where(Project.id == project_id)
        proj_res = await session.execute(proj_stmt)
        projects = proj_res.scalars().all()
        p_ids = [p.id for p in projects]

        # Load active demand plans
        dem_stmt = select(DemandPlan)
        if project_id:
            dem_stmt = dem_stmt.where(DemandPlan.project_id == project_id)
        dem_res = await session.execute(dem_stmt)
        demand_plans = dem_res.scalars().all()

        # Load active allocations
        alloc_stmt = select(Allocation).where(Allocation.is_active == True)
        if project_id:
            alloc_stmt = alloc_stmt.where(Allocation.project_id == project_id)
        alloc_res = await session.execute(alloc_stmt)
        allocations = alloc_res.scalars().all()

        # Load active employees
        emp_ids = list({a.employee_id for a in allocations})
        emp_stmt = select(Employee)
        if emp_ids and project_id:
            emp_stmt = emp_stmt.where(Employee.id.in_(emp_ids))
        emp_res = await session.execute(emp_stmt)
        employees = emp_res.scalars().all()

        # Load current employee skills
        skill_stmt = select(EmployeeSkill).where(EmployeeSkill.is_current == True)
        if emp_ids and project_id:
            skill_stmt = skill_stmt.where(EmployeeSkill.employee_id.in_(emp_ids))
        skill_res = await session.execute(skill_stmt)
        employee_skills = skill_res.scalars().all()

        all_risks: List[RiskDetectionItem] = []

        all_risks.extend(
            cls.detect_overallocations(
                allocations=allocations,
                employees=employees,
                thresholds=thresholds,
            )
        )
        all_risks.extend(
            cls.detect_stale_skills(
                employee_skills=employee_skills,
                as_of_date=as_of_date,
                thresholds=thresholds,
            )
        )
        all_risks.extend(
            cls.detect_duplicate_demand(
                demand_plans=demand_plans,
                thresholds=thresholds,
            )
        )
        all_risks.extend(
            cls.detect_overlapping_allocations(
                allocations=allocations,
                thresholds=thresholds,
            )
        )
        all_risks.extend(
            cls.detect_project_staffing_shortages(
                projects=projects,
                demand_plans=demand_plans,
                allocations=allocations,
                as_of_date=as_of_date,
                thresholds=thresholds,
            )
        )

        return all_risks

    @classmethod
    async def sync_issue_records_async(
        cls,
        session: AsyncSession,
        risks: List[RiskDetectionItem],
        as_of_date: Optional[date] = None,
    ) -> int:
        """
        Synchronize detected risks with the database `issue_records` table.
        Avoids redundant duplicate issue records by checking entity_id and issue_type.
        Returns count of newly recorded issue rows.
        """
        now_dt = datetime.now(timezone.utc)
        year = (as_of_date or date.today()).year
        inserted_count = 0

        # Load existing open issues
        existing_stmt = select(IssueRecord).where(
            IssueRecord.status.in_([IssueStatus.OPEN, IssueStatus.IN_PROGRESS])
        )
        existing_res = await session.execute(existing_stmt)
        existing_issues = existing_res.scalars().all()

        # Set of existing issue keys: (employee_id, project_id, issue_type)
        existing_keys = {
            (iss.employee_id, iss.project_id, iss.issue_type.value if hasattr(iss.issue_type, "value") else str(iss.issue_type))
            for iss in existing_issues
        }

        # Sequence offset for business IDs
        count_stmt = select(IssueRecord.business_id)
        count_res = await session.execute(count_stmt)
        existing_count = len(count_res.scalars().all())

        for r in risks:
            key = (r.employee_id, r.project_id, r.issue_type)
            if key in existing_keys:
                continue

            existing_keys.add(key)
            inserted_count += 1
            biz_id = f"ISS-{year}-{existing_count + inserted_count:06d}"
            pk_id = str(uuid.uuid4())

            new_issue = IssueRecord(
                id=pk_id,
                business_id=biz_id,
                project_id=r.project_id,
                employee_id=r.employee_id,
                issue_type=IssueType(r.issue_type),
                severity=IssueSeverity(r.severity),
                status=IssueStatus.OPEN,
                title=r.title[:200],
                description=r.description,
                detected_at=now_dt,
                created_at=now_dt,
                updated_at=now_dt,
            )
            session.add(new_issue)

        await session.commit()
        return inserted_count
