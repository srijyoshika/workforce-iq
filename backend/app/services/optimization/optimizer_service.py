"""
Master Workforce Optimization Service.

Coordinates global mathematical workforce allocation using Google OR-Tools CP-SAT,
executes comparative evaluations against the Greedy Baseline Allocator,
and compiles diagnostic reports.
"""

from datetime import date
from typing import Any, Dict, List, Optional, Sequence, Union

from app.services.optimization.baseline_solver import GreedyBaselineSolver
from app.services.optimization.solver import OrToolsWorkforceSolver
from app.services.optimization.types import (
    BenchmarkComparison,
    OptimizationResult,
    OptimizationStatus,
)


class WorkforceOptimizerService:
    """Master service for optimal workforce capacity scheduling and baseline benchmarking."""

    @classmethod
    def optimize_allocations(
        cls,
        demand_items: Sequence[Dict[str, Any]],
        employees: Sequence[Dict[str, Any]],
        employee_skills: Sequence[Dict[str, Any]],
        availabilities: Optional[Sequence[Dict[str, Any]]] = None,
        existing_allocations: Optional[Sequence[Dict[str, Any]]] = None,
        as_of_date: Optional[date] = None,
        compare_with_baseline: bool = True,
        max_time_seconds: float = 10.0,
    ) -> OptimizationResult:
        """
        Execute OR-Tools CP-SAT optimization and optionally benchmark against Greedy baseline.
        """
        # 1. Solve with OR-Tools CP-SAT
        opt_result = OrToolsWorkforceSolver.solve(
            demand_items=demand_items,
            employees=employees,
            employee_skills=employee_skills,
            availabilities=availabilities,
            existing_allocations=existing_allocations,
            as_of_date=as_of_date,
            max_time_seconds=max_time_seconds,
        )

        # 2. Run Greedy Baseline for comparative reporting
        if compare_with_baseline:
            baseline_result = GreedyBaselineSolver.solve(
                demand_items=demand_items,
                employees=employees,
                employee_skills=employee_skills,
                availabilities=availabilities,
                existing_allocations=existing_allocations,
                as_of_date=as_of_date,
            )

            benchmark = BenchmarkComparison(
                solver_name=baseline_result.solver_name,
                status=baseline_result.status.value,
                demand_fulfillment_percentage=baseline_result.demand_fulfillment_percentage,
                total_cost=baseline_result.total_cost,
                skill_mismatch_score=baseline_result.skill_mismatch_score,
                constraint_violations_count=baseline_result.constraint_violations_count,
                solve_duration_ms=baseline_result.solve_duration_ms,
            )

            # Re-create OptimizationResult with baseline_benchmark attached
            return OptimizationResult(
                status=opt_result.status,
                solver_name=opt_result.solver_name,
                demand_fulfillment_percentage=opt_result.demand_fulfillment_percentage,
                total_allocated_hours=opt_result.total_allocated_hours,
                total_unfilled_hours=opt_result.total_unfilled_hours,
                total_cost=opt_result.total_cost,
                skill_mismatch_score=opt_result.skill_mismatch_score,
                constraint_violations_count=opt_result.constraint_violations_count,
                allocations=opt_result.allocations,
                infeasibility_diagnosis=opt_result.infeasibility_diagnosis,
                baseline_benchmark=benchmark,
                solve_duration_ms=opt_result.solve_duration_ms,
                rule_version=opt_result.rule_version,
            )

        return opt_result

