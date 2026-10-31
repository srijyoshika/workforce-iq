"""
Data Quality and Reproducibility Request and Response Pydantic Schemas.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ValidationReportResponse(BaseModel):
    is_valid: bool
    integrity_failures_count: int
    detected_anomalies_count: int
    anomalies_by_type: Dict[str, int]
    summary_metrics: Dict[str, Any]


class EvaluationMetricsResponse(BaseModel):
    precision: float
    recall: float
    f1_score: float
    true_positives: int
    false_positives: int
    false_negatives: int
    confusion_matrix: Dict[str, int]
    evaluated_at: str


class ReproducibilityResponse(BaseModel):
    is_reproducible: bool
    total_files_checked: int
    matched_checksums_count: int
    mismatched_files: List[str]
    rule_version: str
