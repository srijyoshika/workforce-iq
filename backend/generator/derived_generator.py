"""
Derived Intelligence and Telemetry Generator for WorkforceIQ:
- GapAnalysis: Computes deficits between planned demand and fulfilled allocations.
- Recommendation: Generates AI-assisted mitigation advice for identified skill deficits.
- IssueRecord: Detects operational risks, overutilized staff (>100%), and unstaffed roles.
- ScenarioRun: Records the baseline simulation run and optimization telemetry.
- AuditEvent: Emits compliance audit log entries for all generated batches.
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List
import numpy as np

from backend.generator.config import GeneratorConfig
from backend.generator.id_generator import (
    audit_event_id,
    gap_analysis_id,
    generate_uuid,
    issue_record_id,
    recommendation_id,
    scenario_run_id,
)


def generate_derived_intelligence(
    config: GeneratorConfig,
    employees: List[Dict[str, Any]],
    projects: List[Dict[str, Any]],
    demand_plans: List[Dict[str, Any]],
    allocations: List[Dict[str, Any]],
    skills: List[Dict[str, Any]],
    rng: np.random.Generator,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Calculate derived analytical datasets based on generated demand, allocations, and capacity.
    """
    year = config.planning_start_date.year
    gaps: List[Dict[str, Any]] = []
    recommendations: List[Dict[str, Any]] = []
    issues: List[Dict[str, Any]] = []
    scenarios: List[Dict[str, Any]] = []
    audit_events: List[Dict[str, Any]] = []

    # Map allocations by demand_plan_id
    allocations_by_demand: Dict[str, List[Dict[str, Any]]] = {}
    for a in allocations:
        if a["demand_plan_id"] and a["is_active"]:
            allocations_by_demand.setdefault(a["demand_plan_id"], []).append(a)

    # 1. Generate GapAnalysis for unfulfilled or partially fulfilled demand
    gap_seq = 1
    rec_seq = 1
    issue_seq = 1

    # Filter demands that have zero or insufficient fulfilled hours
    unfulfilled_demands = [d for d in demand_plans if float(d["fulfilled_hours"]) < float(d["required_hours"])]
    sample_gaps = unfulfilled_demands[:min(len(unfulfilled_demands), max(10, len(projects) * 2))]

    for d in sample_gaps:
        biz_id = gap_analysis_id(gap_seq, year=year)
        pk_id = generate_uuid("GapAnalysis", biz_id)
        gap_seq += 1

        req_headcount = d["required_headcount"]
        allocated_count = len(allocations_by_demand.get(d["id"], []))
        deficit = max(1, req_headcount - allocated_count)

        priority = d["priority"]
        severity = "CRITICAL" if priority == 1 else "HIGH" if priority == 2 else "MEDIUM"
        target_date = d["start_date"]

        created_at = datetime(target_date.year, target_date.month, target_date.day, 10, 0, 0, tzinfo=timezone.utc)
        updated_at = datetime(config.as_of_date.year, config.as_of_date.month, config.as_of_date.day, 12, 0, 0, tzinfo=timezone.utc)

        gaps.append({
            "id": pk_id,
            "business_id": biz_id,
            "project_id": d["project_id"],
            "demand_plan_id": d["id"],
            "skill_id": d["primary_skill_id"],
            "required_proficiency": d["min_proficiency"],
            "required_headcount": req_headcount,
            "available_headcount": allocated_count,
            "deficit_headcount": deficit,
            "severity": severity,
            "status": "IDENTIFIED",
            "target_fulfillment_date": target_date,
            "analysis_date": config.as_of_date,
            "created_at": created_at,
            "updated_at": updated_at,
        })

        # 2. Generate Recommendation for the identified gap
        rec_biz = recommendation_id(rec_seq, year=year)
        rec_pk = generate_uuid("Recommendation", rec_biz)
        rec_seq += 1

        rec_type = rng.choice(
            ["INTERNAL_REALLOCATION", "TRAINING_UPSKILL", "EXTERNAL_HIRE", "CONTRACTOR_CONTINGENT"],
            p=[0.40, 0.30, 0.15, 0.15],
        )
        conf_score = Decimal(str(round(rng.uniform(0.780, 0.960), 3)))

        rec_target_emp = employees[rng.integers(0, len(employees))]["id"] if rec_type in ["INTERNAL_REALLOCATION", "TRAINING_UPSKILL"] else None

        recommendations.append({
            "id": rec_pk,
            "business_id": rec_biz,
            "gap_analysis_id": pk_id,
            "target_employee_id": rec_target_emp,
            "target_project_id": d["project_id"],
            "type": rec_type,
            "confidence_score": conf_score,
            "impact_summary": f"Recommended {rec_type.replace('_', ' ')} to eliminate staffing deficit of {deficit} FTE for Project {d['project_id']}.",
            "status": "GENERATED",
            "estimated_cost": Decimal(str(round(rng.uniform(2500.00, 15000.00), 2))),
            "time_to_impact_days": int(rng.integers(14, 60)),
            "reviewed_by_id": None,
            "reviewed_at": None,
            "created_at": created_at,
            "updated_at": updated_at,
        })

    # 3. Detect Operational Issues (Overutilized employees & Unfulfilled Critical Demand)
    emp_alloc_totals: Dict[str, float] = {}
    for a in allocations:
        if a["is_active"]:
            emp_alloc_totals[a["employee_id"]] = emp_alloc_totals.get(a["employee_id"], 0.0) + float(a["allocation_percentage"])

    overloaded_emps = [e_id for e_id, total_pct in emp_alloc_totals.items() if total_pct > 100.0]
    for e_id in overloaded_emps[:20]:
        tot = emp_alloc_totals[e_id]
        iss_biz = issue_record_id(issue_seq, year=year)
        iss_pk = generate_uuid("IssueRecord", iss_biz)
        issue_seq += 1

        issues.append({
            "id": iss_pk,
            "business_id": iss_biz,
            "project_id": None,
            "employee_id": e_id,
            "issue_type": "CAPACITY_OVERLOAD",
            "severity": "HIGH",
            "status": "OPEN",
            "title": f"Employee Staffing Overload: {tot:.1f}% Total Allocation",
            "description": f"Employee is committed across multiple concurrent engagements exceeding 100% capacity threshold by {tot - 100.0:.1f}%.",
            "detected_at": datetime(year, 3, 15, 8, 30, 0, tzinfo=timezone.utc),
            "resolved_at": None,
            "created_at": datetime(year, 3, 15, 8, 30, 0, tzinfo=timezone.utc),
            "updated_at": datetime(config.as_of_date.year, config.as_of_date.month, config.as_of_date.day, 12, 0, 0, tzinfo=timezone.utc),
        })

    # 4. Scenario Run Record
    scn_biz = scenario_run_id(1, year=year)
    scn_pk = generate_uuid("ScenarioRun", scn_biz)
    scenarios.append({
        "id": scn_pk,
        "business_id": scn_biz,
        "name": f"FY{year} Enterprise Baseline Planning Simulation",
        "description": "Baseline workforce supply, demand, and skill feasibility optimization run.",
        "status": "COMPLETED",
        "parameters": {
            "scale": config.scale,
            "seed": config.seed,
            "planning_year": year,
            "total_employees": config.scale_config.employee_count,
            "total_projects": config.scale_config.project_count,
            "as_of_date": str(config.as_of_date),
        },
        "simulation_results": {
            "total_demand_lines": len(demand_plans),
            "total_allocations": len(allocations),
            "identified_gaps_count": len(gaps),
            "overloaded_personnel_count": len(overloaded_emps),
            "average_staffing_utilization_pct": 87.4,
        },
        "executed_by_id": employees[0]["id"] if employees else None,
        "execution_duration_ms": 342,
        "created_at": datetime(year, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(config.as_of_date.year, config.as_of_date.month, config.as_of_date.day, 12, 0, 0, tzinfo=timezone.utc),
    })

    # 5. Audit Event Records
    aud_biz = audit_event_id(1, year=year)
    aud_pk = generate_uuid("AuditEvent", aud_biz)
    audit_events.append({
        "id": aud_pk,
        "business_id": aud_biz,
        "entity_type": "DataGenerator",
        "entity_id": scn_biz,
        "action": "SIMULATE",
        "performed_by_id": employees[0]["id"] if employees else None,
        "timestamp": datetime(config.as_of_date.year, config.as_of_date.month, config.as_of_date.day, 12, 0, 0, tzinfo=timezone.utc),
        "ip_address": "127.0.0.1",
        "old_values": None,
        "new_values": {"status": "COMPLETED", "scale": config.scale, "seed": config.seed},
        "reason": "Synthetic workforce generator batch execution.",
    })

    return {
        "gap_analyses": gaps,
        "recommendations": recommendations,
        "issue_records": issues,
        "scenario_runs": scenarios,
        "audit_events": audit_events,
    }

