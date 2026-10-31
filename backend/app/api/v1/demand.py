"""
Demand Planning API Endpoints.
"""

from typing import Annotated, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import PaginationParams, get_current_user, get_db, require_roles
from app.models.employee import Employee
from app.models.enums import DemandStatus, UserRole
from app.models.project import DemandPlan
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.demand import DemandPlanCreate, DemandPlanResponse, DemandPlanUpdate

router = APIRouter(prefix="/demand", tags=["Demand Planning"])


@router.get("", response_model=PaginatedResponse[DemandPlanResponse], summary="List Demand Plans")
async def list_demand_plans(
    pagination: Annotated[PaginationParams, Depends()],
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(get_current_user)],
    project_id: Optional[str] = Query(default=None, description="Filter by project"),
    role_id: Optional[str] = Query(default=None, description="Filter by role"),
    skill_id: Optional[str] = Query(default=None, description="Filter by skill"),
    status_filter: Optional[DemandStatus] = Query(default=None, alias="status", description="Filter by status"),
):
    query = select(DemandPlan)
    count_query = select(func.count(DemandPlan.id))

    if project_id:
        query = query.where(DemandPlan.project_id == project_id)
        count_query = count_query.where(DemandPlan.project_id == project_id)
    if role_id:
        query = query.where(DemandPlan.role_id == role_id)
        count_query = count_query.where(DemandPlan.role_id == role_id)
    if skill_id:
        query = query.where(DemandPlan.primary_skill_id == skill_id)
        count_query = count_query.where(DemandPlan.primary_skill_id == skill_id)
    if status_filter:
        query = query.where(DemandPlan.status == status_filter)
        count_query = count_query.where(DemandPlan.status == status_filter)

    total_res = await session.execute(count_query)
    total = total_res.scalar() or 0

    query = query.order_by(DemandPlan.start_date.asc(), DemandPlan.priority.asc())
    query = query.offset(pagination.offset).limit(pagination.limit)
    res = await session.execute(query)
    demands = res.scalars().all()

    total_pages = max(1, (total + pagination.page_size - 1) // pagination.page_size)

    return PaginatedResponse[DemandPlanResponse](
        items=[DemandPlanResponse.model_validate(d) for d in demands],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
    )


@router.get("/{demand_id}", response_model=DemandPlanResponse, summary="Get Demand Line by ID")
async def get_demand_plan(
    demand_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(get_current_user)],
):
    stmt = select(DemandPlan).where(DemandPlan.id == demand_id)
    res = await session.execute(stmt)
    demand = res.scalar_one_or_none()
    if not demand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Demand plan '{demand_id}' not found")
    return DemandPlanResponse.model_validate(demand)


@router.post("", response_model=DemandPlanResponse, status_code=status.HTTP_201_CREATED, summary="Create Demand Line")
async def create_demand_plan(
    payload: DemandPlanCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(require_roles(UserRole.ADMIN, UserRole.PROJECT_MANAGER, UserRole.OPERATIONS_PARTNER))],
):
    week_str = f"{payload.start_date.year}W{payload.start_date.isocalendar()[1]:02d}"
    biz_id = f"DEM-{payload.project_id[:8]}-{week_str}"

    req_hours = payload.required_hours or (payload.required_headcount * 40.0)

    new_demand = DemandPlan(
        id=str(uuid.uuid4()),
        business_id=biz_id,
        project_id=payload.project_id,
        role_id=payload.role_id,
        primary_skill_id=payload.primary_skill_id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        required_headcount=payload.required_headcount,
        required_hours=req_hours,
        fulfilled_hours=payload.fulfilled_hours,
        min_proficiency=payload.min_proficiency,
        status=payload.status,
        priority=payload.priority,
        notes=payload.notes,
    )
    session.add(new_demand)
    await session.commit()
    await session.refresh(new_demand)
    return DemandPlanResponse.model_validate(new_demand)


@router.put("/{demand_id}", response_model=DemandPlanResponse, summary="Update Demand Line")
async def update_demand_plan(
    demand_id: str,
    payload: DemandPlanUpdate,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(require_roles(UserRole.ADMIN, UserRole.PROJECT_MANAGER))],
):
    stmt = select(DemandPlan).where(DemandPlan.id == demand_id)
    res = await session.execute(stmt)
    demand = res.scalar_one_or_none()
    if not demand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Demand plan '{demand_id}' not found")

    for f, v in payload.model_dump(exclude_unset=True).items():
        setattr(demand, f, v)

    await session.commit()
    await session.refresh(demand)
    return DemandPlanResponse.model_validate(demand)


@router.delete("/{demand_id}", response_model=SuccessResponse, summary="Delete Demand Line")
async def delete_demand_plan(
    demand_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(require_roles(UserRole.ADMIN, UserRole.PROJECT_MANAGER))],
):
    stmt = select(DemandPlan).where(DemandPlan.id == demand_id)
    res = await session.execute(stmt)
    demand = res.scalar_one_or_none()
    if not demand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Demand plan '{demand_id}' not found")

    await session.delete(demand)
    await session.commit()
    return SuccessResponse(message=f"Demand plan '{demand_id}' deleted")
