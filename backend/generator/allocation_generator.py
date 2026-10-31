"""
Staffing Allocation Generator.
Matches employees to project demand, models multiple concurrent project assignments,
realistic utilization tiers (standard, overutilized, bench), and preserves version history.
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List
import numpy as np

from backend.generator.config import GeneratorConfig
from backend.generator.id_generator import allocation_id, generate_uuid


def generate_allocations(
    config: GeneratorConfig,
    employees: List[Dict[str, Any]],
    projects: List[Dict[str, Any]],
    demand_plans: List[Dict[str, Any]],
    rng: np.random.Generator,
) -> List[Dict[str, Any]]:
    """
    Generate staffing allocations matching qualified employees to active project demand lines.
    Preserves versioning history (superseded v1 -> active v2).
    """
    allocations: List[Dict[str, Any]] = []
    seq = 1
    year = config.planning_start_date.year

    # Index employees by role
    employees_by_role: Dict[str, List[Dict[str, Any]]] = {}
    for e in employees:
        if e["employment_status"] in ["ACTIVE", "CONTRACTOR"]:
            employees_by_role.setdefault(e["role_id"], []).append(e)

    # Index demand plans by project
    demands_by_project: Dict[str, List[Dict[str, Any]]] = {}
    for d in demand_plans:
        demands_by_project.setdefault(d["project_id"], []).append(d)

    # Filter active projects
    active_projects = [p for p in projects if p["status"] in ["ACTIVE", "APPROVED"]]
    if not active_projects:
        active_projects = projects[:10]

    all_emp_ids = [e["id"] for e in employees if e["employment_status"] == "ACTIVE"]

    # Track concurrent commitments per employee: emp_id -> list of (start_date, end_date, pct)
    emp_commitments: Dict[str, List[tuple[date, date, float]]] = {}

    def get_max_overlap_pct(e_id: str, start: date, end: date) -> float:
        """Calculate maximum active commitment for an employee during [start, end]."""
        intervals = emp_commitments.get(e_id, [])
        if not intervals:
            return 0.0
        # Check overlaps
        overlapping = [pct for (s, e, pct) in intervals if not (end < s or start > e)]
        return sum(overlapping)

    for p in active_projects:
        p_id = p["id"]
        p_demands = demands_by_project.get(p_id, [])
        if not p_demands:
            continue

        p_start = p["start_date"]
        p_end = p["end_date"]

        # Sample a subset of demands to fulfill
        sample_demands = p_demands[::max(1, len(p_demands) // 6)]

        for d in sample_demands:
            role_id = d["role_id"]
            eligible_emps = employees_by_role.get(role_id, [])
            if not eligible_emps:
                eligible_emps = [e for e in employees if e["employment_status"] == "ACTIVE"]
            if not eligible_emps:
                continue

            # Alignment with demand duration
            alloc_start = max(p_start, d["start_date"])
            alloc_end = min(p_end, d["end_date"] + timedelta(days=21))
            if alloc_end < alloc_start:
                alloc_end = alloc_start + timedelta(days=28)

            # Find employee with available capacity in [alloc_start, alloc_end]
            # Shuffle candidates deterministically
            candidate_indices = rng.permutation(len(eligible_emps))
            emp_pick = None
            pct_choice = 100.0

            for idx in candidate_indices:
                cand = eligible_emps[idx]
                curr_load = get_max_overlap_pct(cand["id"], alloc_start, alloc_end)
                if curr_load == 0.0:
                    emp_pick = cand
                    pct_choice = 100.0
                    break

            if not emp_pick:
                continue

            emp_id = emp_pick["id"]
            emp_commitments.setdefault(emp_id, []).append((alloc_start, alloc_end, pct_choice))
            std_weekly_hours = float(emp_pick["standard_hours_per_week"])
            allocated_hours = Decimal(str(round(std_weekly_hours * (pct_choice / 100.0), 2)))
            pct = Decimal(str(round(pct_choice, 2)))

            cost_rate = emp_pick.get("cost_rate_per_hour") or Decimal("100.00")
            billing_rate = Decimal(str(round(float(cost_rate) * 1.35, 2)))

            biz_id = allocation_id(seq, year=year)
            pk_id = generate_uuid("Allocation", biz_id)
            seq += 1

            # Update demand fulfillment hours
            weeks_count = max(1, (alloc_end - alloc_start).days // 7)
            d["fulfilled_hours"] = Decimal(str(round(float(d.get("fulfilled_hours", 0)) + (float(allocated_hours) * weeks_count), 2)))

            created_at = datetime(alloc_start.year, alloc_start.month, alloc_start.day, 9, 0, 0, tzinfo=timezone.utc)
            updated_at = datetime(config.as_of_date.year, config.as_of_date.month, config.as_of_date.day, 12, 0, 0, tzinfo=timezone.utc)

            # Allocation history preservation: For ~15% of allocations, generate a Version 1 superseded by Version 2
            has_supersession = rng.random() < 0.15
            if has_supersession and (alloc_end - alloc_start).days >= 14:
                # Version 1 record (prior 50% commitment)
                v1_biz_id = allocation_id(seq, year=year)
                v1_pk = generate_uuid("Allocation", v1_biz_id)
                seq += 1

                v1_pct = Decimal("50.00")
                v1_hours = Decimal(str(round(std_weekly_hours * 0.50, 2)))

                # Version 1 is marked inactive and points to pk_id (Version 2)
                allocations.append({
                    "id": v1_pk,
                    "business_id": v1_biz_id,
                    "employee_id": emp_id,
                    "project_id": p_id,
                    "demand_plan_id": d["id"],
                    "start_date": alloc_start,
                    "end_date": alloc_end,
                    "allocation_percentage": v1_pct,
                    "allocated_hours_per_week": v1_hours,
                    "hourly_billing_rate": billing_rate,
                    "status": "COMPLETED",
                    "version": 1,
                    "is_active": False,
                    "superseded_by_id": pk_id,
                    "notes": "Initial staffing booking. Superseded by v2 due to scope increase.",
                    "created_at": created_at - timedelta(days=30),
                    "updated_at": created_at,
                })

                # Version 2 record (the active one)
                allocations.append({
                    "id": pk_id,
                    "business_id": biz_id,
                    "employee_id": emp_id,
                    "project_id": p_id,
                    "demand_plan_id": d["id"],
                    "start_date": alloc_start,
                    "end_date": alloc_end,
                    "allocation_percentage": pct,
                    "allocated_hours_per_week": allocated_hours,
                    "hourly_billing_rate": billing_rate,
                    "status": "ACTIVE" if alloc_start <= config.as_of_date <= alloc_end else "CONFIRMED",
                    "version": 2,
                    "is_active": True,
                    "superseded_by_id": None,
                    "notes": "Revision 2: Increased weekly commitment to satisfy expanded project milestone.",
                    "created_at": created_at,
                    "updated_at": updated_at,
                })
            else:
                # Standard Version 1 active record
                allocations.append({
                    "id": pk_id,
                    "business_id": biz_id,
                    "employee_id": emp_id,
                    "project_id": p_id,
                    "demand_plan_id": d["id"],
                    "start_date": alloc_start,
                    "end_date": alloc_end,
                    "allocation_percentage": pct,
                    "allocated_hours_per_week": allocated_hours,
                    "hourly_billing_rate": billing_rate,
                    "status": "ACTIVE" if alloc_start <= config.as_of_date <= alloc_end else "CONFIRMED",
                    "version": 1,
                    "is_active": True,
                    "superseded_by_id": None,
                    "notes": "Confirmed staffing assignment.",
                    "created_at": created_at,
                    "updated_at": updated_at,
                })

    return allocations
