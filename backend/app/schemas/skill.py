"""
Skill, EmployeeSkill, and RoleSkill Request and Response Pydantic Schemas.
"""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import SkillCategory, VerificationStatus


class SkillBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    category: SkillCategory
    is_active: bool = True
    description: Optional[str] = None


class SkillCreate(SkillBase):
    pass


class SkillUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[SkillCategory] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None


class SkillResponse(SkillBase):
    id: str
    business_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EmployeeSkillBase(BaseModel):
    employee_id: str
    skill_id: str
    proficiency_level: int = Field(ge=1, le=5)
    verification_status: VerificationStatus = VerificationStatus.SELF_REPORTED
    verified_at: Optional[date] = None
    is_current: bool = True
    notes: Optional[str] = None


class EmployeeSkillCreate(EmployeeSkillBase):
    pass


class EmployeeSkillUpdate(BaseModel):
    proficiency_level: Optional[int] = Field(default=None, ge=1, le=5)
    verification_status: Optional[VerificationStatus] = None
    verified_at: Optional[date] = None
    is_current: Optional[bool] = None
    notes: Optional[str] = None


class EmployeeSkillResponse(EmployeeSkillBase):
    id: str
    business_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
