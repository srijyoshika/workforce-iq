"""
Audit Domain Request and Response Pydantic Schemas.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict
from app.models.enums import AuditAction


class AuditEventResponse(BaseModel):
    id: str
    business_id: str
    entity_type: str
    entity_id: str
    action: AuditAction
    performed_by_id: Optional[str] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None
    timestamp: datetime
    ip_address: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
