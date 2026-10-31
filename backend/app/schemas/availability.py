"""
Availability and Leave Request and Response Pydantic Schemas.
"""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import AvailabilityType


class AvailabilityBase(BaseModel):
    employee_id: str
    start_date: date
    end_date: date
    availability_type: AvailabilityType = AvailabilityType.PTO
    capacity_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    available_hours_per_day: float = Field(default=0.0, ge=0.0, le=24.0)
    is_approved: bool = True
    approved_by_id: Optional[str] = None
    reason: Optional[str] = None


class AvailabilityCreate(AvailabilityBase):
    pass


class AvailabilityUpdate(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    availability_type: Optional[AvailabilityType] = None
    capacity_percentage: Optional[float] = None
    available_hours_per_day: Optional[float] = None
    is_approved: Optional[bool] = None
    reason: Optional[str] = None


class AvailabilityResponse(AvailabilityBase):
    id: str
    business_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
