"""
Workforce Recommendation Request and Response Pydantic Schemas.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import RecommendationStatus, RecommendationType


class RecommendationItemResponse(BaseModel):
    action: str
    gap_id: str
    project_id: str
    required_skill: str
    required_hours: float
    affected_employees: List[str]
    expected_cost: float
    estimated_time_to_resolve_days: int
    expected_shortage_reduction_hours: float
    deadline_feasibility: bool
    confidence_score: float
    explanation: str
    assumptions: List[str]
    rule_version: str


class RecommendationPlanResponse(BaseModel):
    total_expected_cost: float
    total_shortage_reduction_hours: float
    gaps_analyzed_count: int
    gaps_mitigated_count: int
    unmitigated_gap_ids: List[str]
    recommendations: List[RecommendationItemResponse]
    rule_version: str


class RecommendationRecordResponse(BaseModel):
    id: str
    business_id: str
    gap_analysis_id: Optional[str] = None
    target_employee_id: Optional[str] = None
    target_project_id: Optional[str] = None
    type: RecommendationType
    confidence_score: float
    impact_summary: str
    status: RecommendationStatus
    estimated_cost: float
    time_to_impact_days: Optional[int] = None
    reviewed_by_id: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RecommendationDecisionRequest(BaseModel):
    reason: Optional[str] = Field(default=None, description="Manager decision rationale")
