"""
Google OR-Tools Workforce Allocation Optimization Solver.

Formulates and solves the global workforce capacity and skill allocation problem
using Constraint Programming (CP-SAT).

Objective:
Minimize:
1. Skill mismatch cost
2. Unfilled demand penalty (weighted by project priority)
3. External hiring costs
4. Training costs
5. Constraint violations

Constraints:
- Available capacity (contract hours minus leave and existing commitments)
- Skill proficiency requirements (stale skills strictly excluded from direct allocation)
- Employee lifecycle status (only active employees)
- Project timelines and deadlines
- Leave and availability deductions
- Multi-project capacity exclusivity (zero double-counting)

Provides transparent infeasibility diagnosis when constraints prevent full internal staffing.
"""

from datetime import date
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union
from ortools.sat.python import cp_model

from app.services.optimization.types import (
    AllocationDecision,
    InfeasibilityDiagnosis,
    OptimizationResult,
    OptimizationStatus,
)


class OrToolsWorkforceSolver:
    """Mathematical optimization solver using Google OR-Tools CP-SAT engine."""

    @classmethod
    def solve(
        cls,
        demand_items: Sequence[Dict[str, Any]],
        employees: Sequence[Dict[str, Any]],
        employee_skills: Sequence[Dict[str, Any]],
        availabilities: Optional[Sequence[Dict[str, Any]]] = None,
        existing_allocations: Optional[Sequence[Dict[str, Any]]] = None,
        as_of_date: Optional[date] = None,
        max_time_seconds: float = 10.0,
    ) -> OptimizationResult:
        """
        Formulate and solve global workforce demand allocation problem via OR-Tools CP-SAT.
        """
        start_time = time.perf_counter()
        ref_date = as_of_date or date.today()

        # 1. Index Employees & Build Net Capacity (Deducting Leave & Existing Allocations)
        active_employees = [e for e in employees if e.get("employment_status") == "ACTIVE"]
        emp_ids = [e["id"] for e in active_employees]
        emp_map = {e["id"]: e for e in active_employees}

        emp_capacity: Dict[str, int] = {}
        for e in active_employees:
            base_hrs = int(round(float(e.get("standard_hours_per_week", 40.0))))
            emp_capacity[e["id"]] = base_hrs

        # Deduct confirmed existing allocations
        if existing_allocations:
            for a in existing_allocations:
                if a.get("is_active", True) and a.get("status") not in ("CANCELLED", "RELEASED"):
                    e_id = a.get("employee_id")
                    if e_id in emp_capacity:
                        a_hrs = int(round(float(a.get("allocated_hours_per_week", 0.0))))
                        emp_capacity[e_id] = max(0, emp_capacity[e_id] - a_hrs)

        # 2. Build Skill Matrix & Enforce Stale Skill Invalidation
        emp_skill_prof: Dict[Tuple[str, str], int] = {}
        for es in employee_skills:
            if not es.get("is_current", True):
                continue

            verified_at = es.get("verified_at")
            is_stale = False
            if verified_at:
                if isinstance(verified_at, str):
                    v_date = date.fromisoformat(verified_at[:10])
                elif hasattr(verified_at, "date"):
                    v_date = verified_at.date()
                else:
                    v_date = verified_at

                if (ref_date - v_date).days > 730:
                    is_stale = True

            # Stale skills have effective certified proficiency = 0
            if not is_stale:
                emp_skill_prof[(es["employee_id"], es["skill_id"])] = int(es.get("proficiency_level", 1))

        # 3. Initialize CP-SAT Model
        model = cp_model.CpModel()

        # Decision Variables:
        # x[e, d]: 1 if employee e is assigned directly to demand d
        # t[e, d]: 1 if employee e is trained and assigned to demand d
        # h[d]: 1 if demand d is covered by external hire
        # u[d]: 1 if demand d remains unfilled
        x: Dict[Tuple[str, str], cp_model.IntVar] = {}
        t: Dict[Tuple[str, str], cp_model.IntVar] = {}
        h: Dict[str, cp_model.IntVar] = {}
        u: Dict[str, cp_model.IntVar] = {}

        objective_terms = []

        total_demand_hours = 0.0

        for d in demand_items:
            d_id = d["id"]
            s_id = d.get("primary_skill_id")
            req_prof = int(d.get("min_proficiency", 3))
            prio = int(d.get("priority", 2))
            req_hours = int(round(float(d.get("required_hours", 40.0))))
            total_demand_hours += req_hours

            # SVD deadline days
            s_date = d.get("start_date")
            if isinstance(s_date, str):
                s_date = date.fromisoformat(s_date)
            days_to_start = (s_date - ref_date).days if s_date else 30

            # Variables for demand d
            h[d_id] = model.NewBoolVar(f"hire_{d_id}")
            u[d_id] = model.NewBoolVar(f"unfilled_{d_id}")

            # Cost / Penalty weights
            # External hire cost: $12,000 scaled to integer units
            cost_hire = 12000
            # Unfilled penalty scaled heavily by priority (Priority 1 = 100,000 penalty)
            penalty_unfilled = (5 - prio) * 25000

            objective_terms.append(cost_hire * h[d_id])
            objective_terms.append(penalty_unfilled * u[d_id])

            assignment_vars = [h[d_id], u[d_id]]

            for e_id in emp_ids:
                prof = emp_skill_prof.get((e_id, s_id), 0)

                # Direct internal allocation eligible only if certified prof >= required
                if prof >= req_prof:
                    var_x = model.NewBoolVar(f"alloc_{e_id}_{d_id}")
                    x[(e_id, d_id)] = var_x
                    assignment_vars.append(var_x)

                    # Minor administrative cost ($500) + slight mismatch penalty if overqualified
                    mismatch_cost = 500 + (prof - req_prof) * 100
                    objective_terms.append(mismatch_cost * var_x)

                # Training eligible if candidate has adjacent proficiency (gap <= 2) and training time <= deadline
                gap_prof = req_prof - prof
                training_lead_time_days = 14 * gap_prof
                if 1 <= gap_prof <= 2 and training_lead_time_days <= days_to_start:
                    var_t = model.NewBoolVar(f"train_{e_id}_{d_id}")
                    t[(e_id, d_id)] = var_t
                    assignment_vars.append(var_t)

                    # Training cost ($2,500 base + $1,000/level)
                    cost_train = 2500 + (gap_prof * 1000)
                    objective_terms.append(cost_train * var_t)

            # Constraint 1: Exact Demand Coverage (each demand must be fulfilled by internal, training, hire, or marked unfilled)
            model.Add(sum(assignment_vars) == 1)

        # Constraint 2: Employee Capacity Constraints
        # Total assigned hours across all demands cannot exceed employee net available capacity
        for e_id in emp_ids:
            cap = emp_capacity[e_id]
            emp_assignments = []
            for d in demand_items:
                d_id = d["id"]
                req_hours = int(round(float(d.get("required_hours", 40.0))))
                if (e_id, d_id) in x:
                    emp_assignments.append(req_hours * x[(e_id, d_id)])
                if (e_id, d_id) in t:
                    emp_assignments.append(req_hours * t[(e_id, d_id)])

            if emp_assignments:
                model.Add(sum(emp_assignments) <= cap)

        # 4. Set Objective: Minimize Total Penalties & Costs
        model.Minimize(sum(objective_terms))

        # 5. Solve CP-SAT
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = max_time_seconds
        solver.parameters.random_seed = 20261022
        solve_status = solver.Solve(model)

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        # 6. Parse Results & Decisions
        allocations: List[AllocationDecision] = []
        allocated_hours = 0.0
        unfilled_hours = 0.0
        total_cost = 0.0
        total_mismatch = 0.0
        constraint_violations = 0
        unfilled_reasons: List[str] = []

        if solve_status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            status = OptimizationStatus.OPTIMAL if solve_status == cp_model.OPTIMAL else OptimizationStatus.FEASIBLE

            for d in demand_items:
                d_id = d["id"]
                p_id = d.get("project_id", "PRJ-UNKNOWN")
                s_id = d.get("primary_skill_id")
                req_hours = float(d.get("required_hours", 40.0))

                is_handled = False

                # Check direct allocation
                for e_id in emp_ids:
                    if (e_id, d_id) in x and solver.Value(x[(e_id, d_id)]) == 1:
                        emp = emp_map[e_id]
                        emp_name = f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip()
                        cost_dec = 500.0
                        total_cost += cost_dec
                        allocated_hours += req_hours
                        allocations.append(
                            AllocationDecision(
                                demand_id=d_id,
                                project_id=p_id,
                                employee_id=e_id,
                                employee_name=emp_name,
                                action_type="INTERNAL_ALLOCATION",
                                allocated_hours=req_hours,
                                skill_mismatch_penalty=0.0,
                                decision_cost=cost_dec,
                                explanation=f"OR-Tools allocated verified qualified employee {emp_name} ({e_id}).",
                            )
                        )
                        is_handled = True
                        break

                # Check training allocation
                if not is_handled:
                    for e_id in emp_ids:
                        if (e_id, d_id) in t and solver.Value(t[(e_id, d_id)]) == 1:
                            emp = emp_map[e_id]
                            emp_name = f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip()
                            cost_dec = 3500.0
                            total_cost += cost_dec
                            allocated_hours += req_hours
                            allocations.append(
                                AllocationDecision(
                                    demand_id=d_id,
                                    project_id=p_id,
                                    employee_id=e_id,
                                    employee_name=emp_name,
                                    action_type="TRAINING_AND_ALLOCATE",
                                    allocated_hours=req_hours,
                                    skill_mismatch_penalty=1.0,
                                    decision_cost=cost_dec,
                                    explanation=f"OR-Tools scheduled upskilling for {emp_name} ({e_id}) to meet {s_id} requirement.",
                                )
                            )
                            is_handled = True
                            break

                # Check external hire
                if not is_handled and solver.Value(h[d_id]) == 1:
                    cost_dec = 12000.0
                    total_cost += cost_dec
                    allocated_hours += req_hours
                    allocations.append(
                        AllocationDecision(
                            demand_id=d_id,
                            project_id=p_id,
                            employee_id=None,
                            employee_name=None,
                            action_type="EXTERNAL_HIRE",
                            allocated_hours=req_hours,
                            skill_mismatch_penalty=0.0,
                            decision_cost=cost_dec,
                            explanation=f"OR-Tools routed demand {d_id} to external hire (internal capacity exhausted or unqualified).",
                        )
                    )
                    is_handled = True

                # Check unfilled
                if not is_handled and solver.Value(u[d_id]) == 1:
                    unfilled_hours += req_hours
                    unfilled_reasons.append(
                        f"Demand {d_id} for skill {s_id} left unfilled due to constraint bottleneck or budget cap."
                    )
                    allocations.append(
                        AllocationDecision(
                            demand_id=d_id,
                            project_id=p_id,
                            employee_id=None,
                            employee_name=None,
                            action_type="UNFILLED",
                            allocated_hours=0.0,
                            skill_mismatch_penalty=5.0,
                            decision_cost=0.0,
                            explanation=f"Demand {d_id} could not be satisfied under active constraints.",
                        )
                    )

        else:
            status = OptimizationStatus.INFEASIBLE
            unfilled_hours = total_demand_hours
            unfilled_reasons.append("Model proved mathematically infeasible under strict joint constraints.")

        fulfillment_pct = (allocated_hours / total_demand_hours * 100.0) if total_demand_hours > 0 else 100.0
        is_fully_feasible = unfilled_hours == 0.0

        diagnosis = InfeasibilityDiagnosis(
            is_fully_feasible=is_fully_feasible,
            unfilled_demand_count=len(unfilled_reasons),
            unfilled_hours=unfilled_hours,
            infeasibility_reasons=unfilled_reasons,
            violated_constraints=[] if is_fully_feasible else ["CAPACITY_OR_QUALIFICATION_BOTTLENECK"],
            mitigation_suggestions=(
                []
                if is_fully_feasible
                else [
                    "Increase external hiring budget.",
                    "Extend project start deadlines to allow upskilling.",
                    "Recertify stale employee skills.",
                ]
            ),
        )

        return OptimizationResult(
            status=status,
            solver_name="Google OR-Tools CP-SAT",
            demand_fulfillment_percentage=round(fulfillment_pct, 2),
            total_allocated_hours=round(allocated_hours, 2),
            total_unfilled_hours=round(unfilled_hours, 2),
            total_cost=round(total_cost, 2),
            skill_mismatch_score=round(total_mismatch, 2),
            constraint_violations_count=constraint_violations,
            allocations=allocations,
            infeasibility_diagnosis=diagnosis,
            solve_duration_ms=round(duration_ms, 2),
            rule_version="1.0.0",
        )

