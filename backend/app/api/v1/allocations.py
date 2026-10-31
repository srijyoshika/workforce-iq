"""
Workforce Project Allocation API Endpoints.
"""

from datetime import datetime, timezone
from typing import Annotated, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import PaginationParams, get_current_user, get_db, require_roles
from app.models.allocation import Allocation
from app.models.audit import AuditEvent
from app.models.employee import Employee
from app.models.enums import AllocationStatus, AuditAction, UserRole
from app.schemas.allocation import AllocationCreate, AllocationResponse, AllocationUpdate
from app.schemas.common import PaginatedResponse, SuccessResponse

router = APIRouter(prefix="/allocations", tags=["Allocations"])


@router.get("", response_model=PaginatedResponse[AllocationResponse], summary="List Project Allocations")
async def list_allocations(
    pagination: Annotated[PaginationParams, Depends()],
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(get_current_user)],
    employee_id: Optional[str] = Query(default=None, description="Filter by employee"),
    project_id: Optional[str] = Query(default=None, description="Filter by project"),
    is_active: Optional[bool] = Query(default=None, description="Filter by active status"),
):
    query = select(Allocation)
    count_query = select(func.count(Allocation.id))

    if employee_id:
        query = query.where(Allocation.employee_id == employee_id)
        count_query = count_query.where(Allocation.employee_id == employee_id)
    if project_id:
        query = query.where(Allocation.project_id == project_id)
        count_query = count_query.where(Allocation.project_id == project_id)
    if is_active is not None:
        query = query.where(Allocation.is_active == is_active)
        count_query = count_query.where(Allocation.is_active == is_active)

    total_res = await session.execute(count_query)
    total = total_res.scalar() or 0

    query = query.order_by(Allocation.start_date.desc()).offset(pagination.offset).limit(pagination.limit)
    res = await session.execute(query)
    allocations = res.scalars().all()

    total_pages = max(1, (total + pagination.page_size - 1) // pagination.page_size)

    return PaginatedResponse[AllocationResponse](
        items=[AllocationResponse.model_validate(a) for a in allocations],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
    )


@router.get("/{allocation_id}", response_model=AllocationResponse, summary="Get Allocation by ID")
async def get_allocation(
    allocation_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(get_current_user)],
):
    stmt = select(Allocation).where(Allocation.id == allocation_id)
    res = await session.execute(stmt)
    alloc = res.scalar_one_or_none()
    if not alloc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Allocation '{allocation_id}' not found")
    return AllocationResponse.model_validate(alloc)


@router.post("", response_model=AllocationResponse, status_code=status.HTTP_201_CREATED, summary="Create Project Allocation")
async def create_allocation(
    payload: AllocationCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(require_roles(UserRole.ADMIN, UserRole.PROJECT_MANAGER, UserRole.OPERATIONS_PARTNER))],
):
    count_stmt = select(func.count(Allocation.id))
    cnt_res = await session.execute(count_stmt)
    cnt = cnt_res.scalar() or 0
    biz_id = f"ALLOC-{payload.start_date.year}-{cnt + 1:06d}"

    new_alloc = Allocation(
        id=str(uuid.uuid4()),
        business_id=biz_id,
        employee_id=payload.employee_id,
        project_id=payload.project_id,
        demand_plan_id=payload.demand_plan_id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        allocation_percentage=payload.allocation_percentage,
        allocated_hours_per_week=payload.allocated_hours_per_week,
        status=payload.status,
        is_active=payload.is_active,
        version=payload.version,
        notes=payload.notes,
    )
    session.add(new_alloc)

    # Record Audit Event
    now_dt = datetime.now(timezone.utc)
    audit_ev = AuditEvent(
        id=str(uuid.uuid4()),
        business_id=f"AUD-{now_dt.year}-{uuid.uuid4().hex[:6]}",
        entity_type="Allocation",
        entity_id=new_alloc.id,
        action=AuditAction.ALLOCATE,
        performed_by_id=current_user.id,
        new_values={
            "allocation_id": new_alloc.id,
            "business_id": biz_id,
            "employee_id": payload.employee_id,
            "project_id": payload.project_id,
            "hours_per_week": payload.allocated_hours_per_week,
            "version": payload.version,
        },
    )
    session.add(audit_ev)

    await session.commit()
    await session.refresh(new_alloc)
    return AllocationResponse.model_validate(new_alloc)


@router.put("/{allocation_id}", response_model=AllocationResponse, summary="Update Project Allocation")
async def update_allocation(
    allocation_id: str,
    payload: AllocationUpdate,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(require_roles(UserRole.ADMIN, UserRole.PROJECT_MANAGER, UserRole.OPERATIONS_PARTNER))],
):
    stmt = select(Allocation).where(Allocation.id == allocation_id)
    res = await session.execute(stmt)
    alloc = res.scalar_one_or_none()
    if not alloc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Allocation '{allocation_id}' not found")

    # Capture previous state for audit and increment version
    previous_state = {
        "version": alloc.version,
        "allocation_percentage": float(alloc.allocation_percentage),
        "allocated_hours_per_week": float(alloc.allocated_hours_per_week),
        "status": alloc.status.value if hasattr(alloc.status, "value") else str(alloc.status),
        "start_date": alloc.start_date.isoformat() if hasattr(alloc.start_date, "isoformat") else str(alloc.start_date),
        "end_date": alloc.end_date.isoformat() if hasattr(alloc.end_date, "isoformat") else str(alloc.end_date),
    }

    alloc.version += 1

    for f, v in payload.model_dump(exclude_unset=True).items():
        setattr(alloc, f, v)

    # Record Audit Event
    now_dt = datetime.now(timezone.utc)
    audit_ev = AuditEvent(
        id=str(uuid.uuid4()),
        business_id=f"AUD-{now_dt.year}-{uuid.uuid4().hex[:6]}",
        entity_type="Allocation",
        entity_id=alloc.id,
        action=AuditAction.UPDATE,
        performed_by_id=current_user.id,
        old_values=previous_state,
        new_values={
            "allocation_id": alloc.id,
            "business_id": alloc.business_id,
            "new_version": alloc.version,
            "updated_by": current_user.email,
        },
    )
    session.add(audit_ev)

    await session.commit()
    await session.refresh(alloc)
    return AllocationResponse.model_validate(alloc)


@router.delete("/{allocation_id}", response_model=SuccessResponse, summary="Release or Delete Allocation")
async def delete_allocation(
    allocation_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(require_roles(UserRole.ADMIN, UserRole.PROJECT_MANAGER))],
):
    stmt = select(Allocation).where(Allocation.id == allocation_id)
    res = await session.execute(stmt)
    alloc = res.scalar_one_or_none()
    if not alloc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Allocation '{allocation_id}' not found")

    alloc.is_active = False
    alloc.status = AllocationStatus.RELEASED

    # Record Audit Event
    now_dt = datetime.now(timezone.utc)
    audit_ev = AuditEvent(
        id=str(uuid.uuid4()),
        business_id=f"AUD-{now_dt.year}-{uuid.uuid4().hex[:6]}",
        entity_type="Allocation",
        entity_id=alloc.id,
        action=AuditAction.DELETE,
        performed_by_id=current_user.id,
        new_values={
            "allocation_id": alloc.id,
            "business_id": alloc.business_id,
            "status": AllocationStatus.RELEASED.value,
            "released_by": current_user.email,
        },
    )
    session.add(audit_ev)

    await session.commit()
    return SuccessResponse(message=f"Allocation '{alloc.business_id}' successfully released")
