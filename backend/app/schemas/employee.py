"""
Employee Entity Request and Response Pydantic Schemas.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.models.enums import EmploymentStatus, UserRole


class EmployeeBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    role_id: Optional[str] = None
    department: str = Field(min_length=1, max_length=100)
    location: str = Field(min_length=1, max_length=100)
    employment_status: EmploymentStatus = EmploymentStatus.ACTIVE
    hire_date: date
    exit_date: Optional[date] = None
    standard_hours_per_week: float = Field(default=40.0, ge=1.0, le=80.0)
    cost_rate_per_hour: Optional[float] = Field(default=None, ge=0.0)
    system_role: UserRole = UserRole.EMPLOYEE
    years_of_experience: Optional[float] = Field(default=0.0, ge=0.0, le=60.0)
    experience_level: Optional[str] = Field(default="Mid-Level", max_length=50)
    previous_company: Optional[str] = Field(default=None, max_length=100)
    experience_summary: Optional[str] = Field(default=None)


class EmployeeCreate(EmployeeBase):
    """Payload to register a new employee."""
    password: Optional[str] = Field(default="Workforce2026!", min_length=4)


class EmployeeUpdate(BaseModel):
    """Payload to update an existing employee."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role_id: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    employment_status: Optional[EmploymentStatus] = None
    exit_date: Optional[date] = None
    standard_hours_per_week: Optional[float] = None
    cost_rate_per_hour: Optional[float] = None
    system_role: Optional[UserRole] = None
    years_of_experience: Optional[float] = None
    experience_level: Optional[str] = None
    previous_company: Optional[str] = None
    experience_summary: Optional[str] = None


class EmployeeResponse(EmployeeBase):
    """Standard serialized employee response."""
    id: str
    business_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
