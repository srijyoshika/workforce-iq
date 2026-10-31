"""
Role Entity Request and Response Pydantic Schemas.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class RoleBase(BaseModel):
    title: Optional[str] = None
    name: Optional[str] = None
    code: Optional[str] = None
    department: str = Field(default="Engineering", min_length=1, max_length=100)
    level: Optional[int] = Field(default=1, ge=1, le=10)
    is_active: bool = True
    description: Optional[str] = None
    standard_hourly_rate: Optional[float] = None


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    level: Optional[int] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None


class RoleResponse(RoleBase):
    id: str
    business_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
