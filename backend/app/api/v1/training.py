"""
Workforce Training and Upskilling API Endpoints.
"""

from typing import Annotated, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import PaginationParams, get_current_user, get_db, require_roles
from app.models.employee import Employee
from app.models.enums import TrainingStatus, UserRole
from app.models.training import Training
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.training import TrainingCreate, TrainingResponse, TrainingUpdate

router = APIRouter(prefix="/training", tags=["Training & Upskilling"])


@router.get("", response_model=PaginatedResponse[TrainingResponse], summary="List Training Enrollments")
async def list_trainings(
    pagination: Annotated[PaginationParams, Depends()],
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(get_current_user)],
    employee_id: Optional[str] = Query(default=None, description="Filter by employee"),
    skill_id: Optional[str] = Query(default=None, description="Filter by skill"),
    status_filter: Optional[TrainingStatus] = Query(default=None, alias="status", description="Filter by status"),
):
    query = select(Training)
    count_query = select(func.count(Training.id))

    if employee_id:
        query = query.where(Training.employee_id == employee_id)
        count_query = count_query.where(Training.employee_id == employee_id)
    if skill_id:
        query = query.where(Training.skill_id == skill_id)
        count_query = count_query.where(Training.skill_id == skill_id)
    if status_filter:
        query = query.where(Training.status == status_filter)
        count_query = count_query.where(Training.status == status_filter)

    total_res = await session.execute(count_query)
    total = total_res.scalar() or 0

    query = query.order_by(Training.start_date.desc()).offset(pagination.offset).limit(pagination.limit)
    res = await session.execute(query)
    records = res.scalars().all()

    total_pages = max(1, (total + pagination.page_size - 1) // pagination.page_size)

    return PaginatedResponse[TrainingResponse](
        items=[TrainingResponse.model_validate(r) for r in records],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
    )


@router.get("/{training_id}", response_model=TrainingResponse, summary="Get Training Record by ID")
async def get_training(
    training_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(get_current_user)],
):
    stmt = select(Training).where(Training.id == training_id)
    res = await session.execute(stmt)
    rec = res.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Training record '{training_id}' not found")
    return TrainingResponse.model_validate(rec)


@router.post("", response_model=TrainingResponse, status_code=status.HTTP_201_CREATED, summary="Enroll Employee in Training")
async def create_training(
    payload: TrainingCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(require_roles(UserRole.ADMIN, UserRole.HR_PARTNER))],
):
    count_stmt = select(func.count(Training.id))
    cnt_res = await session.execute(count_stmt)
    cnt = cnt_res.scalar() or 0
    biz_id = f"TRN-{payload.start_date.year}-{cnt + 1:06d}"

    new_rec = Training(
        id=str(uuid.uuid4()),
        business_id=biz_id,
        employee_id=payload.employee_id,
        skill_id=payload.skill_id,
        program_name=payload.program_name,
        provider=payload.provider,
        start_date=payload.start_date,
        target_completion_date=payload.target_completion_date,
        actual_completion_date=payload.actual_completion_date,
        target_proficiency=payload.target_proficiency,
        status=payload.status,
        cost=payload.cost,
        hours_per_week=payload.hours_per_week,
    )
    session.add(new_rec)
    await session.commit()
    await session.refresh(new_rec)
    return TrainingResponse.model_validate(new_rec)
