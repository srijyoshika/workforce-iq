"""
Scenario Simulation Request and Response Pydantic Schemas.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import ScenarioStatus


class ScenarioRunBase(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    status: ScenarioStatus = ScenarioStatus.DRAFT


class ScenarioRunCreate(ScenarioRunBase):
    pass


class ScenarioRunResponse(ScenarioRunBase):
    id: str
    business_id: str
    simulation_results: Optional[Dict[str, Any]] = None
    executed_by_id: Optional[str] = None
    execution_duration_ms: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
