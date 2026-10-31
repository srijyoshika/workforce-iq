"""
WorkforceIQ Workforce Optimization Package.
Formulates and solves global workforce scheduling using Google OR-Tools CP-SAT and comparative baseline benchmarking.
"""

from app.services.optimization.baseline_solver import GreedyBaselineSolver
from app.services.optimization.optimizer_service import WorkforceOptimizerService
from app.services.optimization.solver import OrToolsWorkforceSolver
from app.services.optimization.types import (
    AllocationDecision,
    BenchmarkComparison,
    InfeasibilityDiagnosis,
    OptimizationResult,
    OptimizationStatus,
)

__all__ = [
    "OptimizationStatus",
    "AllocationDecision",
    "InfeasibilityDiagnosis",
    "BenchmarkComparison",
    "OptimizationResult",
    "OrToolsWorkforceSolver",
    "GreedyBaselineSolver",
    "WorkforceOptimizerService",
]

