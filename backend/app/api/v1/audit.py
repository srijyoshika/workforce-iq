"""
Audit Event History API Endpoints.
Provides immutable audit trail queries with server-side pagination and filtering.
"""

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import PaginationParams, get_current_user, get_db, require_roles
from app.models.audit import AuditEvent
from app.models.employee import Employee
from app.models.enums import AuditAction, UserRole
from app.schemas.audit import AuditEventResponse
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/audit", tags=["Audit History"])


@router.get("", response_model=PaginatedResponse[AuditEventResponse], summary="List Audit Events")
async def list_audit_events(
    pagination: Annotated[PaginationParams, Depends()],
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(require_roles(UserRole.ADMIN, UserRole.OPERATIONS_PARTNER, UserRole.HR_PARTNER))],
    action: Optional[AuditAction] = Query(default=None, description="Filter by mutation action"),
    entity_type: Optional[str] = Query(default=None, description="Filter by entity type"),
):
    query = select(AuditEvent).order_by(desc(AuditEvent.timestamp))
    count_query = select(func.count(AuditEvent.id))

    if action:
        query = query.where(AuditEvent.action == action)
        count_query = count_query.where(AuditEvent.action == action)
    if entity_type:
        query = query.where(AuditEvent.entity_type == entity_type)
        count_query = count_query.where(AuditEvent.entity_type == entity_type)

    total_res = await session.execute(count_query)
    total = total_res.scalar() or 0

    query = query.offset(pagination.offset).limit(pagination.limit)
    res = await session.execute(query)
    events = res.scalars().all()

    total_pages = max(1, (total + pagination.page_size - 1) // pagination.page_size)

    return PaginatedResponse[AuditEventResponse](
        items=[AuditEventResponse.model_validate(e) for e in events],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
    )

