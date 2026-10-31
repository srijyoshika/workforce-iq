"""
DemandPlan Request and Response Pydantic Schemas.
"""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import DemandStatus


class DemandPlanBase(BaseModel):
    project_id: str
    role_id: str
    primary_skill_id: Optional[str] = None
    start_date: date
    end_date: date
    required_headcount: int = Field(default=1, ge=1)
    required_hours: Optional[float] = Field(default=None, ge=0.0)
    fulfilled_hours: float = Field(default=0.0, ge=0.0)
    min_proficiency: int = Field(default=3, ge=1, le=5)
    status: DemandStatus = DemandStatus.DRAFT
    priority: int = Field(default=2, ge=1, le=4)
    notes: Optional[str] = None


class DemandPlanCreate(DemandPlanBase):
    pass


class DemandPlanUpdate(BaseModel):
    role_id: Optional[str] = None
    primary_skill_id: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    required_headcount: Optional[int] = None
    required_hours: Optional[float] = None
    fulfilled_hours: Optional[float] = None
    min_proficiency: Optional[int] = None
    status: Optional[DemandStatus] = None
    priority: Optional[int] = None
    notes: Optional[str] = None


class DemandPlanResponse(DemandPlanBase):
    id: str
    business_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
