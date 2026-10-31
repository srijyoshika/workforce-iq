"""
Allocation Request and Response Pydantic Schemas.
"""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import AllocationStatus


class AllocationBase(BaseModel):
    employee_id: str
    project_id: str
    demand_plan_id: Optional[str] = None
    start_date: date
    end_date: date
    allocation_percentage: float = Field(ge=0.0, le=100.0)
    allocated_hours_per_week: float = Field(ge=0.0, le=80.0)
    status: AllocationStatus = AllocationStatus.PROPOSED
    is_active: bool = True
    version: int = 1
    superseded_by_id: Optional[str] = None
    notes: Optional[str] = None


class AllocationCreate(AllocationBase):
    pass


class AllocationUpdate(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    allocation_percentage: Optional[float] = None
    allocated_hours_per_week: Optional[float] = None
    status: Optional[AllocationStatus] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class AllocationResponse(AllocationBase):
    id: str
    business_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
