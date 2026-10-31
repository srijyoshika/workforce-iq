"""
Controlled Anomaly Injection Engine for WorkforceIQ.

Injects deliberate, parameterized workforce business anomalies AFTER baseline data
passes relational integrity and validation checks:
1. OVERALLOCATION: Exceeds employee capacity; calculates exact excess hours.
2. STALE_SKILL: Skill verification older than allowed validity period while remaining current.
3. DUPLICATE_DEMAND: Second delivery of existing demand record using delivery identity.
4. OVERLAPPING_ALLOCATION: Overlapping project time intervals; calculates exact overlap time.

Preserves original source records and generates decoupled Ground Truth expectations.
"""

from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Tuple
import numpy as np

from backend.generator.config import GeneratorConfig
from backend.generator.ground_truth import GroundTruthRecord
from backend.generator.id_generator import (
    allocation_id,
    demand_plan_id,
    employee_skill_id,
    generate_uuid,
)


def inject_anomalies(
    dataset: Dict[str, List[Dict[str, Any]]],
    config: GeneratorConfig,
    anomaly_counts: Dict[str, int] = None,
    seed: int = 20261022,
) -> Tuple[Dict[str, List[Dict[str, Any]]], List[GroundTruthRecord]]:
    """
    Inject controlled anomalies into a validated baseline workforce dataset.
    Returns:
        anomalous_dataset: Dataset containing preserved original records plus deliberate anomalies.
        ground_truth_records: Decoupled ground truth specifications for evaluation.
    """
    rng = np.random.default_rng(seed)
    anom_data = {k: list(v) for k, v in dataset.items()}
    ground_truth: List[GroundTruthRecord] = []

    # Default count per anomaly type based on scale
    if anomaly_counts is None:
        if config.scale == "starter":
            anomaly_counts = {
                "OVERALLOCATION": 3,
                "STALE_SKILL": 3,
                "DUPLICATE_DEMAND": 3,
                "OVERLAPPING_ALLOCATION": 3,
            }
        else:
            anomaly_counts = {
                "OVERALLOCATION": 15,
                "STALE_SKILL": 15,
                "DUPLICATE_DEMAND": 15,
                "OVERLAPPING_ALLOCATION": 15,
            }

    year = config.planning_start_date.year
    scenario_counter = 1

    # -------------------------------------------------------------------------
    # 1. ANOMALY: OVERALLOCATION
    # Create an allocation that exceeds the employee's available capacity.
    # Preserve original records. Calculate exact excess hours.
    # -------------------------------------------------------------------------
    target_overalloc = anomaly_counts.get("OVERALLOCATION", 0)
    existing_allocations = anom_data["allocations"]
    alloc_seq = len(existing_allocations) + 1000

    # Find active employees who already have at least one active allocation
    alloc_emp_map: Dict[str, List[Dict[str, Any]]] = {}
    for a in existing_allocations:
        if a.get("is_active"):
            alloc_emp_map.setdefault(a["employee_id"], []).append(a)

    eligible_emps = [e for e in anom_data["employees"] if e["id"] in alloc_emp_map and e["employment_status"] == "ACTIVE"]
    rng.shuffle(eligible_emps)

    injected_overalloc = 0
    used_emp_ids: Set[str] = set()

    for emp in eligible_emps:
        if injected_overalloc >= target_overalloc:
            break

        emp_id = emp["id"]
        used_emp_ids.add(emp_id)
        emp_allocs = alloc_emp_map[emp_id]
        base_alloc = emp_allocs[0]
        capacity_hours = float(emp["standard_hours_per_week"])

        # Project to allocate against (same project as base_alloc to simulate single-project capacity overload)
        target_project_id = base_alloc["project_id"]

        # Time window overlapping with base_alloc
        alloc_start = base_alloc["start_date"]
        alloc_end = min(base_alloc["end_date"], alloc_start + timedelta(days=28))
        if alloc_end <= alloc_start:
            alloc_end = alloc_start + timedelta(days=14)

        # Existing allocated hours in this window
        existing_hours_in_window = float(base_alloc["allocated_hours_per_week"])
        
        # Calculate extra hours that will cause overallocation by 12 to 24 hours
        excess_hours_target = round(float(rng.uniform(12.0, 24.0)), 2)
        additional_hours = round(max(10.0, (capacity_hours - existing_hours_in_window) + excess_hours_target), 2)
        total_hours = round(existing_hours_in_window + additional_hours, 2)
        exact_excess = round(total_hours - capacity_hours, 2)

        biz_id = allocation_id(alloc_seq, year=year)
        pk_id = generate_uuid("Allocation", biz_id)
        alloc_seq += 1

        new_alloc = {
            "id": pk_id,
            "business_id": biz_id,
            "employee_id": emp_id,
            "project_id": target_project_id,
            "demand_plan_id": None,
            "start_date": alloc_start,
            "end_date": alloc_end,
            "allocation_percentage": Decimal(str(round((additional_hours / capacity_hours) * 100.0, 2))),
            "allocated_hours_per_week": Decimal(str(additional_hours)),
            "hourly_billing_rate": Decimal("150.00"),
            "status": "ACTIVE",
            "version": 1,
            "is_active": True,
            "superseded_by_id": None,
            "notes": "Deliberately injected overallocation anomaly for capacity stress-testing.",
            "created_at": datetime(alloc_start.year, alloc_start.month, alloc_start.day, 10, 0, 0, tzinfo=timezone.utc),
            "updated_at": datetime(config.as_of_date.year, config.as_of_date.month, config.as_of_date.day, 12, 0, 0, tzinfo=timezone.utc),
        }

        anom_data["allocations"].append(new_alloc)
        injected_overalloc += 1

        ground_truth.append(
            GroundTruthRecord(
                scenario_id=f"SCN-ANOMALY-OVERALLOC-{scenario_counter:04d}",
                entity_type="Allocation",
                entity_id=pk_id,
                issue_type="OVERALLOCATION",
                expected_detection=True,
                expected_severity="CRITICAL",
                expected_action="REDUCE_ALLOCATION_HOURS",
                expected_value={
                    "employee_id": emp_id,
                    "allocation_id": pk_id,
                    "business_id": biz_id,
                    "capacity_hours": capacity_hours,
                    "total_allocated_hours": total_hours,
                    "excess_hours": exact_excess,
                    "window_start": str(alloc_start),
                    "window_end": str(alloc_end),
                },
                rule_version="1.0.0",
            )
        )
        scenario_counter += 1

    # -------------------------------------------------------------------------
    # 2. ANOMALY: STALE_SKILL
    # Create an employee skill profile whose verification date is older than the
    # allowed validity period (730 days). Marked current (is_current = True).
    # Preserve original records.
    # -------------------------------------------------------------------------
    target_stale = anomaly_counts.get("STALE_SKILL", 0)
    current_skills = [es for es in anom_data["employee_skills"] if es["is_current"] and es.get("verified_at")]
    rng.shuffle(current_skills)

    injected_stale = 0
    validity_threshold_days = 730  # 2 years enterprise validity policy

    for sk in current_skills:
        if injected_stale >= target_stale:
            break

        # Set verification date to between 800 and 1200 days before as_of_date
        days_stale = int(rng.integers(800, 1200))
        stale_verified_date = config.as_of_date - timedelta(days=days_stale)
        stale_verified_at = datetime(
            stale_verified_date.year, stale_verified_date.month, stale_verified_date.day, 14, 0, 0, tzinfo=timezone.utc
        )
        days_overdue = days_stale - validity_threshold_days

        # Mutate the verification date while preserving is_current=True and all other fields
        sk["verified_at"] = stale_verified_at
        sk["is_current"] = True
        injected_stale += 1

        ground_truth.append(
            GroundTruthRecord(
                scenario_id=f"SCN-ANOMALY-STALE-SKL-{scenario_counter:04d}",
                entity_type="EmployeeSkill",
                entity_id=sk["id"],
                issue_type="STALE_SKILL",
                expected_detection=True,
                expected_severity="HIGH",
                expected_action="REVERIFY_EMPLOYEE_SKILL",
                expected_value={
                    "employee_id": sk["employee_id"],
                    "skill_id": sk["skill_id"],
                    "business_id": sk["business_id"],
                    "verified_at": stale_verified_at.isoformat(),
                    "as_of_date": str(config.as_of_date),
                    "elapsed_days": days_stale,
                    "validity_threshold_days": validity_threshold_days,
                    "days_overdue": days_overdue,
                },
                rule_version="1.0.0",
            )
        )
        scenario_counter += 1

    # -------------------------------------------------------------------------
    # 3. ANOMALY: DUPLICATE_DEMAND
    # Create a second delivery of an existing demand record.
    # Retain both source records. Use business-key and source-delivery identity.
    # -------------------------------------------------------------------------
    target_dup = anomaly_counts.get("DUPLICATE_DEMAND", 0)
    eligible_demands = [d for d in anom_data["demand_plans"] if d["status"] in ["APPROVED", "SUBMITTED"]]
    rng.shuffle(eligible_demands)

    injected_dup = 0
    for orig_d in eligible_demands:
        if injected_dup >= target_dup:
            break

        # Duplicate the demand record with a new UUID and distinct duplicate business id
        dup_biz_id = f"{orig_d['business_id']}-DUP"
        dup_pk = generate_uuid("DemandPlan", dup_biz_id)

        # Exact duplicate of delivery identity: (project_id, role_id, start_date, end_date, primary_skill_id)
        dup_record = deepcopy(orig_d)
        dup_record["id"] = dup_pk
        dup_record["business_id"] = dup_biz_id
        dup_record["notes"] = f"Duplicate delivery of requirement {orig_d['business_id']}."
        dup_record["created_at"] = orig_d["created_at"] + timedelta(minutes=5)

        anom_data["demand_plans"].append(dup_record)
        injected_dup += 1

        ground_truth.append(
            GroundTruthRecord(
                scenario_id=f"SCN-ANOMALY-DUP-DEMAND-{scenario_counter:04d}",
                entity_type="DemandPlan",
                entity_id=dup_pk,
                issue_type="DUPLICATE_DEMAND",
                expected_detection=True,
                expected_severity="MEDIUM",
                expected_action="DE_DUPLICATE_DEMAND_LINE",
                expected_value={
                    "original_demand_id": orig_d["id"],
                    "duplicate_demand_id": dup_pk,
                    "original_business_id": orig_d["business_id"],
                    "duplicate_business_id": dup_biz_id,
                    "project_id": orig_d["project_id"],
                    "role_id": orig_d["role_id"],
                    "start_date": str(orig_d["start_date"]),
                    "end_date": str(orig_d["end_date"]),
                    "delivery_identity": f"{orig_d['project_id']}:{orig_d['role_id']}:{orig_d['start_date']}:{orig_d['end_date']}",
                },
                rule_version="1.0.0",
            )
        )
        scenario_counter += 1

    # -------------------------------------------------------------------------
    # 4. ANOMALY: OVERLAPPING_ALLOCATION
    # Assign one employee to overlapping project time intervals.
    # Calculate exact overlapping time. Preserve both assignments.
    # -------------------------------------------------------------------------
    target_overlap = anomaly_counts.get("OVERLAPPING_ALLOCATION", 0)
    injected_overlap = 0

    # Map existing active allocation windows per employee
    existing_emp_intervals: Dict[str, List[Tuple[date, date]]] = {}
    for a in anom_data["allocations"]:
        if a.get("is_active"):
            existing_emp_intervals.setdefault(a["employee_id"], []).append((a["start_date"], a["end_date"]))

    active_employees = [e for e in anom_data["employees"] if e["employment_status"] == "ACTIVE" and e["id"] not in used_emp_ids]
    rng.shuffle(active_employees)
    active_projects = [p for p in anom_data["projects"] if p["status"] == "ACTIVE"]

    if len(active_projects) >= 2:
        for emp in active_employees:
            if injected_overlap >= target_overlap:
                break

            emp_id = emp["id"]
            proj_1 = active_projects[(injected_overlap * 2) % len(active_projects)]
            proj_2 = active_projects[(injected_overlap * 2 + 1) % len(active_projects)]
            std_hours = float(emp["standard_hours_per_week"])

            # Schedule intervals with deliberate overlap:
            # Interval 1: Day 60 to Day 150 (90 days)
            # Interval 2: Day 120 to Day 210 (90 days)
            # Overlap: Day 120 to Day 150 (31 days)
            t1_start = config.planning_start_date + timedelta(days=60 + (injected_overlap * 14))
            t1_end = t1_start + timedelta(days=90)

            t2_start = t1_start + timedelta(days=60)  # Starts 30 days before T1 ends
            t2_end = t2_start + timedelta(days=90)

            # Ensure this employee has no pre-existing allocations in [t1_start, t2_end]
            has_conflict = any(
                not (t2_end < s or t1_start > e)
                for (s, e) in existing_emp_intervals.get(emp_id, [])
            )
            if has_conflict:
                continue

            overlap_start = max(t1_start, t2_start)
            overlap_end = min(t1_end, t2_end)
            overlap_days = (overlap_end - overlap_start).days + 1
            weekly_committed = std_hours  # Both are full-time assignments
            overlap_hours = round((overlap_days / 7.0) * weekly_committed, 2)

            biz_id_1 = allocation_id(alloc_seq, year=year)
            pk_1 = generate_uuid("Allocation", biz_id_1)
            alloc_seq += 1

            biz_id_2 = allocation_id(alloc_seq, year=year)
            pk_2 = generate_uuid("Allocation", biz_id_2)
            alloc_seq += 1

            split_pct = Decimal("50.00")
            split_hours = Decimal(str(round(std_hours * 0.50, 2)))

            alloc_1 = {
                "id": pk_1,
                "business_id": biz_id_1,
                "employee_id": emp_id,
                "project_id": proj_1["id"],
                "demand_plan_id": None,
                "start_date": t1_start,
                "end_date": t1_end,
                "allocation_percentage": split_pct,
                "allocated_hours_per_week": split_hours,
                "hourly_billing_rate": Decimal("140.00"),
                "status": "CONFIRMED",
                "version": 1,
                "is_active": True,
                "superseded_by_id": None,
                "notes": f"Primary project engagement on {proj_1['business_id']}.",
                "created_at": datetime(t1_start.year, t1_start.month, t1_start.day, 9, 0, 0, tzinfo=timezone.utc),
                "updated_at": datetime(config.as_of_date.year, config.as_of_date.month, config.as_of_date.day, 12, 0, 0, tzinfo=timezone.utc),
            }

            alloc_2 = {
                "id": pk_2,
                "business_id": biz_id_2,
                "employee_id": emp_id,
                "project_id": proj_2["id"],
                "demand_plan_id": None,
                "start_date": t2_start,
                "end_date": t2_end,
                "allocation_percentage": split_pct,
                "allocated_hours_per_week": split_hours,
                "hourly_billing_rate": Decimal("140.00"),
                "status": "CONFIRMED",
                "version": 1,
                "is_active": True,
                "superseded_by_id": None,
                "notes": f"Conflicting overlapping engagement on {proj_2['business_id']}.",
                "created_at": datetime(t2_start.year, t2_start.month, t2_start.day, 9, 0, 0, tzinfo=timezone.utc),
                "updated_at": datetime(config.as_of_date.year, config.as_of_date.month, config.as_of_date.day, 12, 0, 0, tzinfo=timezone.utc),
            }

            anom_data["allocations"].append(alloc_1)
            anom_data["allocations"].append(alloc_2)
            existing_emp_intervals.setdefault(emp_id, []).extend([(t1_start, t1_end), (t2_start, t2_end)])
            injected_overlap += 1

            ground_truth.append(
                GroundTruthRecord(
                    scenario_id=f"SCN-ANOMALY-OVERLAP-ALLOC-{scenario_counter:04d}",
                    entity_type="Allocation",
                    entity_id=pk_2,
                    issue_type="OVERLAPPING_ALLOCATION",
                    expected_detection=True,
                    expected_severity="HIGH",
                    expected_action="RESOLVE_SCHEDULE_OVERLAP",
                    expected_value={
                        "employee_id": emp_id,
                        "primary_allocation_id": pk_1,
                        "conflicting_allocation_id": pk_2,
                        "primary_business_id": biz_id_1,
                        "conflicting_business_id": biz_id_2,
                        "overlap_start": str(overlap_start),
                        "overlap_end": str(overlap_end),
                        "overlap_days": overlap_days,
                        "overlap_hours": overlap_hours,
                    },
                    rule_version="1.0.0",
                )
            )
            scenario_counter += 1

    return anom_data, ground_truth
