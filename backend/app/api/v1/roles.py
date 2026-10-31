"""
Role Taxonomy API Endpoints.
"""

from typing import Annotated, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import PaginationParams, get_current_user, get_db, require_roles
from app.models.employee import Employee
from app.models.enums import UserRole
from app.models.role import Role
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.role import RoleCreate, RoleResponse, RoleUpdate

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.get("", response_model=PaginatedResponse[RoleResponse], summary="List Job Roles")
async def list_roles(
    pagination: Annotated[PaginationParams, Depends()],
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(get_current_user)],
    department: Optional[str] = Query(default=None, description="Filter by department"),
):
    query = select(Role)
    count_query = select(func.count(Role.id))

    if department:
        query = query.where(Role.department == department)
        count_query = count_query.where(Role.department == department)

    if pagination.search:
        term = f"%{pagination.search.strip()}%"
        s_filter = or_(Role.title.ilike(term), Role.business_id.ilike(term), Role.department.ilike(term), Role.code.ilike(term))
        query = query.where(s_filter)
        count_query = count_query.where(s_filter)

    total_res = await session.execute(count_query)
    total = total_res.scalar() or 0

    query = query.order_by(Role.department.asc(), Role.title.asc())
    query = query.offset(pagination.offset).limit(pagination.limit)
    res = await session.execute(query)
    roles = res.scalars().all()

    total_pages = max(1, (total + pagination.page_size - 1) // pagination.page_size)

    return PaginatedResponse[RoleResponse](
        items=[RoleResponse.model_validate(r) for r in roles],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
    )


@router.get("/{role_id}", response_model=RoleResponse, summary="Get Role by ID")
async def get_role(
    role_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(get_current_user)],
):
    stmt = select(Role).where(or_(Role.id == role_id, Role.business_id == role_id))
    res = await session.execute(stmt)
    role = res.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Role '{role_id}' not found")
    return RoleResponse.model_validate(role)


@router.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED, summary="Create Job Role")
async def create_role(
    payload: RoleCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(require_roles(UserRole.ADMIN, UserRole.HR_PARTNER))],
):
    count_stmt = select(func.count(Role.id))
    cnt_res = await session.execute(count_stmt)
    cnt = cnt_res.scalar() or 0
    biz_id = f"ROL-{cnt + 1:06d}"

    new_role = Role(
        id=str(uuid.uuid4()),
        business_id=biz_id,
        title=payload.title or payload.name or f"Role {cnt + 1}",
        code=payload.code or f"ROL-CODE-{cnt + 1:04d}",
        department=payload.department,
        is_active=payload.is_active,
        description=payload.description,
        standard_hourly_rate=Decimal(str(payload.standard_hourly_rate or 75.0)),
    )
    session.add(new_role)
    await session.commit()
    await session.refresh(new_role)
    return RoleResponse.model_validate(new_role)


@router.put("/{role_id}", response_model=RoleResponse, summary="Update Job Role")
async def update_role(
    role_id: str,
    payload: RoleUpdate,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(require_roles(UserRole.ADMIN, UserRole.HR_PARTNER))],
):
    stmt = select(Role).where(or_(Role.id == role_id, Role.business_id == role_id))
    res = await session.execute(stmt)
    role = res.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Role '{role_id}' not found")

    for f, v in payload.model_dump(exclude_unset=True).items():
        setattr(role, f, v)

    await session.commit()
    await session.refresh(role)
    return RoleResponse.model_validate(role)


@router.delete("/{role_id}", response_model=SuccessResponse, summary="Delete Job Role")
async def delete_role(
    role_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(require_roles(UserRole.ADMIN))],
):
    stmt = select(Role).where(or_(Role.id == role_id, Role.business_id == role_id))
    res = await session.execute(stmt)
    role = res.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Role '{role_id}' not found")

    await session.delete(role)
    await session.commit()
    return SuccessResponse(message=f"Role '{role_id}' deleted")
