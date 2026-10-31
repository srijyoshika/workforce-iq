"""
Project Request and Response Pydantic Schemas.
"""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import ProjectStatus


class ProjectBase(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    code: str = Field(min_length=1, max_length=50)
    department: Optional[str] = "Engineering"
    client_name: Optional[str] = None
    manager_id: Optional[str] = None
    start_date: date
    end_date: date
    status: ProjectStatus = ProjectStatus.PIPELINE
    budget: Optional[float] = Field(default=None, ge=0.0)
    priority: int = Field(default=2, ge=1, le=4)
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    manager_id: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[ProjectStatus] = None
    budget: Optional[float] = None
    priority: Optional[int] = None
    description: Optional[str] = None


class ProjectResponse(ProjectBase):
    id: str
    business_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
