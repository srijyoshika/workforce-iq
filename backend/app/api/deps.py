"""
FastAPI Dependencies for Database Sessions, Authentication, and Role-Based Authorization.
"""

from typing import Annotated, Any, AsyncGenerator, Callable, List, Optional
from fastapi import Depends, HTTPException, Query, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.database import get_db_session
from app.models.employee import Employee
from app.models.enums import EmploymentStatus, UserRole

# Reusable HTTP Bearer security scheme
security_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields an asynchronous database session."""
    async for session in get_db_session():
        yield session


async def get_current_user(
    request: Request,
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security_scheme)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> Employee:
    """
    Authenticate and extract the current authenticated Employee / User from the JWT Bearer token.
    Raises 401 Unauthorized if token is missing, expired, or invalid.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, expired, or revoked access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    emp_id = payload.get("emp_id") or payload.get("sub")
    if not emp_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token claims",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch employee from database
    stmt = select(Employee).where(Employee.id == emp_id)
    res = await session.execute(stmt)
    employee = res.scalar_one_or_none()

    if not employee:
        # Check by email or business_id as fallback
        email = payload.get("email")
        if email:
            stmt = select(Employee).where(Employee.email == email)
            res = await session.execute(stmt)
            employee = res.scalar_one_or_none()

    if not employee:
        # Check if this is the bootstrap administrator
        if payload.get("email") == "admin@workforceiq.com" or payload.get("role") == UserRole.ADMIN.value:
            from datetime import date
            employee = Employee(
                id=emp_id or "ADMIN-001",
                business_id="EMP-ADMIN",
                first_name="System",
                last_name="Administrator",
                email="admin@workforceiq.com",
                system_role=UserRole.ADMIN,
                department="Executive",
                location="Global",
                employment_status=EmploymentStatus.ACTIVE,
                hire_date=date(2026, 1, 1),
                standard_hours_per_week=40.0,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authenticated user account no longer exists",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # Attach raw token to request state for logout invalidation
    request.state.access_token = token
    return employee


def require_roles(*allowed_roles: UserRole) -> Callable:
    """
    Role-based authorization dependency factory.
    Verifies that the current user's role is in the permitted role list.
    """
    allowed_values = {r.value if hasattr(r, "value") else str(r) for r in allowed_roles}

    async def role_checker(
        current_user: Annotated[Employee, Depends(get_current_user)]
    ) -> Employee:
        user_role_val = (
            current_user.system_role.value
            if hasattr(current_user.system_role, "value")
            else str(current_user.system_role)
        )
        if user_role_val not in allowed_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: User role '{user_role_val}' is not authorized for this resource.",
            )
        return current_user

    return role_checker


class PaginationParams:
    """Common query parameter parser for paginated listing endpoints."""

    def __init__(
        self,
        page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
        page_size: int = Query(default=50, ge=1, le=500, description="Items per page"),
        sort_by: Optional[str] = Query(default=None, description="Field name to sort by"),
        sort_order: str = Query(default="asc", pattern="^(asc|desc)$", description="Sort direction"),
        search: Optional[str] = Query(default=None, description="Free-text search filter"),
    ):
        self.page = page
        self.page_size = page_size
        self.sort_by = sort_by
        self.sort_order = sort_order
        self.search = search

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size
