"""
Greedy Baseline Allocator.

Implements a simple first-fit greedy allocation heuristic without global optimization.
Serves as the benchmark baseline against which the OR-Tools optimizer is evaluated.
"""

from datetime import date
import time
from typing import Any, Dict, List, Optional, Sequence, Union

from app.services.optimization.types import (
    AllocationDecision,
    BenchmarkComparison,
    InfeasibilityDiagnosis,
    OptimizationResult,
    OptimizationStatus,
)


class GreedyBaselineSolver:
    """Simple first-fit baseline allocator for comparative benchmark testing."""

    @classmethod
    def solve(
        cls,
        demand_items: Sequence[Dict[str, Any]],
        employees: Sequence[Dict[str, Any]],
        employee_skills: Sequence[Dict[str, Any]],
        availabilities: Optional[Sequence[Dict[str, Any]]] = None,
        existing_allocations: Optional[Sequence[Dict[str, Any]]] = None,
        as_of_date: Optional[date] = None,
    ) -> OptimizationResult:
        """
        Greedy first-fit allocation:
        Iterates over demands in sequential input order and assigns the first employee who
        holds the matching skill with proficiency >= required and available capacity.
        """
        start_time = time.perf_counter()
        ref_date = as_of_date or date.today()

        # Map current verified skills: (emp_id, skill_id) -> proficiency
        emp_skill_map: Dict[tuple, int] = {}
        for es in employee_skills:
            if not es.get("is_current", True):
                continue
            verified_at = es.get("verified_at")
            if verified_at:
                if isinstance(verified_at, str):
                    v_date = date.fromisoformat(verified_at[:10])
                elif hasattr(verified_at, "date"):
                    v_date = verified_at.date()
                else:
                    v_date = verified_at
                # Stale skill guard: > 730 days is disqualified
                if (ref_date - v_date).days > 730:
                    continue
            emp_skill_map[(es["employee_id"], es["skill_id"])] = int(es.get("proficiency_level", 1))

        # Map initial net capacity per employee (deducting existing allocations and leave)
        emp_map: Dict[str, Dict[str, Any]] = {e["id"]: e for e in employees if e.get("employment_status") == "ACTIVE"}
        capacity_map: Dict[str, float] = {
            e["id"]: float(e.get("standard_hours_per_week", 40.0))
            for e in emp_map.values()
        }

        # Deduct confirmed existing allocations
        if existing_allocations:
            for a in existing_allocations:
                if a.get("is_active", True) and a.get("status") not in ("CANCELLED", "RELEASED"):
                    e_id = a.get("employee_id")
                    if e_id in capacity_map:
                        a_hrs = float(a.get("allocated_hours_per_week", 0.0))
                        capacity_map[e_id] = max(0.0, capacity_map[e_id] - a_hrs)

        total_demand_hours = sum(float(d.get("required_hours", 40.0)) for d in demand_items)
        allocated_hours = 0.0
        unfilled_hours = 0.0
        total_cost = 0.0
        mismatch_score = 0.0
        constraint_violations = 0
        allocations: List[AllocationDecision] = []
        unfilled_reasons: List[str] = []

        # Iterate sequentially (greedy first-fit without global priority weighting)
        for d in demand_items:
            d_id = d["id"]
            p_id = d.get("project_id", "PRJ-UNKNOWN")
            s_id = d.get("primary_skill_id")
            req_prof = int(d.get("min_proficiency", 3))
            req_hours = float(d.get("required_hours", 40.0))

            assigned_emp_id: Optional[str] = None
            assigned_emp_name: Optional[str] = None

            # Look for first available employee with matching skill and capacity
            for emp_id, emp in emp_map.items():
                cur_prof = emp_skill_map.get((emp_id, s_id), 0)
                if cur_prof >= req_prof and capacity_map.get(emp_id, 0.0) >= req_hours:
                    assigned_emp_id = emp_id
                    assigned_emp_name = f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip()
                    capacity_map[emp_id] -= req_hours
                    allocated_hours += req_hours
                    decision_cost = 500.0  # Internal allocation admin cost
                    total_cost += decision_cost
                    allocations.append(
                        AllocationDecision(
                            demand_id=d_id,
                            project_id=p_id,
                            employee_id=assigned_emp_id,
                            employee_name=assigned_emp_name,
                            action_type="INTERNAL_ALLOCATION",
                            allocated_hours=req_hours,
                            skill_mismatch_penalty=0.0,
                            decision_cost=decision_cost,
                            explanation=f"Greedy first-fit allocated {assigned_emp_name} ({emp_id}) with Level {cur_prof} skill.",
                        )
                    )
                    break

            if not assigned_emp_id:
                # Greedy solver leaves unassigned or falls back to hiring
                unfilled_hours += req_hours
                unfilled_cost = 12000.0  # External hiring fallback
                total_cost += unfilled_cost
                unfilled_reasons.append(f"Demand {d_id} ({s_id}) could not find immediate available capacity in greedy pass.")
                allocations.append(
                    AllocationDecision(
                        demand_id=d_id,
                        project_id=p_id,
                        employee_id=None,
                        employee_name=None,
                        action_type="EXTERNAL_HIRE",
                        allocated_hours=req_hours,
                        skill_mismatch_penalty=10.0,
                        decision_cost=unfilled_cost,
                        explanation=f"Greedy solver fell back to external hire due to uncoordinated capacity exhaustion.",
                    )
                )

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        fulfillment_pct = (allocated_hours / total_demand_hours * 100.0) if total_demand_hours > 0 else 100.0

        is_fully_feasible = unfilled_hours == 0.0
        diagnosis = InfeasibilityDiagnosis(
            is_fully_feasible=is_fully_feasible,
            unfilled_demand_count=len(unfilled_reasons),
            unfilled_hours=unfilled_hours,
            infeasibility_reasons=unfilled_reasons,
            violated_constraints=[] if is_fully_feasible else ["CAPACITY_EXHAUSTION_IN_GREEDY_ORDER"],
            mitigation_suggestions=["Re-order demands by priority or use global CP-SAT constraint optimizer."],
        )

        return OptimizationResult(
            status=OptimizationStatus.OPTIMAL if is_fully_feasible else OptimizationStatus.FEASIBLE,
            solver_name="Greedy First-Fit Baseline",
            demand_fulfillment_percentage=fulfillment_pct,
            total_allocated_hours=allocated_hours,
            total_unfilled_hours=unfilled_hours,
            total_cost=total_cost,
            skill_mismatch_score=mismatch_score,
            constraint_violations_count=constraint_violations,
            allocations=allocations,
            infeasibility_diagnosis=diagnosis,
            solve_duration_ms=duration_ms,
            rule_version="1.0.0",
        )

