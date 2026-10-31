"""
WorkforceIQ Enterprise Scenario Planning & Simulation Service.

Provides complete what-if simulation modeling with strict baseline protection:
- Simulates demand surges / contractions
- Injects hypothetical projects
- Modifies delivery priorities & timelines
- Simulates unexpected employee leaves & workforce reductions
- Adjusts training and hiring budget caps
- Integrates Google OR-Tools CP-SAT optimizer benchmarked against Greedy baseline
- Emits comprehensive audit trails and traceable recommendation artifacts
"""

import copy
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import time
from typing import Any, Dict, List, Optional, Tuple
import uuid

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

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
    ScenarioStatus,
)
from app.models.intelligence import ScenarioRun
from app.models.project import DemandPlan, Project
from app.models.skill import EmployeeSkill, Skill
from app.services.optimization.baseline_solver import GreedyBaselineSolver
from app.services.optimization.solver import OrToolsWorkforceSolver
from app.services.recommendation.engine import RecommendationEngine


class ScenarioEngineService:
    """Enterprise Scenario Planning Engine with guaranteed zero baseline mutation."""

    @classmethod
    async def run_scenario_simulation(
        cls,
        session: AsyncSession,
        name: str,
        description: Optional[str],
        parameters: Dict[str, Any],
        executed_by_id: Optional[str] = None,
    ) -> ScenarioRun:
        """
        Execute what-if workforce scenario without altering live database records.
        """
        start_clock = time.perf_counter()
        now_dt = datetime.now(timezone.utc)
        today = now_dt.date()

        # -------------------------------------------------------------
        # STEP 1: Load Live Baseline Data into Memory (Cloned Dictionaries)
        # -------------------------------------------------------------
        # A. Employees
        emp_res = await session.execute(select(Employee))
        db_employees = emp_res.scalars().all()
        employees: List[Dict[str, Any]] = [
            {
                "id": e.id,
                "business_id": e.business_id,
                "first_name": e.first_name,
                "last_name": e.last_name,
                "department": e.department,
                "location": e.location,
                "employment_status": e.employment_status.value if hasattr(e.employment_status, "value") else str(e.employment_status),
                "hire_date": e.hire_date,
                "exit_date": e.exit_date,
                "standard_hours_per_week": float(e.standard_hours_per_week),
                "cost_rate_per_hour": float(e.cost_rate_per_hour or 65.0),
            }
            for e in db_employees
        ]

        # B. Employee Skills
        skl_res = await session.execute(select(EmployeeSkill))
        db_skills = skl_res.scalars().all()
        employee_skills: List[Dict[str, Any]] = [
            {
                "id": s.id,
                "employee_id": s.employee_id,
                "skill_id": s.skill_id,
                "proficiency_level": s.proficiency_level,
                "verification_status": s.verification_status.value if hasattr(s.verification_status, "value") else str(s.verification_status),
                "verified_at": s.verified_at,
                "is_current": s.is_current,
            }
            for s in db_skills
        ]

        # C. Projects
        prj_res = await session.execute(select(Project))
        db_projects = prj_res.scalars().all()
        projects: List[Dict[str, Any]] = [
            {
                "id": p.id,
                "business_id": p.business_id,
                "name": p.name,
                "code": p.code,
                "start_date": p.start_date,
                "end_date": p.end_date,
                "status": p.status.value if hasattr(p.status, "value") else str(p.status),
                "priority": getattr(p, "priority", 2),
                "budget": float(p.budget or 0.0),
            }
            for p in db_projects
        ]

        # D. Demand Plans
        dem_res = await session.execute(select(DemandPlan))
        db_demands = dem_res.scalars().all()
        demands: List[Dict[str, Any]] = [
            {
                "id": d.id,
                "business_id": d.business_id,
                "project_id": d.project_id,
                "role_id": d.role_id,
                "primary_skill_id": d.primary_skill_id,
                "start_date": d.start_date,
                "end_date": d.end_date,
                "required_headcount": d.required_headcount,
                "required_hours": float(d.required_hours or (d.required_headcount * 40.0)),
                "fulfilled_hours": float(d.fulfilled_hours or 0.0),
                "min_proficiency": d.min_proficiency,
                "status": d.status.value if hasattr(d.status, "value") else str(d.status),
                "priority": d.priority,
            }
            for d in db_demands
        ]

        # E. Existing Allocations
        alloc_res = await session.execute(select(Allocation).where(Allocation.is_active == True))
        db_allocs = alloc_res.scalars().all()
        allocations: List[Dict[str, Any]] = [
            {
                "id": a.id,
                "employee_id": a.employee_id,
                "project_id": a.project_id,
                "start_date": a.start_date,
                "end_date": a.end_date,
                "allocation_percentage": float(a.allocation_percentage),
                "allocated_hours_per_week": float(a.allocated_hours_per_week),
                "status": a.status.value if hasattr(a.status, "value") else str(a.status),
                "is_active": a.is_active,
            }
            for a in db_allocs
        ]

        # F. Availabilities & Leaves
        avail_res = await session.execute(select(Availability))
        db_avails = avail_res.scalars().all()
        availabilities: List[Dict[str, Any]] = [
            {
                "id": av.id,
                "employee_id": av.employee_id,
                "start_date": av.start_date,
                "end_date": av.end_date,
                "availability_type": av.availability_type.value if hasattr(av.availability_type, "value") else str(av.availability_type),
                "capacity_percentage": float(av.capacity_percentage),
                "available_hours_per_day": float(av.available_hours_per_day),
                "is_approved": av.is_approved,
            }
            for av in db_avails
        ]

        # -------------------------------------------------------------
        # STEP 2: Baseline Protection Checksum & Metadata
        # -------------------------------------------------------------
        baseline_version = f"BASELINE-v1.0-{today.isoformat()}"
        baseline_records_count = {
            "employees": len(employees),
            "projects": len(projects),
            "demands": len(demands),
            "allocations": len(allocations),
            "skills": len(employee_skills),
        }

        # -------------------------------------------------------------
        # STEP 3: Apply Scenario What-If Modifications to Cloned State
        # -------------------------------------------------------------
        # A. Demand Surge / Contraction
        demand_surge_pct = float(parameters.get("demand_surge_percentage", 0.0))
        demand_factor = float(parameters.get("demand_factor", 1.0 + (demand_surge_pct / 100.0)))
        if demand_factor != 1.0:
            for d in demands:
                d["required_hours"] = round(d["required_hours"] * demand_factor, 1)

        # B. Hypothetical Projects & Associated Demands
        hypothetical_projects = parameters.get("hypothetical_projects", [])
        for hp in hypothetical_projects:
            hp_id = hp.get("id") or str(uuid.uuid4())
            new_prj = {
                "id": hp_id,
                "business_id": f"HYPO-PRJ-{hp.get('code', 'NEW')}",
                "name": hp.get("name", "Hypothetical Initiative"),
                "code": hp.get("code", "HYPO"),
                "start_date": hp.get("start_date", today),
                "end_date": hp.get("end_date", today + timedelta(days=90)),
                "status": "PIPELINE",
                "priority": int(hp.get("priority", 2)),
                "budget": float(hp.get("budget", 100000.0)),
            }
            projects.append(new_prj)

            for hd in hp.get("demands", []):
                demands.append({
                    "id": hd.get("id") or str(uuid.uuid4()),
                    "business_id": f"HYPO-DEM-{len(demands) + 1}",
                    "project_id": hp_id,
                    "role_id": hd.get("role_id", "ROLE-DEV"),
                    "primary_skill_id": hd.get("primary_skill_id", "SKL-PY"),
                    "start_date": hd.get("start_date", new_prj["start_date"]),
                    "end_date": hd.get("end_date", new_prj["end_date"]),
                    "required_headcount": int(hd.get("required_headcount", 1)),
                    "required_hours": float(hd.get("required_hours", 40.0)),
                    "fulfilled_hours": 0.0,
                    "min_proficiency": int(hd.get("min_proficiency", 3)),
                    "status": "DRAFT",
                    "priority": new_prj["priority"],
                })

        # C. Project Priority Changes
        priority_overrides: Dict[str, int] = parameters.get("priority_overrides", {})
        if priority_overrides:
            for p in projects:
                if p["id"] in priority_overrides:
                    p["priority"] = int(priority_overrides[p["id"]])
                elif p.get("code") in priority_overrides:
                    p["priority"] = int(priority_overrides[p["code"]])

        # D. Project Timeline Shifts (Days)
        timeline_shifts: Dict[str, int] = parameters.get("timeline_shifts", {})
        if timeline_shifts:
            for p in projects:
                shift_days = timeline_shifts.get(p["id"]) or timeline_shifts.get(p.get("code"))
                if shift_days:
                    delta = timedelta(days=int(shift_days))
                    if isinstance(p["start_date"], str):
                        p["start_date"] = date.fromisoformat(p["start_date"]) + delta
                    elif hasattr(p["start_date"], "__add__"):
                        p["start_date"] += delta

                    if isinstance(p["end_date"], str):
                        p["end_date"] = date.fromisoformat(p["end_date"]) + delta
                    elif hasattr(p["end_date"], "__add__"):
                        p["end_date"] += delta

        # E. Simulated Additional Leaves
        simulated_leaves = parameters.get("simulated_leaves", [])
        for sl in simulated_leaves:
            availabilities.append({
                "id": str(uuid.uuid4()),
                "employee_id": sl.get("employee_id"),
                "start_date": sl.get("start_date", today),
                "end_date": sl.get("end_date", today + timedelta(days=14)),
                "availability_type": sl.get("availability_type", "PTO"),
                "capacity_percentage": float(sl.get("capacity_percentage", 0.0)),
                "available_hours_per_day": 0.0,
                "is_approved": True,
            })

        # F. Workforce Reductions / Attrition Simulation
        attrition_pct = float(parameters.get("attrition_rate", 0.0))
        terminated_ids = set(parameters.get("terminated_employee_ids", []))
        if attrition_pct > 0:
            active_count = sum(1 for e in employees if e["employment_status"] == "ACTIVE")
            target_cut = int(round(active_count * (attrition_pct / 100.0)))
            cut_so_far = 0
            for e in employees:
                if cut_so_far >= target_cut:
                    break
                if e["employment_status"] == "ACTIVE" and e["id"] not in terminated_ids:
                    terminated_ids.add(e["id"])
                    cut_so_far += 1

        if terminated_ids:
            for e in employees:
                if e["id"] in terminated_ids:
                    e["employment_status"] = "TERMINATED"

        # G. Training & Hiring Budget Parameters
        training_budget = float(parameters.get("training_budget", 50000.0))
        hiring_budget = float(parameters.get("hiring_budget", 200000.0))
        hiring_lead_time_days = int(parameters.get("hiring_lead_time_days", 45))

        # -------------------------------------------------------------
        # STEP 4: Execute Mathematical Optimization & Baseline Comparison
        # -------------------------------------------------------------
        # Filter active demand for optimization
        active_demands = [d for d in demands if d.get("status") not in ("CANCELLED", "FULFILLED")]
        if not active_demands:
            # Fallback sample demand if none exists
            active_demands = [{
                "id": "DEM-SIM-1",
                "project_id": "PRJ-SIM",
                "primary_skill_id": "SKL-PY",
                "required_hours": 40.0,
                "min_proficiency": 3,
                "priority": 1,
            }]

        # 1. OR-Tools CP-SAT Solver
        opt_result = OrToolsWorkforceSolver.solve(
            demand_items=active_demands,
            employees=employees,
            employee_skills=employee_skills,
            availabilities=availabilities,
            existing_allocations=allocations,
            as_of_date=today,
            max_time_seconds=5.0,
        )

        # 2. Greedy Baseline Solver for comparative benchmarking
        baseline_result = GreedyBaselineSolver.solve(
            demand_items=active_demands,
            employees=employees,
            employee_skills=employee_skills,
            availabilities=availabilities,
            existing_allocations=allocations,
            as_of_date=today,
        )

        # -------------------------------------------------------------
        # STEP 5: Generate Scenario Decision Recommendations
        # -------------------------------------------------------------
        # Map unfilled demands to gaps
        simulated_gaps = []
        for d in active_demands:
            req_hrs = float(d.get("required_hours", 40.0))
            simulated_gaps.append({
                "id": f"GAP-{d.get('id', '1')}",
                "demand_plan_id": d.get("id", "1"),
                "business_id": f"GAP-{d.get('business_id', '1')}",
                "project_id": d.get("project_id"),
                "required_skill_id": d.get("primary_skill_id"),
                "skill_id": d.get("primary_skill_id"),
                "required_skill_name": "Technical Competency",
                "skill_name": "Technical Competency",
                "required_proficiency": d.get("min_proficiency", 3),
                "unfilled_hours": req_hrs,
                "unfilled_demand_hours": req_hrs,
                "severity": "CRITICAL" if d.get("priority", 2) == 1 else "HIGH",
                "project_priority": d.get("priority", 2),
                "start_date": d.get("start_date", today),
                "end_date": d.get("end_date", today + timedelta(days=60)),
            })

        scenario_recommendations = RecommendationEngine.generate_recommendations(
            gaps=simulated_gaps[:10],
            employees=employees,
            employee_skills=employee_skills,
            allocations=allocations,
            training_budget=training_budget,
            hiring_budget=hiring_budget,
            hiring_lead_time_days=hiring_lead_time_days,
            as_of_date=today,
        )

        # -------------------------------------------------------------
        # STEP 6: Synthesize Complete Scenario Output Matrix
        # -------------------------------------------------------------
        total_forecast_demand = sum(float(d.get("required_hours", 40.0)) for d in active_demands)
        active_staff = [e for e in employees if e.get("employment_status") == "ACTIVE"]
        available_supply = sum(float(e.get("standard_hours_per_week", 40.0)) for e in active_staff)

        hiring_reqs = sum(1 for r in scenario_recommendations if (r.action.value if hasattr(r.action, "value") else str(r.action)) == "HIRE")
        training_reqs = sum(1 for r in scenario_recommendations if (r.action.value if hasattr(r.action, "value") else str(r.action)) == "TRAIN")

        duration_ms = int((time.perf_counter() - start_clock) * 1000)

        simulation_results = {
            "baseline_version": baseline_version,
            "baseline_records_snapshot": baseline_records_count,
            "input_assumptions": parameters,
            "metrics": {
                "forecast_demand_hours": round(total_forecast_demand, 1),
                "available_supply_hours": round(available_supply, 1),
                "unfilled_demand_hours": round(opt_result.total_unfilled_hours, 1),
                "total_cost": round(opt_result.total_cost, 2),
                "cost_impact": round(opt_result.total_cost - baseline_result.total_cost, 2),
                "demand_fulfillment_percentage": opt_result.demand_fulfillment_percentage,
                "skill_gaps_count": len(simulated_gaps),
                "capacity_gaps_count": max(0, int(round((total_forecast_demand - available_supply) / 40.0))),
                "utilization_risks_count": len(opt_result.infeasibility_diagnosis.violated_constraints) if opt_result.infeasibility_diagnosis else 0,
                "hiring_requirements_count": hiring_reqs,
                "training_requirements_count": training_reqs,
            },
            "baseline_comparison": {
                "greedy_baseline": {
                    "solver_name": baseline_result.solver_name,
                    "status": baseline_result.status.value,
                    "demand_fulfillment_percentage": baseline_result.demand_fulfillment_percentage,
                    "total_cost": baseline_result.total_cost,
                    "total_unfilled_hours": baseline_result.total_unfilled_hours,
                    "skill_mismatch_score": baseline_result.skill_mismatch_score,
                },
                "ortools_optimized": {
                    "solver_name": opt_result.solver_name,
                    "status": opt_result.status.value,
                    "demand_fulfillment_percentage": opt_result.demand_fulfillment_percentage,
                    "total_cost": opt_result.total_cost,
                    "total_unfilled_hours": opt_result.total_unfilled_hours,
                    "skill_mismatch_score": opt_result.skill_mismatch_score,
                },
                "improvement": {
                    "fulfillment_gain_percentage": round(opt_result.demand_fulfillment_percentage - baseline_result.demand_fulfillment_percentage, 2),
                    "cost_delta": round(opt_result.total_cost - baseline_result.total_cost, 2),
                    "unfilled_hours_reduced": round(baseline_result.total_unfilled_hours - opt_result.total_unfilled_hours, 1),
                },
            },
            "recommendations": [r.to_dict() for r in scenario_recommendations],
            "infeasibility_diagnosis": opt_result.infeasibility_diagnosis.to_dict() if opt_result.infeasibility_diagnosis else None,
            "execution_duration_ms": duration_ms,
        }

        # -------------------------------------------------------------
        # STEP 7: Persist Scenario Run & Audit Event (Guaranteed Zero Baseline Mutation)
        # -------------------------------------------------------------
        cnt_res = await session.execute(select(func.count(ScenarioRun.id)))
        cnt = cnt_res.scalar() or 0
        biz_id = f"SCN-{now_dt.year}-{cnt + 1:06d}"

        new_scenario = ScenarioRun(
            id=str(uuid.uuid4()),
            business_id=biz_id,
            name=name,
            description=description,
            status=ScenarioStatus.COMPLETED,
            parameters=parameters,
            simulation_results=simulation_results,
            executed_by_id=executed_by_id,
            execution_duration_ms=duration_ms,
        )
        session.add(new_scenario)

        # Audit Event logging scenario simulation
        audit_ev = AuditEvent(
            id=str(uuid.uuid4()),
            business_id=f"AUD-{now_dt.year}-{cnt + 1:06d}",
            entity_type="ScenarioRun",
            entity_id=new_scenario.id,
            action=AuditAction.SIMULATE,
            performed_by_id=executed_by_id,
            new_values={
                "scenario_id": new_scenario.id,
                "business_id": biz_id,
                "name": name,
                "baseline_version": baseline_version,
                "demand_fulfillment_percentage": opt_result.demand_fulfillment_percentage,
                "unfilled_demand_hours": opt_result.total_unfilled_hours,
            },
        )
        session.add(audit_ev)

        await session.commit()
        await session.refresh(new_scenario)

        return new_scenario
