"""
Employee Management API Endpoints.
Provides CRUD operations, pagination, search, and department filtering.
"""

from typing import Annotated, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import PaginationParams, get_current_user, get_db, require_roles
from app.core.security import hash_password
from app.models.employee import Employee
from app.models.enums import EmploymentStatus, UserRole
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.employee import EmployeeCreate, EmployeeResponse, EmployeeUpdate

router = APIRouter(prefix="/employees", tags=["Employees"])


@router.get("", response_model=PaginatedResponse[EmployeeResponse], summary="List Employees with Pagination & Filters")
async def list_employees(
    pagination: Annotated[PaginationParams, Depends()],
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(get_current_user)],
    department: Optional[str] = Query(default=None, description="Filter by department"),
    employment_status: Optional[EmploymentStatus] = Query(default=None, description="Filter by employment status"),
    role_id: Optional[str] = Query(default=None, description="Filter by primary role ID"),
):
    """
    Retrieve paginated list of employees with multi-field search and department filtering.
    """
    query = select(Employee)
    count_query = select(func.count(Employee.id))

    if department:
        query = query.where(Employee.department == department)
        count_query = count_query.where(Employee.department == department)
    if employment_status:
        query = query.where(Employee.employment_status == employment_status)
        count_query = count_query.where(Employee.employment_status == employment_status)
    if role_id:
        query = query.where(Employee.role_id == role_id)
        count_query = count_query.where(Employee.role_id == role_id)

    if pagination.search:
        term = f"%{pagination.search.strip()}%"
        search_filter = or_(
            Employee.first_name.ilike(term),
            Employee.last_name.ilike(term),
            Employee.email.ilike(term),
            Employee.business_id.ilike(term),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    # Sorting
    if pagination.sort_by and hasattr(Employee, pagination.sort_by):
        col = getattr(Employee, pagination.sort_by)
        query = query.order_by(col.desc() if pagination.sort_order == "desc" else col.asc())
    else:
        query = query.order_by(Employee.last_name.asc(), Employee.first_name.asc())

    # Total count
    total_res = await session.execute(count_query)
    total = total_res.scalar() or 0

    # Paginate
    query = query.offset(pagination.offset).limit(pagination.limit)
    res = await session.execute(query)
    employees = res.scalars().all()

    total_pages = max(1, (total + pagination.page_size - 1) // pagination.page_size)

    return PaginatedResponse[EmployeeResponse](
        items=[EmployeeResponse.model_validate(e) for e in employees],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
    )


@router.get("/{employee_id}", response_model=EmployeeResponse, summary="Get Employee by ID")
async def get_employee(
    employee_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(get_current_user)],
):
    """Retrieve full employee profile by primary key UUID or business ID."""
    stmt = select(Employee).where(
        or_(Employee.id == employee_id, Employee.business_id == employee_id)
    )
    res = await session.execute(stmt)
    emp = res.scalar_one_or_none()

    if not emp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee '{employee_id}' not found",
        )
    return EmployeeResponse.model_validate(emp)


@router.post("", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED, summary="Create New Employee")
async def create_employee(
    payload: EmployeeCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(require_roles(UserRole.ADMIN, UserRole.HR_PARTNER))],
):
    """Register a new enterprise employee (restricted to ADMIN and HR_PARTNER)."""
    # Check duplicate email
    dup_stmt = select(Employee).where(Employee.email == payload.email)
    dup_res = await session.execute(dup_stmt)
    if dup_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An employee with email '{payload.email}' already exists",
        )

    # Generate sequential business ID
    count_stmt = select(func.count(Employee.id))
    count_res = await session.execute(count_stmt)
    cnt = count_res.scalar() or 0
    biz_id = f"EMP-{cnt + 1:06d}"

    emp_id = str(uuid.uuid4())
    pwd_hash = hash_password(payload.password) if payload.password else None

    new_emp = Employee(
        id=emp_id,
        business_id=biz_id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
        role_id=payload.role_id,
        department=payload.department,
        location=payload.location,
        employment_status=payload.employment_status,
        hire_date=payload.hire_date,
        exit_date=payload.exit_date,
        standard_hours_per_week=payload.standard_hours_per_week,
        cost_rate_per_hour=payload.cost_rate_per_hour,
        system_role=payload.system_role,
        years_of_experience=payload.years_of_experience,
        experience_level=payload.experience_level,
        previous_company=payload.previous_company,
        experience_summary=payload.experience_summary,
        hashed_password=pwd_hash,
    )
    session.add(new_emp)
    await session.commit()
    await session.refresh(new_emp)

    return EmployeeResponse.model_validate(new_emp)


@router.put("/{employee_id}", response_model=EmployeeResponse, summary="Update Employee Details")
async def update_employee(
    employee_id: str,
    payload: EmployeeUpdate,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(require_roles(UserRole.ADMIN, UserRole.HR_PARTNER))],
):
    """Update employee attributes (restricted to ADMIN and HR_PARTNER)."""
    stmt = select(Employee).where(
        or_(Employee.id == employee_id, Employee.business_id == employee_id)
    )
    res = await session.execute(stmt)
    emp = res.scalar_one_or_none()

    if not emp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee '{employee_id}' not found",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(emp, field, val)

    await session.commit()
    await session.refresh(emp)
    return EmployeeResponse.model_validate(emp)


@router.delete("/{employee_id}", response_model=SuccessResponse, summary="Delete or Terminate Employee")
async def delete_employee(
    employee_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(require_roles(UserRole.ADMIN))],
):
    """Delete employee record from database (restricted to ADMIN)."""
    stmt = select(Employee).where(
        or_(Employee.id == employee_id, Employee.business_id == employee_id)
    )
    res = await session.execute(stmt)
    emp = res.scalar_one_or_none()

    if not emp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee '{employee_id}' not found",
        )

    await session.delete(emp)
    await session.commit()
    return SuccessResponse(message=f"Employee '{employee_id}' successfully deleted")
