"""
Training Request and Response Pydantic Schemas.
"""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import TrainingStatus


class TrainingBase(BaseModel):
    employee_id: str
    skill_id: str
    program_name: str = Field(min_length=1, max_length=200)
    provider: Optional[str] = None
    start_date: date
    target_completion_date: date
    actual_completion_date: Optional[date] = None
    target_proficiency: int = Field(ge=1, le=5)
    status: TrainingStatus = TrainingStatus.ENROLLED
    cost: float = Field(default=0.0, ge=0.0)
    hours_per_week: float = Field(default=0.0, ge=0.0)


class TrainingCreate(TrainingBase):
    pass


class TrainingUpdate(BaseModel):
    target_completion_date: Optional[date] = None
    actual_completion_date: Optional[date] = None
    target_proficiency: Optional[int] = None
    status: Optional[TrainingStatus] = None
    cost: Optional[float] = None
    hours_per_week: Optional[float] = None


class TrainingResponse(TrainingBase):
    id: str
    business_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
