"""
Skill Catalog and Employee Skill Profile API Endpoints.
"""

from typing import Annotated, List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import PaginationParams, get_current_user, get_db, require_roles
from app.models.employee import Employee
from app.models.enums import SkillCategory, UserRole
from app.models.skill import EmployeeSkill, Skill
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.skill import (
    EmployeeSkillCreate,
    EmployeeSkillResponse,
    EmployeeSkillUpdate,
    SkillCreate,
    SkillResponse,
    SkillUpdate,
)

router = APIRouter(prefix="/skills", tags=["Skills"])


@router.get("", response_model=PaginatedResponse[SkillResponse], summary="List Skill Catalog")
async def list_skills(
    pagination: Annotated[PaginationParams, Depends()],
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(get_current_user)],
    category: Optional[SkillCategory] = Query(default=None, description="Filter by skill category"),
):
    query = select(Skill)
    count_query = select(func.count(Skill.id))

    if category:
        query = query.where(Skill.category == category)
        count_query = count_query.where(Skill.category == category)

    if pagination.search:
        term = f"%{pagination.search.strip()}%"
        s_filter = or_(Skill.name.ilike(term), Skill.business_id.ilike(term))
        query = query.where(s_filter)
        count_query = count_query.where(s_filter)

    total_res = await session.execute(count_query)
    total = total_res.scalar() or 0

    query = query.order_by(Skill.name.asc()).offset(pagination.offset).limit(pagination.limit)
    res = await session.execute(query)
    skills = res.scalars().all()

    total_pages = max(1, (total + pagination.page_size - 1) // pagination.page_size)

    return PaginatedResponse[SkillResponse](
        items=[SkillResponse.model_validate(s) for s in skills],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
    )


@router.get("/{skill_id}", response_model=SkillResponse, summary="Get Skill by ID")
async def get_skill(
    skill_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(get_current_user)],
):
    stmt = select(Skill).where(or_(Skill.id == skill_id, Skill.business_id == skill_id))
    res = await session.execute(stmt)
    skill = res.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Skill '{skill_id}' not found")
    return SkillResponse.model_validate(skill)


@router.post("", response_model=SkillResponse, status_code=status.HTTP_201_CREATED, summary="Create Skill")
async def create_skill(
    payload: SkillCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(require_roles(UserRole.ADMIN, UserRole.HR_PARTNER))],
):
    count_stmt = select(func.count(Skill.id))
    cnt_res = await session.execute(count_stmt)
    cnt = cnt_res.scalar() or 0
    biz_id = f"SKL-{cnt + 1:06d}"

    new_skill = Skill(
        id=str(uuid.uuid4()),
        business_id=biz_id,
        name=payload.name,
        category=payload.category,
        is_active=payload.is_active,
        description=payload.description,
    )
    session.add(new_skill)
    await session.commit()
    await session.refresh(new_skill)
    return SkillResponse.model_validate(new_skill)


# Employee Skill Profile Endpoints
@router.get("/employee/{employee_id}", response_model=List[EmployeeSkillResponse], summary="Get Employee Skills Profile")
async def get_employee_skills(
    employee_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(get_current_user)],
):
    stmt = select(EmployeeSkill).where(EmployeeSkill.employee_id == employee_id)
    res = await session.execute(stmt)
    skills = res.scalars().all()
    return [EmployeeSkillResponse.model_validate(s) for s in skills]


@router.post("/employee", response_model=EmployeeSkillResponse, status_code=status.HTTP_201_CREATED, summary="Add Skill to Employee Profile")
async def add_employee_skill(
    payload: EmployeeSkillCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(get_current_user)],
):
    count_stmt = select(func.count(EmployeeSkill.id))
    cnt_res = await session.execute(count_stmt)
    cnt = cnt_res.scalar() or 0
    biz_id = f"ES-{cnt + 1:06d}"

    new_es = EmployeeSkill(
        id=str(uuid.uuid4()),
        business_id=biz_id,
        employee_id=payload.employee_id,
        skill_id=payload.skill_id,
        proficiency_level=payload.proficiency_level,
        verification_status=payload.verification_status,
        verified_at=payload.verified_at,
        is_current=payload.is_current,
        notes=payload.notes,
    )
    session.add(new_es)
    await session.commit()
    await session.refresh(new_es)
    return EmployeeSkillResponse.model_validate(new_es)
