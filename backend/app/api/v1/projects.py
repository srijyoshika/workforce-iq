"""
Project Portfolio API Endpoints.
"""

from typing import Annotated, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import PaginationParams, get_current_user, get_db, require_roles
from app.models.employee import Employee
from app.models.enums import ProjectStatus, UserRole
from app.models.project import Project
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("", response_model=PaginatedResponse[ProjectResponse], summary="List Projects")
async def list_projects(
    pagination: Annotated[PaginationParams, Depends()],
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(get_current_user)],
    status_filter: Optional[ProjectStatus] = Query(default=None, alias="status", description="Filter by status"),
    priority: Optional[int] = Query(default=None, ge=1, le=4, description="Filter by priority tier"),
):
    query = select(Project)
    count_query = select(func.count(Project.id))

    if status_filter:
        query = query.where(Project.status == status_filter)
        count_query = count_query.where(Project.status == status_filter)
    if pagination.search:
        term = f"%{pagination.search.strip()}%"
        s_filter = or_(Project.name.ilike(term), Project.code.ilike(term), Project.business_id.ilike(term))
        query = query.where(s_filter)
        count_query = count_query.where(s_filter)

    total_res = await session.execute(count_query)
    total = total_res.scalar() or 0

    query = query.order_by(Project.start_date.asc(), Project.name.asc())
    query = query.offset(pagination.offset).limit(pagination.limit)
    res = await session.execute(query)
    projects = res.scalars().all()

    total_pages = max(1, (total + pagination.page_size - 1) // pagination.page_size)

    return PaginatedResponse[ProjectResponse](
        items=[ProjectResponse.model_validate(p) for p in projects],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
    )


@router.get("/{project_id}", response_model=ProjectResponse, summary="Get Project by ID")
async def get_project(
    project_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(get_current_user)],
):
    stmt = select(Project).where(or_(Project.id == project_id, Project.business_id == project_id, Project.code == project_id))
    res = await session.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{project_id}' not found")
    return ProjectResponse.model_validate(project)


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED, summary="Create Project")
async def create_project(
    payload: ProjectCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(require_roles(UserRole.ADMIN, UserRole.PROJECT_MANAGER, UserRole.OPERATIONS_PARTNER))],
):
    count_stmt = select(func.count(Project.id))
    cnt_res = await session.execute(count_stmt)
    cnt = cnt_res.scalar() or 0
    biz_id = f"PRJ-{payload.start_date.year}-{cnt + 1:06d}"

    new_project = Project(
        id=str(uuid.uuid4()),
        business_id=biz_id,
        name=payload.name,
        code=payload.code,
        department=payload.department or "Engineering",
        client_name=payload.client_name or "Internal Engagement",
        manager_id=payload.manager_id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        status=payload.status,
        budget=Decimal(str(payload.budget)) if payload.budget is not None else Decimal("0.0"),
    )
    session.add(new_project)
    await session.commit()
    await session.refresh(new_project)
    return ProjectResponse.model_validate(new_project)


@router.put("/{project_id}", response_model=ProjectResponse, summary="Update Project")
async def update_project(
    project_id: str,
    payload: ProjectUpdate,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(require_roles(UserRole.ADMIN, UserRole.PROJECT_MANAGER))],
):
    stmt = select(Project).where(or_(Project.id == project_id, Project.business_id == project_id))
    res = await session.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{project_id}' not found")

    for f, v in payload.model_dump(exclude_unset=True).items():
        setattr(project, f, v)

    await session.commit()
    await session.refresh(project)
    return ProjectResponse.model_validate(project)


@router.delete("/{project_id}", response_model=SuccessResponse, summary="Delete Project")
async def delete_project(
    project_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(require_roles(UserRole.ADMIN))],
):
    stmt = select(Project).where(or_(Project.id == project_id, Project.business_id == project_id))
    res = await session.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{project_id}' not found")

    await session.delete(project)
    await session.commit()
    return SuccessResponse(message=f"Project '{project_id}' deleted")
