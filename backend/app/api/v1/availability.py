"""
Employee Availability and Planned Leave API Endpoints.
"""

from typing import Annotated, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import PaginationParams, get_current_user, get_db
from app.models.employee import Availability, Employee
from app.models.enums import AvailabilityType, UserRole
from app.schemas.availability import AvailabilityCreate, AvailabilityResponse, AvailabilityUpdate
from app.schemas.common import PaginatedResponse, SuccessResponse

router = APIRouter(prefix="/availability", tags=["Availability & Leave"])


@router.get("", response_model=PaginatedResponse[AvailabilityResponse], summary="List Planned Leaves & Availabilities")
async def list_availabilities(
    pagination: Annotated[PaginationParams, Depends()],
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(get_current_user)],
    employee_id: Optional[str] = Query(default=None, description="Filter by employee"),
    availability_type: Optional[AvailabilityType] = Query(default=None, description="Filter by type (PTO, SICK_LEAVE, etc.)"),
):
    query = select(Availability)
    count_query = select(func.count(Availability.id))

    if employee_id:
        query = query.where(Availability.employee_id == employee_id)
        count_query = count_query.where(Availability.employee_id == employee_id)
    if availability_type:
        query = query.where(Availability.availability_type == availability_type)
        count_query = count_query.where(Availability.availability_type == availability_type)

    total_res = await session.execute(count_query)
    total = total_res.scalar() or 0

    query = query.order_by(Availability.start_date.desc()).offset(pagination.offset).limit(pagination.limit)
    res = await session.execute(query)
    records = res.scalars().all()

    total_pages = max(1, (total + pagination.page_size - 1) // pagination.page_size)

    return PaginatedResponse[AvailabilityResponse](
        items=[AvailabilityResponse.model_validate(r) for r in records],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
    )


@router.get("/{availability_id}", response_model=AvailabilityResponse, summary="Get Availability Record by ID")
async def get_availability(
    availability_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(get_current_user)],
):
    stmt = select(Availability).where(Availability.id == availability_id)
    res = await session.execute(stmt)
    rec = res.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Availability record '{availability_id}' not found")
    return AvailabilityResponse.model_validate(rec)


@router.post("", response_model=AvailabilityResponse, status_code=status.HTTP_201_CREATED, summary="Register Availability or Leave")
async def create_availability(
    payload: AvailabilityCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(get_current_user)],
):
    # Non-admin users can only create availability for themselves
    user_role_val = current_user.system_role.value if hasattr(current_user.system_role, "value") else str(current_user.system_role)
    if user_role_val not in (UserRole.ADMIN.value, UserRole.HR_PARTNER.value) and current_user.id != payload.employee_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot register leave on behalf of other employees")

    count_stmt = select(func.count(Availability.id))
    cnt_res = await session.execute(count_stmt)
    cnt = cnt_res.scalar() or 0
    biz_id = f"AVL-{payload.start_date.year}-{cnt + 1:06d}"

    new_rec = Availability(
        id=str(uuid.uuid4()),
        business_id=biz_id,
        employee_id=payload.employee_id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        availability_type=payload.availability_type,
        capacity_percentage=payload.capacity_percentage,
        available_hours_per_day=payload.available_hours_per_day,
        is_approved=payload.is_approved,
        approved_by_id=payload.approved_by_id or current_user.id,
        reason=payload.reason,
    )
    session.add(new_rec)
    await session.commit()
    await session.refresh(new_rec)
    return AvailabilityResponse.model_validate(new_rec)
