"""
Workforce Risk and IssueRecord Request and Response Pydantic Schemas.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import IssueSeverity, IssueStatus, IssueType


class IssueRecordBase(BaseModel):
    project_id: Optional[str] = None
    employee_id: Optional[str] = None
    issue_type: IssueType
    severity: IssueSeverity = IssueSeverity.MEDIUM
    status: IssueStatus = IssueStatus.OPEN
    title: str = Field(min_length=1, max_length=200)
    description: str


class IssueRecordCreate(IssueRecordBase):
    pass


class IssueRecordUpdate(BaseModel):
    severity: Optional[IssueSeverity] = None
    status: Optional[IssueStatus] = None
    title: Optional[str] = None
    description: Optional[str] = None
    resolved_at: Optional[datetime] = None


class IssueRecordResponse(IssueRecordBase):
    id: str
    business_id: str
    detected_at: datetime
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RiskScanResponse(BaseModel):
    total_risks_detected: int
    overallocations_count: int
    stale_skills_count: int
    duplicate_demands_count: int
    overlapping_allocations_count: int
    staffing_shortages_count: int
    new_issues_persisted: int
    scanned_at: str
